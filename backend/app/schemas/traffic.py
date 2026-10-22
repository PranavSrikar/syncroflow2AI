"""
SYNCHROFLOW AI — Pydantic Schemas for Traffic, Signal State & Telemetry
Mirrors src/types/traffic.ts exactly for wire-level compatibility.
"""

from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field

Direction = Literal["north", "south", "east", "west"]

ControllerType = Literal[
    "fixed",
    "actuated",
    "queue_adaptive",
    "max_pressure",
    "mpc_only",
    "mappo_assisted_mpc",
    "synchroflow_hybrid",
]

WeatherMode = Literal["clear", "rain", "fog", "monsoon"]

VehicleType = Literal[
    "sedan",
    "suv",
    "bus",
    "truck",
    "rickshaw",
    "motorcycle",
    "ambulance",
    "fire_engine",
]

MovementType = Literal["through", "left", "right", "uturn"]

SignalLightColor = Literal["red", "yellow", "green"]

TransitionStage = Literal[
    "GREEN",
    "GREEN_TERMINATION",
    "YELLOW_CLEARANCE",
    "ALL_RED_CLEARANCE",
]


class ApproachSignalState(BaseModel):
    through: SignalLightColor
    left: SignalLightColor
    right: SignalLightColor
    remainingGreen: float
    yellowDuration: float
    allRedDuration: float


class PedestrianCrossingState(BaseModel):
    direction: Direction
    state: Literal["walk", "flashing_dont_walk", "dont_walk"]
    remainingSec: float
    waitingCount: int
    hasCallRequest: bool


class SafetySupervisorReport(BaseModel):
    conflictCheckPassed: bool
    minGreenSatisfied: bool
    clearanceEnforced: bool
    emergencyPreemptSafe: bool
    activeViolations: List[str] = Field(default_factory=list)
    lastInterlockTriggered: Optional[str] = None
    consecutiveSafeCycles: int = 0


class IntersectionSignalState(BaseModel):
    currentPhaseIndex: int
    phaseName: str
    cycleTime: float
    elapsedInPhase: float
    phaseDuration: float
    nextPhaseIndex: int
    transitionStage: TransitionStage
    transitionTimer: float
    approachSignals: Dict[Direction, ApproachSignalState]
    pedestrianSignals: Dict[Direction, PedestrianCrossingState]
    safetyReport: SafetySupervisorReport
    isPreemptActive: bool
    preemptReason: Optional[str] = None
    preemptVehicleId: Optional[str] = None
    isManualOverride: bool = False
    manualHeldPhase: Optional[int] = None


class Vehicle(BaseModel):
    id: str
    type: VehicleType
    approach: Direction
    movement: MovementType
    laneIndex: int
    progress: float
    speed: float
    targetSpeed: float
    acceleration: float
    waitingTime: float
    totalTripTime: float
    isStopped: bool
    isEmergency: bool
    color: str
    length: float
    width: float
    distanceToStopLine: float
    spawnTime: float
    entryTime: float
    exitTime: Optional[float] = None
    reactionDelay: float
    isBlockedByIncident: Optional[bool] = False


class LaneQueues(BaseModel):
    left: int
    through: int
    right: int


class ApproachTelemetry(BaseModel):
    direction: Direction
    name: str
    queuedVehicles: int
    dischargeRate: float
    maxPressureScore: float
    avgWaitTime: float
    p95WaitTime: float
    oldestWaitingAge: float
    approachSpeed: float
    spillbackDetected: bool
    laneQueues: LaneQueues


class SimulationMetrics(BaseModel):
    avgWaitTime: float
    p95WaitTime: float
    totalCompletedTrips: int
    totalVehiclesSpawned: int
    activeVehicleCount: int
    throughputVehPerHour: float
    maxQueueLength: int
    emergencyMeanTravelTimeSec: float
    safetyInterlockViolationsAvoided: int
    fuelSavedLiters: float
    co2AbatementKg: float
    performanceIndex: int


class GreenSplit(BaseModel):
    phase: str
    duration: int


class MPCDecisionData(BaseModel):
    costFunctionValue: float
    predictedDelayReductionPct: float
    horizonSteps: int
    optimalGreenSplits: List[GreenSplit]
    forecastQueueMatrix: List[List[float]] = Field(default_factory=list)


class MAPPORewardComponents(BaseModel):
    throughput: float
    delayPenalty: float
    emergencyBonus: float
    fairnessPenalty: float


class MAPPODecisionData(BaseModel):
    policyEntropy: float
    valueLoss: float
    criticValue: float
    coordinationScore: float
    neighborMessagePayload: Dict[str, float] = Field(default_factory=dict)
    rewardComponents: MAPPORewardComponents


class IoTSensorNode(BaseModel):
    id: str
    name: str
    approach: Direction
    type: Literal["dsrc_rsu", "camera", "radar", "inductive_loop", "lidar"]
    status: Literal["healthy", "degraded", "fault", "calibrating"]
    latencyMs: float
    packetLossPct: float
    batteryPct: Optional[float] = None
    firmwareVersion: str
    lastReadingTimestamp: int
    detectedCount: int


class AnomalyAlert(BaseModel):
    id: str
    timestamp: int
    severity: Literal["info", "warning", "critical"]
    title: str
    description: str
    source: str
    acknowledged: bool = False
