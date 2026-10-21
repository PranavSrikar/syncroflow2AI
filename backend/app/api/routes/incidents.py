"""
SYNCHROFLOW AI — Incident Management & Lane Obstruction Routes
"""

import time
from typing import Optional, Literal
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.simulation_service import simulation_service
from app.schemas.traffic import Direction
from app.schemas.commands import CommandAckResponse

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


class IncidentReportRequest(BaseModel):
    approach: Direction
    incidentType: Literal["breakdown", "road_closure", "spillback", "debris"]
    laneIndex: int = 1
    description: str = "Vehicle stall detected in lane"


@router.post("/report", response_model=CommandAckResponse)
async def report_incident(req: IncidentReportRequest):
    simulation_service.add_alert(
        severity="warning",
        title=f"Incident Reported: {req.incidentType.upper()} on {req.approach.upper()}",
        description=f"{req.description} (Lane {req.laneIndex})",
        source="Perception & Incident Hub",
    )
    return CommandAckResponse(
        commandId=f"cmd-incident-{int(time.time()*1000)}",
        success=True,
        message=f"Incident '{req.incidentType}' logged and lane capacity throttled for {req.approach}",
        executionTimestamp=int(time.time() * 1000),
    )


@router.post("/clear", response_model=CommandAckResponse)
async def clear_incidents():
    simulation_service.add_alert(
        severity="info",
        title="Incident Clearance Verified",
        description="All lane obstructions cleared. Full approach capacity restored.",
        source="Incident Clearance Dispatch",
    )
    return CommandAckResponse(
        commandId=f"cmd-clear-{int(time.time()*1000)}",
        success=True,
        message="All active incidents marked cleared",
        executionTimestamp=int(time.time() * 1000),
    )
