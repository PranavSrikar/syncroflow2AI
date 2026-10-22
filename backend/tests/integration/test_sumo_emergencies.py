import shutil
import pytest
import traci
from fastapi.testclient import TestClient
from app.main import app
from app.services.sumo_runtime import sumo_runtime


@pytest.mark.skipif(shutil.which("sumo") is None, reason="SUMO required")
@pytest.mark.parametrize("arrival_phase,congested", [(0, False), (2, False), (3, False), (2, True)])
def test_real_emergency_preemption_during_walk_green_and_yellow(arrival_phase, congested):
    with TestClient(app) as client:
        try:
            response = client.post("/api/v1/sumo/start?scenario=pedestrian&controller=mpc")
            assert response.status_code == 200, response.text
            client.post("/api/v1/sumo/pause")
            for _ in range(90):
                raw = sumo_runtime.snapshot()["telemetry"]
                if raw["trafficLights"]["center"]["phaseIndex"] == arrival_phase:
                    break
                sumo_runtime.command("step")
            assert raw["trafficLights"]["center"]["phaseIndex"] == arrival_phase
            assert client.post("/api/v1/sumo/emergencies/request", json={"vehicleId": "nonexistent"}).status_code == 409
            assert client.post("/api/v1/sumo/emergencies/inject", json={"approach": "invalid"}).status_code == 422
            if congested:
                for i in range(30):
                    traci.vehicle.add(f"congestion_{i}", "north_to_south", typeID="car", depart="now")
            first = client.post("/api/v1/sumo/emergencies/inject", json={"approach": "east", "priority": 3})
            second = client.post("/api/v1/sumo/emergencies/inject", json={"approach": "north", "priority": 1})
            assert first.status_code == second.status_code == 200
            ids = [first.json()["vehicleId"], second.json()["vehicleId"]]
            assert first.json()["state"] == "pending_departure"
            emergency_control = False
            selected = set()
            congestion_seen = False
            for _ in range(280):
                state = sumo_runtime.command("step")
                congestion_seen |= state["telemetry"]["approaches"]["north"]["queued"] > 0
                for row in state["emergencyPriority"]["requests"]:
                    if row["state"] == "approaching":
                        assert state["telemetry"]["vehicleDetails"][row["vehicleId"]]["vehicleClass"] == "emergency"
                selected.add(state["emergencyPriority"]["activeVehicleId"])
                emergency_control |= (state["controllerDiagnostics"] or {}).get("policy") == "emergency_priority"
                assert not state["telemetry"]["permissionAnalysis"]["center"]["incompatiblePermissions"]
                requests = {r["vehicleId"]: r for r in state["emergencyPriority"]["requests"]}
                if all(requests[v]["state"] == "completed" for v in ids):
                    break
            assert emergency_control
            assert all(requests[v]["state"] == "completed" for v in ids), requests
            # A lower-priority vehicle can clear during its naturally serving
            # phase before it needs selection; it must not be held back artificially.
            assert ids[0] in selected
            assert not congested or congestion_seen
            assert all(requests[v]["approachResponseSec"] > 0 for v in ids)
            status = client.get("/api/v1/sumo/emergencies/status").json()
            assert status["activeVehicleId"] is None
            assert any(e["event"] == "normal_control_recovery" for e in status["events"])
            with client.websocket_connect("/api/v1/sumo/ws") as ws:
                assert ws.receive_json()["emergencyPriority"]["requests"] == status["requests"]
        finally:
            client.post("/api/v1/sumo/stop")
            sumo_runtime.scenario = "vehicle"
            sumo_runtime.controller_mode = "sumo_fixed_time"
