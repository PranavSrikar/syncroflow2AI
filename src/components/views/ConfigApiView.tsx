/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import {
  Server,
  Radio,
  Wifi,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Info,
  ShieldCheck,
  Send,
} from 'lucide-react';
import { trafficProvider } from '../../services/trafficProvider.ts';
import { SYNCHROFLOW_PROTOCOL_VERSION } from '../../types/contracts.ts';

export const ConfigApiView: React.FC = () => {
  const [mode, setMode] = useState<'local_demo' | 'remote_backend'>(trafficProvider.getMode());
  const [status, setStatus] = useState(trafficProvider.getConnectionStatus());
  const [testAck, setTestAck] = useState<string | null>(null);

  const toggleMode = (newMode: 'local_demo' | 'remote_backend') => {
    setMode(newMode);
    trafficProvider.setMode(newMode);
    setStatus(trafficProvider.getConnectionStatus());
  };

  const handleSendHeartbeatTest = async () => {
    setTestAck('Dispatching test ping command...');
    const res = await trafficProvider.sendCommand({
      commandId: `cmd-test-${Date.now()}`,
      action: 'STEP',
      timestamp: Date.now(),
    });
    setTestAck(`Acknowledgement received: ${res.message} at ${new Date(res.executionTimestamp).toLocaleTimeString()}`);
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto text-slate-200 select-none">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider">
            <Server className="w-4 h-4" />
            Backend Integration & API Contract Configuration
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1 font-sans">
            Simulation Data Provider & WebSocket Manager
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Seamlessly switch between deterministic local browser execution (Stage 1) and remote Python FastAPI / SUMO TraCI backend (Stage 2).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-mono">Protocol:</span>
          <span className="text-xs font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-500/30 px-2.5 py-1 rounded-lg">
            {SYNCHROFLOW_PROTOCOL_VERSION}
          </span>
        </div>
      </div>

      {/* Provider Mode Switcher Card */}
      <div className="p-5 bg-slate-950/90 border border-slate-800 rounded-xl space-y-4">
        <h3 className="text-sm font-semibold text-slate-100">
          Simulation Authority Provider Mode
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Local Mode */}
          <button
            onClick={() => toggleMode('local_demo')}
            className={`p-4 rounded-xl border text-left transition-all ${
              mode === 'local_demo'
                ? 'bg-cyan-950/40 border-cyan-500/60 shadow-lg ring-1 ring-cyan-500/30'
                : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-100">Stage 1: Local Deterministic Engine</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 border border-emerald-500/40 text-emerald-400 font-mono">
                ACTIVE
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
              Browser-based microscopic/mesoscopic simulation running with seeded Mulberry32 PRNG, Intelligent Driver Model, and independent safety supervisor.
            </p>
          </button>

          {/* Remote Mode */}
          <button
            onClick={() => toggleMode('remote_backend')}
            className={`p-4 rounded-xl border text-left transition-all ${
              mode === 'remote_backend'
                ? 'bg-cyan-950/40 border-cyan-500/60 shadow-lg ring-1 ring-cyan-500/30'
                : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-100">Stage 2: Remote Python FastAPI Backend</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-400 font-mono">
                STANDBY
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
              Connects to authoritative external SUMO / TraCI simulation, CVXPY quadratic MPC, and PyTorch MAPPO models via WebSocket & REST at 10Hz.
            </p>
          </button>
        </div>
      </div>

      {/* Connection State & Endpoints Table */}
      <div className="bg-slate-950/90 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-100">
            Endpoint & Communication Health Status
          </h3>
          <span className="text-xs font-mono text-cyan-400">
            Status: {mode === 'local_demo' ? 'Local Standalone' : status.toUpperCase()}
          </span>
        </div>

        <div className="space-y-2 text-xs font-mono">
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">WebSocket URL:</span>
            <span className="text-cyan-300">ws://localhost:8000/api/v1/ws/traffic</span>
          </div>
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">REST API Base:</span>
            <span className="text-slate-300">http://localhost:8000/api/v1</span>
          </div>
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">Sequence-Number Validation:</span>
            <span className="text-emerald-400">Active (Detects dropped/stale states)</span>
          </div>
        </div>

        <div className="pt-2 flex items-center gap-3">
          <button
            onClick={handleSendHeartbeatTest}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-xl text-xs font-medium text-slate-200 flex items-center gap-2 transition-colors"
          >
            <Send className="w-3.5 h-3.5 text-cyan-400" />
            <span>Test Command Dispatch & Ack</span>
          </button>

          {testAck && <span className="text-xs text-emerald-400 font-mono">{testAck}</span>}
        </div>
      </div>
    </div>
  );
};
