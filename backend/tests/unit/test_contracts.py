"""
Unit tests for Pydantic Wire Contracts & Schemas
Ensures full alignment with TypeScript contracts in src/types/contracts.ts & traffic.ts
"""

import pytest
from app.schemas.traffic import (
    IntersectionSignalState,
    Vehicle,
    ApproachTelemetry,
    SimulationMetrics,
    SafetySupervisorReport,
)
from app.schemas.telemetry import SimulationStatePayload
from app.schemas.commands import CommandPayload, CommandAckResponse
from app.schemas.benchmarks import BackendHealthResponse, ActiveEnginesStatus


def test_safety_report_schema():
    report = SafetySupervisorReport(
        conflictCheckPassed=True,
        minGreenSatisfied=True,
        clearanceEnforced=True,
        emergencyPreemptSafe=True,
        activeViolations=[],
        lastInterlockTriggered=None,
        consecutiveSafeCycles=5,
    )
    assert report.conflictCheckPassed is True
    assert report.consecutiveSafeCycles == 5


def test_command_payload_ack():
    cmd = CommandPayload(
        commandId="test-cmd-1",
        action="PAUSE",
        timestamp=1234567890,
    )
    assert cmd.action == "PAUSE"

    ack = CommandAckResponse(
        commandId=cmd.commandId,
        success=True,
        message="Paused",
        executionTimestamp=1234567891,
    )
    assert ack.success is True
    assert ack.commandId == "test-cmd-1"


def test_health_response_schema():
    health = BackendHealthResponse(
        status="ok",
        version="1.2.0",
        protocolVersion="v1.2.0",
        serverTime="2026-10-21T12:00:00Z",
        activeEngines=ActiveEnginesStatus(
            sumoConnected=False,
            cvxpyMpcReady=False,
            mappoModelLoaded=False,
            yoloPerceptionOnline=False,
        ),
    )
    assert health.status == "ok"
    assert health.protocolVersion == "v1.2.0"
