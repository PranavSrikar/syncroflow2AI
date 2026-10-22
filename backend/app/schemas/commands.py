"""
SYNCHROFLOW AI — Pydantic Schemas for Commands & Remote Control
Mirrors src/types/contracts.ts
"""

from typing import Optional, Any, Literal
from pydantic import BaseModel, Field

CommandAction = Literal[
    "SET_CONTROLLER",
    "SET_WEATHER",
    "INJECT_EMERGENCY",
    "LOAD_SCENARIO",
    "MANUAL_PHASE_HOLD",
    "RELEASE_PHASE_HOLD",
    "PAUSE",
    "RESUME",
    "STEP",
    "RESET",
    "SET_SPEED",
    "SET_SEED",
    "PEDESTRIAN_CALL",
]


class CommandPayload(BaseModel):
    commandId: str
    action: CommandAction
    timestamp: int
    payload: Optional[Any] = None


class CommandAckResponse(BaseModel):
    commandId: str
    success: bool
    message: Optional[str] = None
    executionTimestamp: int
