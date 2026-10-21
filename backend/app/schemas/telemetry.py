"""
SYNCHROFLOW AI — Pydantic Schemas for WebSocket State Messages & Telemetry
"""

from typing import List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.traffic import (
    Direction,
    ControllerType,
    WeatherMode,
    IntersectionSignalState,
    Vehicle,
    ApproachTelemetry,
    SimulationMetrics,
    SafetySupervisorReport,
    IoTSensorNode,
    AnomalyAlert,
    MPCDecisionData,
    MAPPODecisionData,
)


class SimulationStatePayload(BaseModel):
    protocolVersion: str = "v1.2.0"
    sequenceNumber: int
    timestamp: int
    simTime: float
    seed: int
    isRunning: bool
    timeScale: float
    controllerType: ControllerType
    weather: WeatherMode
    scenarioId: str
    signals: IntersectionSignalState
    vehicles: List[Vehicle]
    telemetry: Dict[Direction, ApproachTelemetry]
    metrics: SimulationMetrics
    safetyReport: SafetySupervisorReport
    sensorNodes: List[IoTSensorNode] = Field(default_factory=list)
    recentAlerts: List[AnomalyAlert] = Field(default_factory=list)
    mpcData: Optional[MPCDecisionData] = None
    mappoData: Optional[MAPPODecisionData] = None
    source: Literal["local_engine", "fastapi_sumo_backend"] = "fastapi_sumo_backend"


class WebSocketMessage(BaseModel):
    type: Literal["STATE_UPDATE", "COMMAND", "COMMAND_ACK", "ALERT", "HEARTBEAT"]
    sequenceNumber: int
    timestamp: int
    data: Any
