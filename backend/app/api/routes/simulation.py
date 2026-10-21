"""
SYNCHROFLOW AI — Simulation Lifecycle REST Routes
"""

import time
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.simulation_service import simulation_service
from app.schemas.telemetry import SimulationStatePayload
from app.schemas.commands import CommandPayload, CommandAckResponse

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])


class SpeedPayload(BaseModel):
    speed: float


class SeedPayload(BaseModel):
    seed: int


@router.get("/state", response_model=SimulationStatePayload)
async def get_state():
    return simulation_service.get_state_payload()


@router.post("/start", response_model=CommandAckResponse)
async def start_simulation():
    cmd = CommandPayload(
        commandId=f"cmd-start-{int(time.time()*1000)}",
        action="RESUME",
        timestamp=int(time.time() * 1000),
    )
    return simulation_service.handle_command(cmd)


@router.post("/pause", response_model=CommandAckResponse)
async def pause_simulation():
    cmd = CommandPayload(
        commandId=f"cmd-pause-{int(time.time()*1000)}",
        action="PAUSE",
        timestamp=int(time.time() * 1000),
    )
    return simulation_service.handle_command(cmd)


@router.post("/reset", response_model=CommandAckResponse)
async def reset_simulation():
    cmd = CommandPayload(
        commandId=f"cmd-reset-{int(time.time()*1000)}",
        action="RESET",
        timestamp=int(time.time() * 1000),
    )
    return simulation_service.handle_command(cmd)


@router.post("/step", response_model=CommandAckResponse)
async def step_simulation():
    cmd = CommandPayload(
        commandId=f"cmd-step-{int(time.time()*1000)}",
        action="STEP",
        timestamp=int(time.time() * 1000),
    )
    return simulation_service.handle_command(cmd)


@router.post("/speed", response_model=CommandAckResponse)
async def set_speed(payload: SpeedPayload):
    cmd = CommandPayload(
        commandId=f"cmd-speed-{int(time.time()*1000)}",
        action="SET_SPEED",
        timestamp=int(time.time() * 1000),
        payload={"speed": payload.speed},
    )
    return simulation_service.handle_command(cmd)


@router.post("/seed", response_model=CommandAckResponse)
async def set_seed(payload: SeedPayload):
    cmd = CommandPayload(
        commandId=f"cmd-seed-{int(time.time()*1000)}",
        action="SET_SEED",
        timestamp=int(time.time() * 1000),
        payload={"seed": payload.seed},
    )
    return simulation_service.handle_command(cmd)
