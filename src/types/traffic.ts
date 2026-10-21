/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export type Direction = 'north' | 'south' | 'east' | 'west';

export type MovementType = 'through' | 'left' | 'right' | 'uturn';

export type VehicleType =
  | 'car'
  | 'suv'
  | 'bus'
  | 'truck'
  | 'rickshaw'
  | 'motorcycle'
  | 'ambulance'
  | 'fire_engine';

export interface Vehicle {
  id: string;
  type: VehicleType;
  approach: Direction;
  movement: MovementType;
  laneIndex: number; // 0: left/uturn, 1: through, 2: right/through
  progress: number; // 0 to 1 along entry -> intersection -> exit path
  speed: number; // m/s
  targetSpeed: number; // m/s
  acceleration: number; // m/s^2
  waitingTime: number; // seconds spent with speed < 1.0 m/s
  totalTripTime: number; // seconds since spawn
  isStopped: boolean;
  isEmergency: boolean;
  color: string;
  length: number;
  width: number;
  distanceToStopLine: number; // meters
  spawnTime: number;
  entryTime: number;
  exitTime?: number;
  reactionDelay: number; // driver reaction time in seconds
  isBlockedByIncident?: boolean;
}

export type SignalLightColor = 'red' | 'yellow' | 'green';

export interface ApproachSignalState {
  through: SignalLightColor;
  left: SignalLightColor;
  right: SignalLightColor;
  remainingGreen: number; // seconds
  yellowDuration: number;
  allRedDuration: number;
}

export type TransitionStage =
  | 'GREEN'
  | 'GREEN_TERMINATION'
  | 'YELLOW_CLEARANCE'
  | 'ALL_RED_CLEARANCE'
  | 'NEW_GREEN'
  | 'PREEMPTION_CLEARANCE'
  | 'MANUAL_HOLD'
  | 'SAFE_FALLBACK';

export interface PedestrianCrossingState {
  direction: Direction;
  state: 'DONT_WALK' | 'WALK' | 'FLASHING_DONT_WALK';
  waitingCount: number;
  crossingCount: number;
  remainingTime: number;
  hasCallRequest: boolean;
  avgWaitTime: number;
}

export interface SafetySupervisorReport {
  timestamp: number;
  conflictCheckPassed: boolean;
  minGreenRespected: boolean;
  yellowClearanceRespected: boolean;
  allRedClearanceRespected: boolean;
  pedestrianClearanceHonored: boolean;
  emergencyCorridorIsolated: boolean;
  illegalTransitionAttempted: boolean;
  activeViolations: string[];
  lastInterlockTriggered?: string;
  consecutiveSafeCycles: number;
}

export interface IntersectionSignalState {
  currentPhaseIndex: number; // 0: NS Thru/Right, 1: NS Left, 2: EW Thru/Right, 3: EW Left
  phaseName: string;
  cycleTime: number; // total cycle e.g. 112s
  elapsedInPhase: number;
  phaseDuration: number;
  nextPhaseIndex: number;
  transitionStage: TransitionStage;
  transitionTimer: number;
  approachSignals: Record<Direction, ApproachSignalState>;
  pedestrianSignals: Record<Direction, PedestrianCrossingState>;
  safetyReport: SafetySupervisorReport;
  isPreemptActive: boolean;
  preemptReason?: string;
  preemptVehicleId?: string;
  isManualOverride: boolean;
  manualHeldPhase?: number;
}

export type ControllerType =
  | 'fixed'
  | 'actuated'
  | 'queue_adaptive'
  | 'max_pressure'
  | 'mpc_only'
  | 'mappo_assisted_mpc'
  | 'synchroflow_hybrid';

export interface ApproachTelemetry {
  direction: Direction;
  name: string;
  queuedVehicles: number;
  dischargeRate: number; // veh/sec measured from real departure events
  maxPressureScore: number;
  avgWaitTime: number; // seconds measured from actual stopped vehicles
  p95WaitTime: number; // seconds (95th percentile)
  oldestWaitingAge: number; // seconds
  approachSpeed: number; // km/h
  spillbackDetected: boolean;
  laneQueues: {
    left: number;
    through: number;
    right: number;
  };
}

