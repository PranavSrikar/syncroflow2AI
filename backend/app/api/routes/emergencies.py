"""
SYNCHROFLOW AI — Emergency Response & Preemption Routes
"""

import time
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.simulation_service import simulation_service
from app.schemas.traffic import Direction, VehicleType
from app.schemas.commands import CommandPayload, CommandAckResponse

router = APIRouter(prefix="/api/v1/emergencies", tags=["emergencies"])


class EmergencyInjectionRequest(BaseModel):
    direction: Direction = "north"
    type: VehicleType = "ambulance"


@router.post("/inject", response_model=CommandAckResponse)
@router.post("/preempt", response_model=CommandAckResponse)
async def inject_emergency(req: EmergencyInjectionRequest):
    cmd = CommandPayload(
        commandId=f"cmd-preempt-{int(time.time()*1000)}",
        action="INJECT_EMERGENCY",
        timestamp=int(time.time() * 1000),
        payload={"direction": req.direction, "type": req.type},
    )
    return simulation_service.handle_command(cmd)


@router.get("/status")
async def emergency_status():
    sig = simulation_service.signals
    return {
        "isPreemptActive": sig.isPreemptActive,
        "preemptReason": sig.preemptReason,
        "preemptVehicleId": sig.preemptVehicleId,
        "activeEmergencies": [
            v.model_dump() for v in simulation_service.vehicles if v.isEmergency
        ],
    }
