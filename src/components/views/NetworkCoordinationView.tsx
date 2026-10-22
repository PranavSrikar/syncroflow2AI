/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Network, ArrowRight, Activity, ShieldAlert, CheckCircle2, Info } from 'lucide-react';
import { SimulationMetrics } from '../../types/traffic.ts';

interface NetworkCoordinationViewProps {
  metrics: SimulationMetrics;
}

export const NetworkCoordinationView: React.FC<NetworkCoordinationViewProps> = ({ metrics }) => {
  const [corridorOffsetSec, setCorridorOffsetSec] = useState<number>(14);

  // 3 Nodes along 5th Avenue arterial corridor
  const nodes = [
    {
      id: 'NODE-73',
      name: '5th Ave & Elm St (Node 73)',
      distanceMeters: 450,
      currentPhase: 'Phase 1 (Through)',
      occupancyPct: 62,
      greenSplit: '36s / 112s',
      offsetSec: 0,
      upstreamQueue: 8,
    },
    {
      id: 'SC-INT-74',
      name: '5th Ave & Oak St (Node 74 - Master)',
      distanceMeters: 0,
      currentPhase: 'Phase 1 (Through & Right)',
      occupancyPct: metrics.intersectionOccupancy,
      greenSplit: '34s / 112s',
      offsetSec: corridorOffsetSec,
      upstreamQueue: metrics.totalQueueLength,
    },
    {
      id: 'NODE-75',
      name: '5th Ave & Pine St (Node 75)',
      distanceMeters: 520,
      currentPhase: 'Phase 3 (Cross Traffic)',
      occupancyPct: 54,
      greenSplit: '32s / 112s',
      offsetSec: corridorOffsetSec * 2,
      upstreamQueue: 6,
    },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto text-slate-200 select-none">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider">
            <Network className="w-4 h-4" />
            Arterial Progression & Corridor Coordination
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1 font-sans">
            Three-Junction Arterial Network Coordination
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Platoon progression and green-wave synchronization along 5th Avenue between Node 73, Node 74 (Oak St), and Node 75.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Green Wave Offset:</span>
          <select
            value={corridorOffsetSec}
            onChange={(e) => setCorridorOffsetSec(parseInt(e.target.value))}
            className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-cyan-300 font-mono"
          >
            <option value={10}>10s Offset</option>
            <option value={14}>14s Offset (Optimal 45 km/h)</option>
            <option value={18}>18s Offset</option>
          </select>
        </div>
      </div>

      {/* Network Coordination Model Bounds Disclosure */}
      <div className="p-3.5 bg-slate-900/60 border border-slate-800 rounded-xl flex items-start gap-3 text-xs text-slate-400">
        <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <strong className="text-slate-200">Demonstration Scope & Protocol Disclosure:</strong>
          <p className="mt-0.5">
            Node 74 (Oak Street) is running the active microscopic simulation engine. Nodes 73 and 75 represent coupled link boundary models. Full multi-agent SUMO network synchronization across all 3 nodes will execute in the Stage 2 backend.
          </p>
        </div>
      </div>

      {/* Three Junction Diagram */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {nodes.map((n, idx) => (
          <div
            key={n.id}
            className={`p-5 rounded-xl border relative flex flex-col justify-between ${
              n.id === 'SC-INT-74'
                ? 'bg-cyan-950/30 border-cyan-500/50 shadow-xl ring-1 ring-cyan-500/30'
                : 'bg-slate-950/80 border-slate-800'
            }`}
          >
            <div>
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <span className="text-xs font-semibold text-slate-100">{n.name}</span>
                <span
                  className={`text-[9px] font-mono px-2 py-0.5 rounded ${
                    n.id === 'SC-INT-74'
                      ? 'bg-cyan-500 text-slate-950 font-bold'
                      : 'bg-slate-900 text-slate-400 border border-slate-800'
                  }`}
                >
                  {n.id === 'SC-INT-74' ? 'ACTIVE SIM' : 'COUPLED'}
                </span>
              </div>

              <div className="space-y-2 pt-3 text-xs">
                <div className="flex justify-between text-slate-400">
                  <span>Current Phase:</span>
                  <span className="font-mono text-emerald-400">{n.currentPhase}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Green Wave Offset:</span>
                  <span className="font-mono text-cyan-300">+{n.offsetSec}s</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Green Split:</span>
                  <span className="font-mono text-slate-300">{n.greenSplit}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Link Occupancy:</span>
                  <span className="font-mono text-cyan-400 font-bold">{n.occupancyPct}%</span>
                </div>
              </div>
            </div>

            {/* Inter-node distance marker */}
            {idx < 2 && (
              <div className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-slate-900 border border-cyan-500/40 items-center justify-center text-cyan-400">
                <ArrowRight className="w-3.5 h-3.5" />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
