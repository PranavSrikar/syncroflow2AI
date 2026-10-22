"""
SYNCHROFLOW AI — Signal Controller Selection Routes
"""

import time
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.simulation_service import simulation_service
from app.schemas.traffic import ControllerType
from app.schemas.commands import CommandPayload, CommandAckResponse

router = APIRouter(prefix="/api/v1/controllers", tags=["controllers"])

CANONICAL_CONTROLLERS = [
    {
        "id": "fixed",
        "name": "Optimized Fixed-Time Pre-timed",
        "description": "Pre-timed 112s NEMA dual-ring cycle with static green splits.",
    },
    {
        "id": "actuated",
        "name": "Semi-Actuated Gap-Out (NEMA TS2)",
        "description": "Inductive loop gap-out extension logic with min/max green bounds.",
    },
    {
        "id": "queue_adaptive",
        "name": "Dynamic Queue-Proportional Adaptive",
        "description": "Green time dynamically distributed based on observed queue lengths.",
    },
    {
        "id": "max_pressure",
        "name": "Max-Pressure Network Adaptive (Varaiya)",
        "description": "Dynamic movement pressure differentials guaranteeing global network stability.",
    },
    {
        "id": "mpc_only",
        "name": "Receding-Horizon Constrained MPC",
        "description": "15-step predictive quadratic optimization with storage constraints.",
    },
    {
        "id": "mappo_assisted_mpc",
        "name": "MAPPO-Assisted Predictive MPC",
        "description": "Multi-agent reinforcement learning advising MPC coordination weights.",
    },
    {
        "id": "synchroflow_hybrid",
        "name": "SynchroFlow Full Autonomous Hybrid",
        "description": "Complete hierarchical integration of Vision, Max-Pressure, MAPPO, and MPC.",
    },
]


@router.get("")
@router.get("/")
async def list_controllers():
    return {
        "activeController": simulation_service.controller_type,
        "controllers": CANONICAL_CONTROLLERS,
    }


@router.post("/{controller_type}/select", response_model=CommandAckResponse)
async def select_controller(controller_type: ControllerType):
    cmd = CommandPayload(
        commandId=f"cmd-select-ctrl-{int(time.time()*1000)}",
        action="SET_CONTROLLER",
        timestamp=int(time.time() * 1000),
        payload={"controller": controller_type},
    )
    return simulation_service.handle_command(cmd)
