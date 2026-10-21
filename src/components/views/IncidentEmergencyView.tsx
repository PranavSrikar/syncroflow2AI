/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import {
  Siren,
  Flame,
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Truck,
  RotateCcw,
  Info,
} from 'lucide-react';
import { Direction, SimulationMetrics, IntersectionSignalState } from '../../types/traffic.ts';

interface IncidentEmergencyViewProps {
  metrics: SimulationMetrics;
  signals: IntersectionSignalState;
  onInjectAmbulance: (dir: Direction) => void;
  onInjectFireEngine: (dir: Direction) => void;
}

export const IncidentEmergencyView: React.FC<IncidentEmergencyViewProps> = ({
  metrics,
  signals,
  onInjectAmbulance,
  onInjectFireEngine,
}) => {
  const [selectedDir, setSelectedDir] = useState<Direction>('north');
  const [simulatedDispatchStatus, setSimulatedDispatchStatus] = useState<string | null>(null);

  const handleSimulateTowTruckDispatch = () => {
    setSimulatedDispatchStatus('Simulated municipal tow truck unit #T-42 dispatched to incident location. Clearance ETA ~180s.');
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto text-slate-200 select-none">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-rose-400 font-mono text-xs uppercase tracking-wider">
            <Siren className="w-4 h-4" />
            Incident Verification & Emergency Priority Workflow
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1 font-sans">
            Emergency Preemption & Incident Verification Hub
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Authenticated Level-1 emergency vehicle preemption corridors, false-positive incident suppression, and clearance safety interlocks.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {signals.isPreemptActive ? (
            <span className="px-3 py-1 bg-rose-500/20 border border-rose-500/50 rounded-xl text-rose-300 font-mono text-xs font-semibold flex items-center gap-2">
              <Siren className="w-3.5 h-3.5 animate-bounce" />
              <span>PREEMPTION ACTIVE</span>
            </span>
          ) : (
            <span className="px-3 py-1 bg-slate-900 border border-slate-700 rounded-xl text-slate-400 font-mono text-xs">
              STANDBY (READY)
            </span>
          )}
        </div>
      </div>

      {/* Incident Verification Rules Card */}
      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-start gap-3 text-xs text-slate-400">
        <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <strong className="text-slate-200">Incident Classification & False-Positive Suppression:</strong>
          <p>
            1. Vehicles stopped before the stop line during RED or YELLOW are classified as <em>normal signal queues</em>, never broken down.<br />
            2. Public transit buses stopped at designated curbside bays are verified as <em>scheduled passenger dwells</em> (15s max).<br />
            3. A vehicle motionless for &gt; 35s in a moving through-lane during GREEN triggers an automated incident alert and supervisor verification.
          </p>
        </div>
      </div>

      {/* Emergency Corridor Injection Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-4">
          <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Siren className="w-4 h-4 text-rose-500" />
            <span>Authenticated Emergency Preemption Trigger</span>
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Inbound Approach Corridor:</label>
              <div className="grid grid-cols-4 gap-2">
                {(['north', 'south', 'east', 'west'] as Direction[]).map((d) => (
                  <button
                    key={d}
                    onClick={() => setSelectedDir(d)}
                    className={`py-1.5 rounded-lg border font-mono uppercase font-bold text-center transition-colors ${
                      selectedDir === d
                        ? 'bg-rose-600 text-white border-rose-500'
                        : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={() => onInjectAmbulance(selectedDir)}
                className="flex-1 py-2.5 bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-rose-600/20 transition-colors"
              >
                <Siren className="w-4 h-4" />
                <span>Inject Ambulance</span>
              </button>

              <button
                onClick={() => onInjectFireEngine(selectedDir)}
                className="flex-1 py-2.5 bg-red-700 hover:bg-red-600 text-white font-medium text-xs rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-red-700/20 transition-colors"
              >
                <Flame className="w-4 h-4" />
                <span>Inject Fire Engine</span>
              </button>
            </div>
          </div>
        </div>

        {/* Incident Response & Dispatch Simulator */}
        <div className="p-5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-4">
          <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Truck className="w-4 h-4 text-cyan-400" />
            <span>Simulated Municipal Incident Response</span>
          </h3>

          <p className="text-xs text-slate-400 leading-relaxed">
            Dispatch simulated incident response crews to clear stalled vehicles, tow obstructions, or establish temporary physical lane closures.
          </p>

          <div className="pt-2">
            <button
              onClick={handleSimulateTowTruckDispatch}
              className="w-full py-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-medium rounded-xl flex items-center justify-center gap-2 transition-colors"
            >
              <Truck className="w-4 h-4 text-cyan-400" />
              <span>Simulate Municipal Tow Truck Dispatch</span>
            </button>
          </div>

          {simulatedDispatchStatus && (
            <div className="p-2.5 bg-slate-900/90 border border-cyan-500/40 rounded-lg text-xs font-mono text-cyan-300">
              {simulatedDispatchStatus}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
