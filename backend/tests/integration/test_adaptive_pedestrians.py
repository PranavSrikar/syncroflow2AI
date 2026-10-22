import shutil
import pytest
import traci
from fastapi.testclient import TestClient
from app.main import app
from app.services.sumo_runtime import sumo_runtime


@pytest.mark.skipif(shutil.which("sumo") is None, reason="SUMO required")
@pytest.mark.parametrize("controller", ["max_pressure", "mpc"])
def test_protected_pedestrians_and_slow_walker_clearance(controller):
    with TestClient(app) as client:
        try:
            response = client.post(f"/api/v1/sumo/start?scenario=pedestrian&controller={controller}")
            assert response.status_code == 200, response.text
            client.post("/api/v1/sumo/pause")
            seen, stages = set(), set()
            frozen = None
            released = False
            for _ in range(360):
                response = client.post("/api/v1/sumo/step")
                assert response.status_code == 200, response.text
                raw = response.json()
                phase = raw["trafficLights"]["center"]["phaseIndex"]
                stages.add(phase)
                seen.update(p["roadId"] for p in raw["pedestrians"].values() if p["roadId"].startswith(":center_c"))
                analysis = raw["permissionAnalysis"]["center"]
                assert not analysis["incompatiblePermissions"]
                assert not any(p["pedestrianInvolved"] for p in analysis["yieldingInteractions"])
                if frozen is None:
                    for person, observation in raw["pedestrians"].items():
                        if observation["roadId"].startswith(":center_c"):
                            traci.person.setSpeed(person, 0)
                            frozen = person
                            break
                if frozen and not released and sumo_runtime.controller.supervisor.occupancy_holds >= 3:
                    assert phase in {1, 4, 6, 9}
                    assert set(raw["trafficLights"]["center"]["signalState"]) == {"r"}
                    traci.person.setSpeed(frozen, 1.0)
                    released = True
            assert len(seen) == 4
            assert stages == set(range(10))
            assert released
            assert sumo_runtime.controller.supervisor.report()["occupancyHolds"] >= 3
        finally:
            client.post("/api/v1/sumo/stop")
            sumo_runtime.scenario = "vehicle"
            sumo_runtime.controller_mode = "sumo_fixed_time"
