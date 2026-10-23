"""Read-only digital twin additions compared with actual TraCI observations."""
import math
import shutil
import pytest
import traci
from fastapi.testclient import TestClient
from app.main import app
from app.services.sumo_runtime import sumo_runtime

@pytest.mark.skipif(shutil.which('sumo') is None, reason='Actual SUMO required')
@pytest.mark.parametrize('scenario', ['vehicle', 'pedestrian', 'corridor'])
def test_geometry_vehicle_positions_and_service_age_are_authoritative(scenario):
    with TestClient(app) as client:
        try:
            response = client.post(f'/api/v1/sumo/start?scenario={scenario}&controller=hybrid&paused=true')
            assert response.status_code == 200, response.text
            for _ in range(12):
                assert client.post('/api/v1/sumo/step').status_code == 200
            state = client.get('/api/v1/sumo/status').json()
            raw = state['telemetry']
            geometry = raw['networkGeometry']
            assert geometry['source'] == 'sumo_traci_lane_shapes'
            assert geometry['lanes'] and geometry['junctions']
            for lane, row in geometry['lanes'].items():
                assert row['shape'] == [list(p) for p in traci.lane.getShape(lane)]
                assert row['width'] == traci.lane.getWidth(lane)
                assert all(math.isfinite(n) for point in row['shape'] for n in point)
            assert raw['vehicleDetails']
            for vehicle, row in raw['vehicleDetails'].items():
                assert row['position'] == list(traci.vehicle.getPosition(vehicle))
                assert row['vehicleClass'] == traci.vehicle.getVehicleClass(vehicle)
            if scenario == 'corridor':
                for agent, row in state['junctions'].items():
                    controller = sumo_runtime.network.controllers[agent]
                    assert row['serviceAge']['phaseAgeSec'] == {
                        str(p): raw['simTime']-t for p,t in controller.supervisor.last_served.items()}
            else:
                assert state['serviceAge']['maximumRedSec'] == sumo_runtime.controller.supervisor.MAX_RED
            assert state['mappoStatus']['operationalPolicyEnabled'] is False
        finally:
            client.post('/api/v1/sumo/stop')
