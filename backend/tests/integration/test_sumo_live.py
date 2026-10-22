"""Real simulator tests: no mocked TraCI measurements."""
import shutil
import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.sumo_runtime import sumo_runtime


@pytest.mark.skipif(shutil.which("sumo") is None, reason="SUMO executable required")
def test_real_sumo_lifecycle_and_stream():
    with TestClient(app) as client:
        try:
            assert client.post("/api/v1/sumo/start").status_code == 200
            assert client.post("/api/v1/sumo/pause").status_code == 200
            initial = client.get("/api/v1/sumo/status").json()
            assert initial["connected"] and not initial["running"]
            for _ in range(30):
                response = client.post("/api/v1/sumo/step")
                assert response.status_code == 200, response.text
            raw = response.json()
            assert raw["source"] == "sumo_traci"
            assert raw["simTime"] == initial["telemetry"]["simTime"] + 30
            assert raw["vehicleDetails"]
            assert raw["permissionAnalysis"]["center"]["compatibleUnderSumoRules"]
            assert set(raw["approaches"]) == {"north", "south", "east", "west"}
            for row in raw["approaches"].values():
                assert 0 <= row["queued"] <= row["vehicles"]
            for light in raw["trafficLights"].values():
                assert len(light["signalState"]) == len(light["controlledLinks"])
            with client.websocket_connect("/api/v1/sumo/ws") as ws:
                message = ws.receive_json()
                assert message["telemetry"] == raw
                assert message["controller"] == "sumo_fixed_time"
                assert message["safetySupervisor"]["status"] == "unavailable"
            assert client.post("/api/v1/sumo/start").status_code == 200
            assert client.post("/api/v1/sumo/step").status_code == 409
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                current = client.get("/api/v1/sumo/telemetry").json()
                if current["simTime"] > raw["simTime"]:
                    break
                time.sleep(0.05)
            assert current["simTime"] > raw["simTime"]
        finally:
            client.post("/api/v1/sumo/stop")
        assert not sumo_runtime.snapshot()["connected"]
        assert client.get("/api/v1/sumo/telemetry").status_code == 409


def test_step_requires_connection():
    with TestClient(app) as client:
        client.post("/api/v1/sumo/stop")
        assert client.post("/api/v1/sumo/step").status_code == 409


@pytest.mark.skipif(shutil.which("sumo") is None, reason="SUMO executable required")
def test_pedestrian_scenario_reports_actual_walkers_and_crossings():
    with TestClient(app) as client:
        try:
            response = client.post("/api/v1/sumo/start?scenario=pedestrian")
            assert response.status_code == 200, response.text
            client.post("/api/v1/sumo/pause")
            assert client.post("/api/v1/sumo/start?scenario=vehicle").status_code == 409
            seen, crossed = set(), set()
            for _ in range(180):
                response = client.post("/api/v1/sumo/step")
                assert response.status_code == 200, response.text
                raw = response.json()
                seen.update(raw["pedestrians"])
                crossed.update(p["roadId"] for p in raw["pedestrians"].values() if p["roadId"].startswith(":center_c"))
            assert seen
            assert len(crossed) == 4
            assert len(raw["trafficLights"]["center"]["signalState"]) == 20
            assert raw["stateEstimates"]["north"]["rateWindowSec"] == 60
            assert set(raw["downstream"]) == {"north", "south", "east", "west"}
            audit = client.get("/api/v1/sumo/network-safety?pedestrian=true").json()
            assert len([m for m in audit["movements"]["center"] if m["pedestrian"]]) == 4
        finally:
            client.post("/api/v1/sumo/stop")
            sumo_runtime.scenario = "vehicle"


@pytest.mark.skipif(shutil.which("sumo") is None, reason="SUMO executable required")
@pytest.mark.parametrize("controller", ["max_pressure", "mpc"])
def test_adaptive_vehicle_control_and_independent_rejection(controller):
    import traci
    with TestClient(app) as client:
        try:
            response = client.post(f"/api/v1/sumo/start?scenario=vehicle&controller={controller}")
            assert response.status_code == 200, response.text
            client.post("/api/v1/sumo/pause")
            supervisor = sumo_runtime.controller.supervisor
            phase = traci.trafficlight.getPhase("center")
            original_state = traci.trafficlight.getRedYellowGreenState("center")
            with pytest.raises(ValueError):
                supervisor.apply_duration(phase, 1, "deliberate_min_green_violation")
            assert traci.trafficlight.getRedYellowGreenState("center") == original_state
            for i in range(100):
                traci.vehicle.add(f"stress_{i}", "north_to_south", typeID="car", depart="now")
            stages = set()
            previous_phase, entered_at = None, None
            green_durations = []
            solved_mpc = None
            for _ in range(240):
                response = client.post("/api/v1/sumo/step")
                assert response.status_code == 200, response.text
                raw = response.json()
                if controller == 'mpc' and sumo_runtime.controller.diagnostics.get('policy') == 'constrained_mpc':
                    solved_mpc = dict(sumo_runtime.controller.diagnostics)
                current = raw["trafficLights"]["center"]["phaseIndex"]
                stages.add(current)
                assert raw["permissionAnalysis"]["center"]["compatibleUnderSumoRules"]
                if previous_phase is not None and current != previous_phase:
                    assert current == (previous_phase + 1) % 6
                    elapsed = raw["simTime"] - entered_at
                    if previous_phase % 3 == 0:
                        assert 10 <= elapsed <= 45
                        green_durations.append(elapsed)
                    elif previous_phase % 3 == 1:
                        assert elapsed >= 3
                    else:
                        assert elapsed >= 2
                    entered_at = raw["simTime"]
                elif previous_phase is None:
                    entered_at = raw["simTime"]
                previous_phase = current
            assert stages == set(range(6))
            assert green_durations
            report = client.get("/api/v1/sumo/status").json()
            assert report["controller"] == controller
            assert report["safetySupervisor"]["acceptedActions"] > 0
            assert report["safetySupervisor"]["rejectedActions"] >= 1
            assert report["controllerDiagnostics"]["phasePressurePcu"]
            if controller == "mpc":
                # The last tick may be inside mandatory minimum green, where no
                # solve is due. Verify an actual solve observed during the run.
                assert solved_mpc is not None, report['controllerDiagnostics']
                assert len(solved_mpc["predictedQueuesPcu"]) == 60
                assert solved_mpc["feasibleCandidates"] > 0
                sumo_runtime.controller.SOLVE_BUDGET_SEC = 0
                fallback_seen = False
                for _ in range(70):
                    assert client.post("/api/v1/sumo/step").status_code == 200
                    diagnostics = client.get("/api/v1/sumo/status").json()["controllerDiagnostics"]
                    if diagnostics.get("policy") == "max_pressure_fallback":
                        fallback_seen = True
                        assert "budget" in diagnostics["fallback"]
                        break
                assert fallback_seen
        finally:
            client.post("/api/v1/sumo/stop")
            sumo_runtime.controller_mode = "sumo_fixed_time"
        assert client.post("/api/v1/sumo/start?controller=unimplemented").status_code == 409
