/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Users, CheckCircle2, ShieldCheck, Hand, AlertTriangle, Info } from 'lucide-react';
import { Direction, IntersectionSignalState } from '../../types/traffic.ts';

interface PedestrianCrossingViewProps {
  signals: IntersectionSignalState;
}

export const PedestrianCrossingView: React.FC<PedestrianCrossingViewProps> = ({ signals }) => {
  const [activeCallApproaches, setActiveCallApproaches] = useState<Record<Direction, boolean>>({
    north: false,
    south: false,
    east: false,
    west: false,
  });

  const handlePressCallButton = (dir: Direction) => {
    setActiveCallApproaches((prev) => ({ ...prev, [dir]: true }));
    signals.pedestrianSignals[dir].hasCallRequest = true;
    signals.pedestrianSignals[dir].waitingCount += 1;
  };

  const crosswalks: Direction[] = ['north', 'south', 'east', 'west'];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto text-slate-200 select-none">
      <div className="pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider">
          <Users className="w-4 h-4" />
          Pedestrian Crosswalk Safety & Actuation
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1 font-sans">
          Pedestrian Safety Interlocks & Crosswalk Demands
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Stateful pedestrian entities with interactive call buttons, WALK intervals, Flashing Don&apos;t Walk clearance, and vehicular holding constraints.
        </p>
      </div>

      {/* Safety Interlock Note */}
      <div className="p-3.5 bg-slate-900/60 border border-slate-800 rounded-xl flex items-start gap-3 text-xs text-slate-400">
        <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <strong className="text-slate-200">Pedestrian Clearance Hard Interlock:</strong>
          <p className="mt-0.5">
            When a pedestrian walk phase is active, conflicting left-turn and right-turn vehicular green movements are either held red or given a flashing amber cautionary yield arrow.
          </p>
        </div>
      </div>

      {/* 4 Crosswalk Arms Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {crosswalks.map((dir) => {
          const ped = signals.pedestrianSignals[dir];
          const isWalk = ped.state === 'WALK';
          const isFlashing = ped.state === 'FLASHING_DONT_WALK';

          return (
            <div key={dir} className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase text-slate-200">{dir} Crosswalk</span>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                    isWalk
                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/40'
                      : isFlashing
                      ? 'bg-amber-950 text-amber-400 border border-amber-500/40'
                      : 'bg-rose-950 text-rose-400 border border-rose-500/40'
                  }`}
                >
                  {ped.state}
                </span>
              </div>

              <div className="p-3 bg-slate-900/70 rounded-lg border border-slate-800 space-y-2 text-xs">
                <div className="flex justify-between text-slate-400">
                  <span>Waiting Pedestrians:</span>
                  <span className="font-mono text-cyan-300 font-bold">{ped.waitingCount} persons</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Call Request Status:</span>
                  <span className="font-mono text-emerald-400">
                    {ped.hasCallRequest || activeCallApproaches[dir] ? 'REGISTERED (ACTUATED)' : 'IDLE'}
                  </span>
                </div>
              </div>

              <button
                onClick={() => handlePressCallButton(dir)}
                className="w-full py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-medium rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                <Hand className="w-3.5 h-3.5 text-cyan-400" />
                <span>Press Pedestrian Pushbutton ({dir.toUpperCase()})</span>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
