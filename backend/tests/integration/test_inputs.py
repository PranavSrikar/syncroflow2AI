from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.services.forecasting import forecast_service, ForecastSettings
from app.services.camera_runtime import camera_runtime
from datetime import datetime, timedelta, timezone
import shutil
from app.services.sumo_runtime import sumo_runtime

client = TestClient(app)


def test_input_api_fallback_validation_and_forecast(monkeypatch):
    monkeypatch.delenv('SYNCHROFLOW_CAMERA_CONFIG', raising=False)
    camera_runtime.stop()
    forecast_service.configure(ForecastSettings())
    assert client.post('/api/v1/perception/start').status_code == 409
    assert client.get('/api/v1/traffic-state?source=camera').json()['fallback']
    assert client.get('/api/v1/traffic-state').json()['requestedSource'] == 'sumo'
    assert client.get('/api/v1/traffic-state?source=invalid').status_code == 422
    assert not client.get('/api/v1/forecast').json()['available']
    assert client.get('/api/v1/forecast?at=2026-10-22T08:00:00').status_code == 422
    assert client.post('/api/v1/forecast/history', json={'csv': 'bad'}).status_code == 422
    assert client.post('/api/v1/forecast/config', json={'timezone': 'invalid'}).status_code == 422
    csv = 'timestamp,approach,arrivals_pcu,interval_sec\n2026-10-21T08:00:00Z,north,12,60'
    assert client.post('/api/v1/forecast/history', json={'csv': csv, 'example_data': True}).json()['rows'] == 1
    assert client.post('/api/v1/forecast/config', json={'enabled': True}).status_code == 200
    forecast = client.get('/api/v1/forecast?at=2026-10-22T08:00:00Z').json()
    assert forecast['available'] and forecast['exampleData']
    assert forecast['approaches']['north']['steps'][0]['arrivalRatePcuPerSec'] == pytest.approx(.2)
    assert client.post('/api/v1/forecast/weather/refresh').status_code == 409
    forecast_service.configure(ForecastSettings())



@pytest.mark.skipif(shutil.which('sumo') is None, reason='Actual SUMO required')
def test_historical_forecast_reaches_supervised_mpc_and_disables_cleanly():
    # Artificial input is explicitly marked and explicitly enabled for this test.
    now = datetime.now(timezone.utc)
    csv = 'timestamp,approach,arrivals_pcu,interval_sec\n'+'\n'.join(
        f'{(now-timedelta(days=7)).isoformat()},{d},12,60' for d in ('north', 'south', 'east', 'west'))
    previous = (forecast_service.settings, forecast_service.rows, forecast_service.example)
    try:
        forecast_service.ingest_csv(csv, example=True)
        forecast_service.configure(ForecastSettings(enabled=True, allow_example_for_mpc=True))
        with TestClient(app) as session:
            try:
                assert session.post('/api/v1/sumo/start?scenario=vehicle&controller=mpc').status_code == 200
                session.post('/api/v1/sumo/pause')
                for _ in range(12):
                    response = session.post('/api/v1/sumo/step')
                    assert response.status_code == 200, response.text
                status = session.get('/api/v1/sumo/status').json()
                assert status['controllerDiagnostics']['arrivalForecastSource'] == 'seasonal_shrinkage_baseline'
                assert status['forecasts']['exampleData']
                assert status['safetySupervisor']['status'] != 'unavailable'
                assert status['telemetry']['permissionAnalysis']['center']['compatibleUnderSumoRules']
                forecast_service.configure(ForecastSettings(enabled=False))
                for _ in range(2):
                    assert session.post('/api/v1/sumo/step').status_code == 200
                diagnostics = session.get('/api/v1/sumo/status').json()['controllerDiagnostics']
                assert diagnostics['arrivalForecastSource'] == 'recent_observations'
            finally:
                session.post('/api/v1/sumo/stop')
                sumo_runtime.controller_mode = 'sumo_fixed_time'
    finally:
        forecast_service.settings, forecast_service.rows, forecast_service.example = previous
