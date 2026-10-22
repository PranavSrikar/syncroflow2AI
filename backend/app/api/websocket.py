"""
SYNCHROFLOW AI — WebSocket State Streaming & Real-Time Command Dispatch
Endpoint: /api/v1/ws/traffic
"""

import json
import time
import asyncio
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.simulation_service import simulation_service
from app.schemas.commands import CommandPayload
from app.core.logging import logger

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast_state(self):
        if not self.active_connections:
            return

        payload = simulation_service.get_state_payload()
        msg = {
            "type": "STATE_UPDATE",
            "sequenceNumber": payload.sequenceNumber,
            "timestamp": payload.timestamp,
            "data": payload.model_dump(),
        }
        raw_msg = json.dumps(msg)

        disconnected = set()
        for conn in self.active_connections:
            try:
                await conn.send_text(raw_msg)
            except Exception:
                disconnected.add(conn)

        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@router.websocket("/ws/traffic")
async def websocket_traffic_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Send immediate state on connect
    try:
        initial_state = simulation_service.get_state_payload()
        await websocket.send_text(
            json.dumps(
                {
                    "type": "STATE_UPDATE",
                    "sequenceNumber": initial_state.sequenceNumber,
                    "timestamp": initial_state.timestamp,
                    "data": initial_state.model_dump(),
                }
            )
        )

        while True:
            text = await websocket.receive_text()
            data = json.loads(text)
            msg_type = data.get("type")

            if msg_type == "COMMAND":
                cmd_data = data.get("data", {})
                cmd = CommandPayload(**cmd_data)
                ack = simulation_service.handle_command(cmd)

                ack_msg = {
                    "type": "COMMAND_ACK",
                    "sequenceNumber": simulation_service.sequence_number,
                    "timestamp": int(time.time() * 1000),
                    "data": ack.model_dump(),
                }
                await websocket.send_text(json.dumps(ack_msg))
            elif msg_type == "HEARTBEAT":
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "HEARTBEAT",
                            "sequenceNumber": simulation_service.sequence_number,
                            "timestamp": int(time.time() * 1000),
                            "data": {"status": "ok"},
                        }
                    )
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
        manager.disconnect(websocket)
