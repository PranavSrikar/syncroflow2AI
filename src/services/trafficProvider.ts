/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { TrafficSimulationEngine, SimulationState } from '../simulation/engine.ts';
import {
  ProviderConnectionStatus,
  SimulationStatePayload,
  CommandPayload,
  CommandAckResponse,
  WebSocketMessage,
  SYNCHROFLOW_PROTOCOL_VERSION,
} from '../types/contracts.ts';
import { TrafficScenario, ControllerType, WeatherMode, Direction } from '../types/traffic.ts';

export interface ITrafficProvider {
  subscribe(callback: (state: SimulationState) => void): () => void;
  sendCommand(command: CommandPayload): Promise<CommandAckResponse>;
  getConnectionStatus(): ProviderConnectionStatus;
  getMode(): 'local_demo' | 'remote_backend';
  setMode(mode: 'local_demo' | 'remote_backend'): void;
  getEngine(): TrafficSimulationEngine;
}

export class TrafficProviderService implements ITrafficProvider {
  private localEngine: TrafficSimulationEngine;
  private currentMode: 'local_demo' | 'remote_backend' = 'local_demo';
  private connectionStatus: ProviderConnectionStatus = 'local_demo';
  private subscribers: Set<(state: SimulationState) => void> = new Set();

  // Remote WebSocket details
  private ws: WebSocket | null = null;
  private reconnectTimeoutId: any = null;
  private heartbeatIntervalId: any = null;
  private staleCheckIntervalId: any = null;
  private lastMessageTimestamp: number = 0;
  private lastSequenceNumber: number = 0;
  private reconnectBackoffMs: number = 1000;

  private pendingAcks = new Map<string, { resolve: (ack: CommandAckResponse) => void; timer: ReturnType<typeof setTimeout> }>();
  private remoteSnapshot: unknown = null;
  public getRemoteSnapshot(): unknown { return this.remoteSnapshot; }

  private wsUrl: string;
  private restUrl: string;

  constructor(initialScenario?: TrafficScenario, initialSeed: number = 42) {
    this.localEngine = new TrafficSimulationEngine(initialScenario, initialSeed);

    // Read environment variables or defaults
    const isVite = typeof import.meta !== 'undefined' && import.meta.env;
    this.wsUrl = (isVite && import.meta.env.VITE_BACKEND_WS_URL) || ((isVite && import.meta.env.VITE_BACKEND_API_URL) || 'http://127.0.0.1:8001/api/v1').replace(/^http/, 'ws').replace(/\/$/, '') + '/ws/traffic';
    this.restUrl = (isVite && import.meta.env.VITE_BACKEND_API_URL) || 'http://127.0.0.1:8001/api/v1';
  }

  public getEngine(): TrafficSimulationEngine {
    return this.localEngine;
  }

  public getMode(): 'local_demo' | 'remote_backend' {
    return this.currentMode;
  }

  public setMode(mode: 'local_demo' | 'remote_backend'): void {
    if (this.currentMode === mode) return;
    this.currentMode = mode;

    if (mode === 'remote_backend') {
      this.initRemoteConnection();
    } else {
      this.cleanupRemoteConnection();
      this.connectionStatus = 'local_demo';
    }
  }

  public getConnectionStatus(): ProviderConnectionStatus {
    return this.connectionStatus;
  }

  public subscribe(callback: (state: SimulationState) => void): () => void {
    this.subscribers.add(callback);
    // Send immediate state update
    callback(this.localEngine.getState());

    return () => {
      this.subscribers.delete(callback);
    };
  }

  public notifySubscribers(state: SimulationState): void {
    this.subscribers.forEach((cb) => cb(state));
  }

