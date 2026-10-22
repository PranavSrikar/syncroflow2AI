"""
Integration tests for WebSocket stream and bidirectional commands
"""

import json
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_websocket_stream_and_heartbeat():
    with client.websocket_connect("/api/v1/ws/traffic") as websocket:
        # Receive immediate initial state update
        msg_raw = websocket.receive_text()
        msg = json.loads(msg_raw)
        assert msg["type"] == "STATE_UPDATE"
        assert msg["data"]["protocolVersion"] == "v1.2.0"
        assert "signals" in msg["data"]

        # Send heartbeat
        websocket.send_text(
            json.dumps(
                {
                    "type": "HEARTBEAT",
                    "sequenceNumber": 1,
                    "timestamp": 1234567,
                    "data": {},
                }
            )
        )
        reply_raw = websocket.receive_text()
        reply = json.loads(reply_raw)
        assert reply["type"] == "HEARTBEAT"
        assert reply["data"]["status"] == "ok"


def test_websocket_command_ack():
    with client.websocket_connect("/api/v1/ws/traffic") as websocket:
        # Drain initial message
        _ = websocket.receive_text()

        # Send pause command
        cmd_msg = {
            "type": "COMMAND",
            "sequenceNumber": 2,
            "timestamp": 1234568,
            "data": {
                "commandId": "ws-cmd-pause",
                "action": "PAUSE",
                "timestamp": 1234568,
            },
        }
        websocket.send_text(json.dumps(cmd_msg))

        ack_raw = websocket.receive_text()
        ack = json.loads(ack_raw)
        assert ack["type"] == "COMMAND_ACK"
        assert ack["data"]["commandId"] == "ws-cmd-pause"
        assert ack["data"]["success"] is True
