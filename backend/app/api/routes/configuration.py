"""
SYNCHROFLOW AI — System Configuration Routes
"""

from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings
from app.services.simulation_service import simulation_service

router = APIRouter(prefix="/api/v1/config", tags=["configuration"])


class ConfigResponse(BaseModel):
    version: str
    protocolVersion: str
    environment: str
    defaultSeed: int
    stepDt: float
    controllerType: str
    weather: str
    activeScenario: str


@router.get("", response_model=ConfigResponse)
@router.get("/", response_model=ConfigResponse)
async def get_config():
    return ConfigResponse(
        version=settings.APP_VERSION,
        protocolVersion=settings.PROTOCOL_VERSION,
        environment=settings.ENVIRONMENT,
        defaultSeed=simulation_service.seed,
        stepDt=settings.SIMULATION_STEP_DT,
        controllerType=simulation_service.controller_type,
        weather=simulation_service.weather,
        activeScenario=simulation_service.scenario_id,
    )