  public async sendCommand(command: CommandPayload): Promise<CommandAckResponse> {
    if (this.currentMode === 'local_demo') {
      return this.handleLocalCommand(command);
    }

    // Remote mode command via REST or WebSocket
    try {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        return await new Promise<CommandAckResponse>(resolve => {
          const timer = setTimeout(() => { this.pendingAcks.delete(command.commandId); resolve({ commandId: command.commandId, success: false, message: 'Backend acknowledgement timed out', executionTimestamp: Date.now() }); }, 10000);
          this.pendingAcks.set(command.commandId, { resolve, timer });
          this.ws!.send(JSON.stringify({ type: 'COMMAND', sequenceNumber: this.lastSequenceNumber, timestamp: Date.now(), data: command }));
        });
      }
      const routes: Record<string, string> = { STEP: '/simulation/step', PAUSE: '/simulation/pause', RESUME: '/simulation/start', RESET: '/simulation/reset', SET_SPEED: '/simulation/speed', SET_SEED: '/simulation/seed' };
      const route = routes[command.action];
      if (!route) throw new Error('This legacy command requires a connected synthetic-provider WebSocket');
      const resp = await fetch(`${this.restUrl}${route}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Protocol-Version': SYNCHROFLOW_PROTOCOL_VERSION,
        },
        body: command.payload ? JSON.stringify(command.payload) : undefined,
        signal: AbortSignal.timeout(10000),
      });

      if (!resp.ok) {
        throw new Error(`HTTP Error ${resp.status}`);
      }

      const data = await resp.json();
      return data;
    } catch (err: any) {
      return { commandId: command.commandId, success: false, message: `Remote command failed: ${err.message}. Local engine was not changed.`, executionTimestamp: Date.now() };
    }
  }

  private handleLocalCommand(command: CommandPayload): CommandAckResponse {
    const engine = this.localEngine;

    switch (command.action) {
      case 'PAUSE':
        engine.setPlaying(false);
        break;
      case 'RESUME':
        engine.setPlaying(true);
        break;
      case 'STEP':
        engine.step(0.5);
        break;
      case 'RESET':
        engine.reset();
        break;
      case 'SET_SPEED':
        engine.setSpeed(command.payload?.speed ?? 1);
        break;
      case 'SET_SEED':
        engine.setSeed(command.payload?.seed ?? 42);
        break;
      case 'SET_CONTROLLER':
        engine.setController(command.payload?.controller as ControllerType);
        break;
      case 'SET_WEATHER':
        engine.setWeather(command.payload?.weather as WeatherMode);
        break;
      case 'INJECT_EMERGENCY':
        engine.injectEmergency(command.payload?.direction as Direction, command.payload?.type);
        break;
      case 'PEDESTRIAN_CALL':
        engine.requestPedestrianCall(command.payload?.direction as Direction);
        break;
      case 'LOAD_SCENARIO':
        engine.loadScenario(command.payload?.scenarioId);
        break;
    }

    this.notifySubscribers(engine.getState());

    return {
      commandId: command.commandId,
      success: true,
      message: `Local execution of ${command.action} completed successfully`,
      executionTimestamp: Date.now(),
    };
  }

  private initRemoteConnection(): void {
    this.connectionStatus = 'connecting';
    this.cleanupRemoteConnection();
    this.lastSequenceNumber = 0;

    try {
      this.ws = new WebSocket(this.wsUrl);

      this.ws.onopen = () => {
        this.connectionStatus = 'connected';
        this.reconnectBackoffMs = 1000;
        this.lastMessageTimestamp = Date.now();

        // Start heartbeat and stale-state checker
        this.startHeartbeat();
        this.startStaleChecker();
      };

      this.ws.onmessage = (event) => {
        try {
          const msg: WebSocketMessage = JSON.parse(event.data);
          this.lastMessageTimestamp = Date.now();
          if (msg.type === 'COMMAND_ACK') {
            const ack = msg.data as CommandAckResponse;
            const pending = this.pendingAcks.get(ack.commandId);
            if (pending) { clearTimeout(pending.timer); pending.resolve(ack); this.pendingAcks.delete(ack.commandId); }
            this.lastSequenceNumber = msg.sequenceNumber;
            return;
          }

          // Sequence-number validation
          if (msg.sequenceNumber < this.lastSequenceNumber) {
            console.warn('Dropped out-of-order packet:', msg.sequenceNumber);
            return;
          }
          this.lastSequenceNumber = msg.sequenceNumber;

          if (msg.type === 'STATE_UPDATE') {
            this.connectionStatus = 'connected';
            this.remoteSnapshot = msg.data;
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      this.ws.onerror = () => {
        this.connectionStatus = 'error';
      };

      this.ws.onclose = () => {
        if (this.currentMode === 'remote_backend') {
          this.connectionStatus = 'disconnected';
          this.scheduleReconnect();
        }
      };
    } catch (e) {
      this.connectionStatus = 'error';
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimeoutId) clearTimeout(this.reconnectTimeoutId);

    this.reconnectTimeoutId = setTimeout(() => {
      if (this.currentMode === 'remote_backend') {
        this.initRemoteConnection();
      }
    }, this.reconnectBackoffMs);

    // Exponential backoff up to 15s
    this.reconnectBackoffMs = Math.min(15000, this.reconnectBackoffMs * 1.8);
  }

  private startHeartbeat(): void {
    if (this.heartbeatIntervalId) clearInterval(this.heartbeatIntervalId);
    this.heartbeatIntervalId = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'HEARTBEAT', timestamp: Date.now() }));
      }
    }, 5000);
  }

  private startStaleChecker(): void {
    if (this.staleCheckIntervalId) clearInterval(this.staleCheckIntervalId);
    this.staleCheckIntervalId = setInterval(() => {
      if (this.currentMode === 'remote_backend' && this.connectionStatus === 'connected') {
        const timeSinceLast = Date.now() - this.lastMessageTimestamp;
        if (timeSinceLast > 2500) {
          this.connectionStatus = 'stale';
        }
      }
    }, 1000);
  }

  public cleanupRemoteConnection(): void {
    if (this.reconnectTimeoutId) clearTimeout(this.reconnectTimeoutId);
    if (this.heartbeatIntervalId) clearInterval(this.heartbeatIntervalId);
    if (this.staleCheckIntervalId) clearInterval(this.staleCheckIntervalId);

    for (const [id, pending] of this.pendingAcks) { clearTimeout(pending.timer); pending.resolve({ commandId: id, success: false, message: 'Remote connection closed; command completion is unknown', executionTimestamp: Date.now() }); }
    this.pendingAcks.clear();
    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.onerror = null;
      this.ws.onclose = null;
      if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
        this.ws.close();
      }
      this.ws = null;
    }
  }
}

// Singleton provider instance
export const trafficProvider = new TrafficProviderService();