export interface SimulationMetrics {
  totalVehiclesSpawned: number;
  totalVehiclesPassed: number;
  totalActiveVehicles: number;
  totalCompletedTrips: number;
  avgWaitTime: number; // strictly measured total stopped time / total vehicles
  maxWaitTime: number; // strictly measured maximum waiting time
  p95WaitTime: number; // strictly measured 95th percentile waiting time
  totalQueueLength: number; // strictly count of vehicles currently stopped before stop line
  maxQueueObserved: number; // peak observed queue
  intersectionOccupancy: number; // actual % of physical road capacity occupied
  throughputPerHour: number; // completed vehicles scaled to 1hr rate
  performanceIndex: number; // 0-100 score based on actual delay & throughput
  carbonEmissionsSavedKg: number; // clearly labeled: Stage 1 browser estimation
  emergencyTripCount: number;
  emergencyAvgTravelTime: number; // strictly measured seconds
  pedestrianAvgWaitTime: number; // strictly measured seconds
  starvationAlertsCount: number;
  maxRedViolationCount: number;
  safetyViolationAttemptsPrevented: number;
}

export interface MPCDecisionData {
  horizonSteps: number;
  predictionQueueNS: number[];
  predictionQueueEW: number[];
  optimalGreenSplits: { phase: string; duration: number }[];
  costFunctionValue: number;
  predictedDelayReductionPct: number;
  confidenceScore: number;
  solverTimeMs: number;
  solverType: 'Browser Receding-Horizon Evaluator (Stage 1)' | 'CVXPY OSQP Solver (Stage 2 Backend)';
}

export interface MAPPODecisionData {
  criticValue: number;
  advantage: number;
  actionProbabilities: { action: string; prob: number }[];
  entropy: number;
  rewardComponents: {
    throughput: number;
    delayPenalty: number;
    emergencyBonus: number;
    fairnessPenalty: number;
  };
  policyStatus: 'Advisory demonstration — trained policy not connected (Awaiting Stage 2 PyTorch checkpoint)';
}

export type WeatherMode = 'day' | 'night' | 'monsoon' | 'fog';

export type CameraViewPreset = 'aerial' | 'street' | 'top_down';

export interface TrafficScenario {
  id: string;
  numericId: number; // 1 to 25
  name: string;
  category: 'standard' | 'rush_hour' | 'incident' | 'weather' | 'emergency' | 'network' | 'failure';
  description: string;
  duration: number; // in seconds
  arrivalRates: Record<Direction, number>; // vehicles per hour
  composition: {
    car: number;
    suv: number;
    bus: number;
    truck: number;
    rickshaw: number;
    motorcycle: number;
  };
  weather: WeatherMode;
  initialQueueCount?: Record<Direction, number>;
  // Scenario Dynamics Flags (Ensuring observable difference in simulation)
  hasIncident?: boolean;
  incidentApproach?: Direction;
  incidentLane?: number;
  incidentType?: 'stalled_vehicle' | 'accident' | 'truck_obstruction' | 'bus_dwell' | 'uturn_block';
  autoInjectEmergency?: boolean;
  emergencyVehicleType?: 'ambulance' | 'fire_engine';
  emergencyApproach?: Direction;
  emergencyScheduleSec?: number;
  policeOverrideActive?: boolean;
  policeHeldPhase?: number;
  roadClosureApproach?: Direction;
  sensorDegradationType?: 'camera_glare' | 'camera_outage' | 'rsu_disconnect' | 'mpc_timeout' | 'mappo_disconnect' | 'false_positive_alert';
  pedestrianDemandLevel?: 'low' | 'moderate' | 'heavy';
  downstreamSpillbackActive?: boolean;
  networkCoordinationOffsetSec?: number;
}

export interface IoTSensorNode {
  id: string;
  type: 'camera' | 'lidar' | 'loop' | 'rsu';
  name: string;
  position: [number, number]; // x, y on 2D radar overlay
  status: 'active' | 'degraded' | 'calibrating' | 'offline';
  coveragePct: number;
  lastReading: string;
  latencyMs: number;
  assignedApproach: Direction;
}

export interface AnomalyAlert {
  id: string;
  timestamp: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  location: string;
}
