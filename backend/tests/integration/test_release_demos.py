import shutil
import pytest
import traci
from fastapi.testclient import TestClient
from app.main import app
from app.services.sumo_runtime import sumo_runtime


@pytest.mark.skipif(shutil.which('sumo') is None, reason='Actual SUMO required')
@pytest.mark.parametrize('scenario', ['unequal', 'spillback'])
def test_release_demand_fixtures_use_actual_telemetry(scenario):
    with TestClient(app) as client:
        try:
            response = client.post(f'/api/v1/sumo/start?scenario={scenario}&controller=hybrid&paused=true&seed=95')
            assert response.status_code == 200, response.text
            for _ in range(35):
                response = client.post('/api/v1/sumo/step')
                assert response.status_code == 200, response.text
            state = client.get('/api/v1/sumo/status').json()
            raw = state['telemetry']
            assert raw['source'] == 'sumo_traci'
            assert raw['permissionAnalysis']['center']['compatibleUnderSumoRules']
            if scenario == 'unequal':
                rates = raw['stateEstimates']
                assert rates['north']['arrivalRatePerSec'] > rates['east']['arrivalRatePerSec']
            else:
                assert raw['downstream']['south']['occupancyPercent'] >= 80
                assert raw['downstream']['south']['spillbackIndicator']
                assert sumo_runtime.controller.receiving_supply(raw, 'north') == 0
                assert raw['approaches']['north']['queued'] > 0
        finally:
            client.post('/api/v1/sumo/stop')
            sumo_runtime.scenario, sumo_runtime.controller_mode = 'vehicle', 'sumo_fixed_time'


@pytest.mark.skipif(shutil.which('sumo') is None, reason='Actual SUMO required')
def test_live_program_change_pauses_before_advancing():
    with TestClient(app) as client:
        try:
            assert client.post('/api/v1/sumo/start?scenario=vehicle&controller=mpc&paused=true').status_code == 200
            before = traci.simulation.getTime()
            traci.trafficlight.setProgram('center', '0')  # deliberately simulate external feedback corruption
            response = client.post('/api/v1/sumo/step')
            assert response.status_code == 409
            assert 'Live signal feedback differs' in response.json()['detail']
            assert traci.simulation.getTime() == before
            assert not client.get('/api/v1/sumo/status').json()['running']
        finally:
            client.post('/api/v1/sumo/stop')
            sumo_runtime.scenario, sumo_runtime.controller_mode = 'vehicle', 'sumo_fixed_time'
