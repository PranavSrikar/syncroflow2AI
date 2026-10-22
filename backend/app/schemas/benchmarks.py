"""
SYNCHROFLOW AI — Pydantic Schemas for Health, Capabilities, and Benchmark Experiments
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from app.schemas.traffic import ControllerType


class ActiveEnginesStatus(BaseModel):
    sumoConnected: bool = False
    cvxpyMpcReady: bool = False
    mappoModelLoaded: bool = False
    yoloPerceptionOnline: bool = False


class BackendHealthResponse(BaseModel):
    status: Literal["ok", "degraded"] = "ok"
    version: str = "1.2.0"
    protocolVersion: str = "v1.2.0"
    serverTime: str
    activeEngines: ActiveEnginesStatus


class BenchmarkRequest(BaseModel):
    scenarioId: str = "balanced_traffic"
    seed: int = 42
    durationSec: int = 60
    controllers: List[ControllerType] = Field(
        default_factory=lambda: [
            "fixed",
            "actuated",
            "queue_adaptive",
            "max_pressure",
            "mpc_only",
            "mappo_assisted_mpc",
            "synchroflow_hybrid",
        ]
    )


class ControllerBenchmarkResult(BaseModel):
    controller: ControllerType
    controllerName: str
    scenarioName: str
    seed: int
    simDurationSec: float
    measuredAvgDelay: float
    measuredP95Delay: float
    measuredThroughput: float
    measuredMaxQueue: int
    executionStatus: str


class BenchmarkSuiteResponse(BaseModel):
    experimentId: str
    timestamp: str
    scenarioId: str
    seed: int
    results: List[ControllerBenchmarkResult]
