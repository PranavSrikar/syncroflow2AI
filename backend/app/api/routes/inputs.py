"""Perception and forecast observations, independent of signal actuation."""
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfoNotFoundError

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, TypeAdapter

from app.services.camera_runtime import camera_runtime
from app.services.perception import CameraConfig
from app.services.forecasting import ForecastSettings, Weather, forecast_service
from app.services.sumo_runtime import sumo_runtime

router = APIRouter(prefix='/api/v1', tags=['Perception and forecasting'])


class HistoryUpload(BaseModel):
    csv: str = Field(min_length=1, max_length=10000000)
    example_data: bool = False


@router.get('/perception/status')
def perception_status():
    return camera_runtime.snapshot()


@router.post('/perception/start')
def perception_start():
    # Source/device/weights paths are configured by the local server operator,
    # never supplied by browser requests. No arbitrary URL or filesystem reader.
    path = os.environ.get('SYNCHROFLOW_CAMERA_CONFIG')
    if not path:
        raise HTTPException(409, 'Set SYNCHROFLOW_CAMERA_CONFIG to a local camera JSON file')
    try:
        configs = TypeAdapter(list[CameraConfig]).validate_json(Path(path).read_text(encoding='utf-8'))
        return camera_runtime.start(configs)
    except (OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post('/perception/stop')
def perception_stop():
    try:
        camera_runtime.stop()
        return camera_runtime.snapshot()
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get('/traffic-state')
def traffic_state(source: str = Query(default='sumo', pattern='^(sumo|camera)$')):
    simulation = sumo_runtime.snapshot()
    camera = camera_runtime.snapshot()
    available = source == 'camera' and camera['available']
    return dict(requestedSource=source, source='camera_fusion' if available else ('sumo_traci' if simulation['connected'] else 'unavailable'),
                fallback=camera['fallback'] if source == 'camera' and not available else None,
                traffic=camera['fused'] if available else simulation['telemetry'],
                perception=camera, forecasts=forecast_service.predict(),
                actuation='SUMO controllers retain their existing supervisor; camera mode supplies observations only')


@router.post('/forecast/history')
def history(request: HistoryUpload):
    try:
        return forecast_service.ingest_csv(request.csv, request.example_data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post('/forecast/config')
def forecast_config(request: ForecastSettings):
    try:
        return forecast_service.configure(request)
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post('/forecast/enabled')
def forecast_enabled(enabled: bool):
    with forecast_service.lock:
        settings = forecast_service.settings.model_copy(update={'enabled': enabled})
    return forecast_service.configure(settings)


@router.post('/forecast/weather')
def weather(request: Weather):
    try:
        forecast_service.set_weather(request)
        return forecast_service.predict()
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post('/forecast/weather/refresh')
def refresh_weather():
    try:
        return forecast_service.refresh_weather()
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get('/forecast')
def forecast(at: datetime | None = None, horizon_sec: int = Query(default=60, ge=10, le=900), junction_id: str = 'center'):
    try:
        return forecast_service.predict(at, horizon_sec, junction_id=junction_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
