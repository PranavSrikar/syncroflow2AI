import asyncio
from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from app.services.sumo_runtime import sumo_runtime
from app.services.sumo_network_safety import NetworkSafetyModel

router = APIRouter(prefix="/api/v1/sumo", tags=["SUMO Simulation"])


class SumoEmergencyInjection(BaseModel):
    approach: Literal["north", "south", "east", "west"]
    priority: int = Field(default=1, ge=1, le=3)
    junctionId: str | None = None


class SumoEmergencyRequest(BaseModel):
    vehicleId: str = Field(min_length=1, max_length=128)
    priority: int = Field(default=1, ge=1, le=3)
    junctionId: str | None = None


@router.post("/emergencies/inject")
def inject_emergency(request: SumoEmergencyInjection):
    try:
        return sumo_runtime.inject_emergency(request.approach, request.priority, request.junctionId)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/emergencies/request")
def request_emergency(request: SumoEmergencyRequest):
    try:
        return sumo_runtime.emergency_request(request.vehicleId, request.priority, request.junctionId)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/emergencies/status")
def emergency_status():
    return sumo_runtime.snapshot()["emergencyPriority"]


@lru_cache(maxsize=2)
def network_model(pedestrian):
    name = "junction.pedestrian-test.net.xml" if pedestrian else "junction.net.xml"
    path = Path(__file__).resolve().parents[3] / "sumo_scenarios" / "four_way_basic" / name
    return NetworkSafetyModel(path)


@router.get("/network-safety")
def network_safety(pedestrian: bool = False):
    return network_model(pedestrian).audit()

@router.get("/status")
def status():
    return sumo_runtime.snapshot()

@router.get("/telemetry")
def telemetry():
    state = sumo_runtime.snapshot()
    if not state["connected"]:
        raise HTTPException(409, "SUMO is not connected")
    return state["telemetry"]

@router.post("/{action}")
def command(action: str, scenario: str | None = None, controller: str | None = None, seed: int | None = None, paused: bool = False,
            mpc_budget_ms: float | None = Query(default=None, ge=0, le=1000)):
    if action not in {"start", "pause", "step", "stop"}:
        raise HTTPException(404, "Unknown SUMO action")
    try:
        state = sumo_runtime.command(action, scenario, controller, seed, paused, mpc_budget_ms)
        return state["telemetry"] if action == "step" else {"success": True, **state}
    except Exception as exc:
        raise HTTPException(409, str(exc)) from exc

@router.websocket("/ws")
async def stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(sumo_runtime.snapshot())
            await asyncio.sleep(0.5)
    except (WebSocketDisconnect, RuntimeError, OSError):
        pass
