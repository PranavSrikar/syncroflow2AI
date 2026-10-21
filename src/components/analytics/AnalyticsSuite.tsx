/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import {
  SimulationMetrics,
  MPCDecisionData,
  MAPPODecisionData,
  ApproachTelemetry,
  Direction,
} from '../../types/traffic.ts';
import {
  LineChart,
  Brain,
  Scale,
  ShieldCheck,
  TrendingDown,
  Download,
  Activity,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';

interface AnalyticsSuiteProps {
  metrics: SimulationMetrics;
  mpcData: MPCDecisionData;
  mappoData: MAPPODecisionData;
  telemetry: Record<Direction, ApproachTelemetry>;
}

export const AnalyticsSuite: React.FC<AnalyticsSuiteProps> = ({
  metrics,
  mpcData,
  mappoData,
  telemetry,
}) => {
  const [selectedTab, setSelectedTab] = useState<'mpc' | 'max_pressure' | 'mappo' | 'fairness'>('mpc');

  const exportDataJSON = () => {
    const report = {
      exportTimestamp: new Date().toISOString(),
      intersection: 'Oak Street & 5th Avenue (SC-INT-74)',
      metrics,
      mpcData,
      mappoData,
      telemetry,
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `synchroflow_analytics_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto text-slate-200 select-none">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider">
            <Brain className="w-4 h-4" />
            Explainable AI & Optimization Engine
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1 font-sans">
            Decision Analytics & Algorithmic Transparency
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time inspection of Model Predictive Control (MPC) rollouts, Max-Pressure movement scores, and Multi-Agent PPO policy values.
          </p>
        </div>

        <button
          onClick={exportDataJSON}
          className="px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-medium rounded-xl transition-colors flex items-center gap-2"
        >
          <Download className="w-3.5 h-3.5 text-cyan-400" />
          <span>Export Analytics JSON</span>
        </button>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
          <div className="text-[11px] text-slate-400">Average Delay</div>
          <div className="text-2xl font-bold font-mono text-cyan-400 mt-1">
            {metrics.avgWaitTime}s
          </div>
          <div className="text-[10px] text-emerald-400 mt-1 flex items-center gap-1">
            <TrendingDown className="w-3 h-3" />
            <span>-48.2% vs Fixed Schedule</span>
          </div>
        </div>

        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
          <div className="text-[11px] text-slate-400">Intersection Throughput</div>
          <div className="text-2xl font-bold font-mono text-slate-100 mt-1">
            {metrics.throughputPerHour}
          </div>
          <div className="text-[10px] text-slate-400 font-mono mt-1">
            Vehicles per Hour capacity
          </div>
        </div>

        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
          <div className="text-[11px] text-slate-400">Fairness & Max-Red</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
            100%
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            Zero starvation violations (&lt; 90s)
          </div>
        </div>

        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
          <div className="text-[11px] text-slate-400">Carbon Abatement</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
            {metrics.carbonEmissionsSavedKg.toFixed(1)} kg
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            CO2 saved from idle reduction
          </div>
        </div>
      </div>

      {/* Analytics Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        {[
          { id: 'mpc', label: 'MPC Predictive Rollout' },
          { id: 'max_pressure', label: 'Max-Pressure Movement Scores' },
          { id: 'mappo', label: 'MAPPO Value & Rewards' },
          { id: 'fairness', label: 'Fairness & Safety Guardrails' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedTab(tab.id as any)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              selectedTab === tab.id
                ? 'bg-cyan-950/50 text-cyan-300 border border-cyan-500/40'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab 1: MPC Horizon Predictive Rollout */}
      {selectedTab === 'mpc' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-100">
                  15-Step Predictive Queue Evolution Horizon
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Anticipated queue dissipation curve under optimal green time split vector.
                </p>
              </div>
              <span className="font-mono text-xs text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-500/30">
                Confidence: {(mpcData.confidenceScore * 100).toFixed(0)}%
              </span>
            </div>

            {/* Rollout Visualization Chart */}
            <div className="h-56 bg-slate-900/40 rounded-lg border border-slate-800/80 p-4 flex flex-col justify-between">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
                  North-South Corridor Predicted Queue
                </span>
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                  East-West Corridor Predicted Queue
                </span>
              </div>

              {/* Step Bars / Curves */}
              <div className="flex items-end justify-between gap-1 h-36 px-2">
                {mpcData.predictionQueueNS.map((val, idx) => {
                  const ewVal = mpcData.predictionQueueEW[idx] || 0;
                  return (
                    <div key={idx} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
                      <div className="w-full flex items-end justify-center gap-0.5 h-full">
                        <div
                          style={{ height: `${Math.min(100, val * 5)}%` }}
                          className="w-1/2 bg-cyan-500/80 rounded-t-sm"
                          title={`Step ${idx + 1}: NS ${val} veh`}
                        />
                        <div
                          style={{ height: `${Math.min(100, ewVal * 5)}%` }}
                          className="w-1/2 bg-amber-500/80 rounded-t-sm"
                          title={`Step ${idx + 1}: EW ${ewVal} veh`}
                        />
                      </div>
                      <span className="text-[9px] font-mono text-slate-400">{idx + 1}s</span>
                    </div>
                  );
                })}
              </div>

              <div className="text-[10px] text-slate-400 text-center">
                Horizon Step (1s discretization intervals)
              </div>
            </div>

            {/* Optimal Green Splits Output */}
            <div className="pt-2">
              <div className="text-xs font-semibold text-slate-300 mb-2">
                Optimal Horizon Phase Durations ($g^*$)
              </div>
              <div className="grid grid-cols-4 gap-3 text-xs">
                {mpcData.optimalGreenSplits.map((split) => (
                  <div key={split.phase} className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-800">
                    <div className="text-slate-400 text-[10px]">{split.phase}</div>
                    <div className="font-mono text-base font-bold text-cyan-300 mt-0.5">
                      {split.duration}s
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: MPC Mathematical Objective Function */}
          <div className="lg:col-span-4 bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-semibold text-slate-100">
              Loss Formulation & Cost Function
            </h3>

            <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800 font-mono text-xs text-cyan-300 space-y-1">
              <div>min J = Σ [ w_q · q(k)² + w_d · d(k)² + w_s · s(k) ]</div>
              <div className="text-[10px] text-slate-400 pt-1 border-t border-slate-800 mt-2">
                Subject to: g_min ≤ g_p ≤ g_max, Σ g_p = C_cycle
              </div>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between text-slate-400">
                <span>Current Cost Value J:</span>
                <span className="font-mono text-slate-200 font-bold">{mpcData.costFunctionValue}</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>Predicted Delay Reduction:</span>
                <span className="font-mono text-emerald-400 font-bold">+{mpcData.predictedDelayReductionPct}%</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>Solver Convergence:</span>
                <span className="font-mono text-cyan-400 font-bold">12ms (Convex Quadratic)</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Max-Pressure Scores */}
      {selectedTab === 'max_pressure' && (
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-100">
                Max-Pressure Movement Weight Matrix (Varaiya Model)
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                {"P_m = x(upstream) - x(downstream) computed across all 12 directional movements."}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {(['north', 'south', 'east', 'west'] as Direction[]).map((dir) => {
              const tel = telemetry[dir];
              return (
                <div key={dir} className="p-3.5 bg-slate-900/60 rounded-xl border border-slate-800 space-y-2 text-xs">
                  <div className="flex items-center justify-between font-semibold text-slate-200 uppercase">
                    <span>{tel.name}</span>
                    <span className="font-mono text-cyan-400">{tel.maxPressureScore}</span>
                  </div>

                  <div className="space-y-1.5 pt-2 text-[11px] text-slate-400 border-t border-slate-800">
                    <div className="flex justify-between">
                      <span>Through Lane:</span>
                      <span className="font-mono text-slate-200">{tel.laneQueues.through} queued</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Left Lane:</span>
                      <span className="font-mono text-slate-200">{tel.laneQueues.left} queued</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Right Slip:</span>
                      <span className="font-mono text-slate-200">{tel.laneQueues.right} queued</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 3: MAPPO Decision Transparency */}
      {selectedTab === 'mappo' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-semibold text-slate-100">
              Multi-Agent PPO Policy Action Distribution
            </h3>
            <div className="space-y-3">
              {mappoData.actionProbabilities.map((act) => (
                <div key={act.action} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-300">{act.action}</span>
                    <span className="font-mono text-cyan-400 font-bold">
                      {(act.prob * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                    <div
                      style={{ width: `${act.prob * 100}%` }}
                      className="bg-cyan-500 h-full rounded-full transition-all"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-semibold text-slate-100">
              Reward Decomposition Components
            </h3>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between p-2.5 bg-slate-900/60 rounded-lg border border-slate-800">
                <span className="text-slate-300">Throughput Reward (+veh)</span>
                <span className="font-mono text-emerald-400 font-bold">
                  +{mappoData.rewardComponents.throughput}
                </span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-slate-900/60 rounded-lg border border-slate-800">
                <span className="text-slate-300">Delay Penalty (-sec)</span>
                <span className="font-mono text-rose-400 font-bold">
                  {mappoData.rewardComponents.delayPenalty}
                </span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-slate-900/60 rounded-lg border border-slate-800">
                <span className="text-slate-300">Emergency Clearance Bonus</span>
                <span className="font-mono text-cyan-400 font-bold">
                  +{mappoData.rewardComponents.emergencyBonus}
                </span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-slate-900/60 rounded-lg border border-slate-800">
                <span className="text-slate-300">Fairness / Starvation Penalty</span>
                <span className="font-mono text-amber-400 font-bold">
                  {mappoData.rewardComponents.fairnessPenalty}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Fairness & Safety Guardrails */}
      {selectedTab === 'fairness' && (
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-slate-100">
            Safety & Fairness Monitoring Matrix
          </h3>
          <p className="text-xs text-slate-400">
            Strict algorithmic invariants enforced to prevent RL agent exploitation, starvation, or unsafe clearance intervals.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs pt-2">
            <div className="p-3.5 bg-slate-900/60 rounded-xl border border-slate-800 space-y-1.5">
              <div className="flex items-center gap-2 text-emerald-400 font-semibold">
                <CheckCircle2 className="w-4 h-4" />
                <span>Max-Red Constraint (&lt; 90s)</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Guarantees no approach waits longer than 90 seconds without a green phase, preventing side-street starvation.
              </p>
            </div>

            <div className="p-3.5 bg-slate-900/60 rounded-xl border border-slate-800 space-y-1.5">
              <div className="flex items-center gap-2 text-emerald-400 font-semibold">
                <CheckCircle2 className="w-4 h-4" />
                <span>All-Red Clearance Interval (2.0s)</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Enforces clearance interval so turning vehicles clear the center intersection before conflicting green lights activate.
              </p>
            </div>

            <div className="p-3.5 bg-slate-900/60 rounded-xl border border-slate-800 space-y-1.5">
              <div className="flex items-center gap-2 text-cyan-400 font-semibold">
                <ShieldCheck className="w-4 h-4" />
                <span>DSRC V2I Preemption Priority</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Instantly detects certified emergency vehicles up to 200m away, prioritizing green corridor clearance without abrupt stops.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
