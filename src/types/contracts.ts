/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  ControllerType,
  WeatherMode,
  Direction,
  IntersectionSignalState,
  SimulationMetrics,
  ApproachTelemetry,
  Vehicle,
  TrafficScenario,
  SafetySupervisorReport,
} from './traffic.ts';

export const SYNCHROFLOW_PROTOCOL_VERSION = 'v1.2.0';

export type ProviderConnectionStatus =
  | 'local_demo'
  | 'connecting'
  | 'connected'
  | 'disconnected'
  | 'stale'
  | 'error';

export interface BackendHealthResponse {
  status: 'ok' | 'degraded';
  version: string;
  protocolVersion: string;
  serverTime: string;
  activeEngines: {
    sumoConnected: boolean;
    cvxpyMpcReady: boolean;
    mappoModelLoaded: boolean;
    yoloPerceptionOnline: boolean;
  };
}

export interface SimulationStatePayload {
  protocolVersion: string;
  sequenceNumber: number;
  timestamp: number;
  simTime: number;
  seed: number;
  isRunning: boolean;
  timeScale: number;
  controllerType: ControllerType;
  weather: WeatherMode;
  scenarioId: string;
  signals: IntersectionSignalState;
  vehicles: Vehicle[];
  telemetry: Record<Direction, ApproachTelemetry>;
  metrics: SimulationMetrics;
  safetyReport: SafetySupervisorReport;
  source: 'local_engine' | 'fastapi_sumo_backend';
}

export type CommandAction =
  | 'SET_CONTROLLER'
  | 'SET_WEATHER'
  | 'INJECT_EMERGENCY'
  | 'LOAD_SCENARIO'
  | 'MANUAL_PHASE_HOLD'
  | 'RELEASE_PHASE_HOLD'
  | 'PAUSE'
  | 'RESUME'
  | 'STEP'
  | 'RESET'
  | 'SET_SPEED'
  | 'SET_SEED'
  | 'PEDESTRIAN_CALL';

export interface CommandPayload {
  commandId: string;
  action: CommandAction;
  timestamp: number;
  payload?: any;
}

export interface CommandAckResponse {
  commandId: string;
  success: boolean;
  message?: string;
  executionTimestamp: number;
}

export interface WebSocketMessage {
  type: 'STATE_UPDATE' | 'COMMAND' | 'COMMAND_ACK' | 'ALERT' | 'HEARTBEAT';
  sequenceNumber: number;
  timestamp: number;
  data: any;
}
