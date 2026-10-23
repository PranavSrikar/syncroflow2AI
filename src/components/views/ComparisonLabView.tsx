/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { ControllerType, TrafficScenario, SimulationMetrics } from '../../types/traffic.ts';
import { ALL_25_SCENARIOS } from '../../simulation/scenarios.ts';
import { TrafficSimulationEngine } from '../../simulation/engine.ts';
import {
  Scale,
  Play,
  RotateCcw,
  Download,
  AlertCircle,
  CheckCircle2,
  Sliders,
  BarChart2,
  Info,
} from 'lucide-react';

interface BenchmarkResult {
  controller: ControllerType;
  controllerName: string;
  scenarioName: string;
  seed: number;
  simDurationSec: number;
  measuredAvgDelay: number;
  measuredP95Delay: number;
  measuredThroughput: number;
  measuredMaxQueue: number;
  executionStatus: 'Measured (Local Browser Engine)' | 'Awaiting Stage 2 Backend';
}

export const ComparisonLabView: React.FC = () => {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>(ALL_25_SCENARIOS[0].id);
  const [selectedSeed, setSelectedSeed] = useState<number>(42);
  const [benchmarkDuration, setBenchmarkDuration] = useState<number>(60); // 60s fast benchmark
  const [isRunningBenchmark, setIsRunningBenchmark] = useState<boolean>(false);
  const [benchmarkProgress, setBenchmarkProgress] = useState<number>(0);
  const [results, setResults] = useState<BenchmarkResult[]>([]);

  // The 7 canonical controllers
  const CONTROLLERS: { id: ControllerType; name: string; isExecutableLocally: boolean; description: string }[] = [
    { id: 'fixed', name: 'Optimized Fixed-Time Pre-timed', isExecutableLocally: true, description: 'Pre-timed 112s NEMA dual-ring cycle with static green splits.' },
    { id: 'actuated', name: 'Semi-Actuated (Gap-Out)', isExecutableLocally: true, description: 'Sensor-actuated phase hold while dilemma zone loops detect vehicles.' },
    { id: 'queue_adaptive', name: 'Queue-Based Dynamic Adaptive', isExecutableLocally: true, description: 'Dynamic green allocation proportional to inbound queue count.' },
    { id: 'max_pressure', name: 'Max-Pressure-style browser heuristic', isExecutableLocally: true, description: 'Selects movement phases with maximum upstream minus downstream queue differential.' },
    { id: 'mpc_only', name: 'Browser MPC-style heuristic', isExecutableLocally: true, description: 'Receding-horizon trajectory candidate evaluation minimizing queue and delay cost.' },
    { id: 'mappo_assisted_mpc', name: 'Browser advisory heuristic (MAPPO label)', isExecutableLocally: true, description: 'Rule-based browser advisory; no trained neural checkpoint.' },
    { id: 'synchroflow_hybrid', name: 'SynchroFlow Full Hybrid System', isExecutableLocally: true, description: 'Browser hybrid heuristic and model interlocks; no physical V2I or trained MAPPO.' },
  ];

  const runBenchmark = async () => {
    setIsRunningBenchmark(true);
    setBenchmarkProgress(0);
    const newResults: BenchmarkResult[] = [];

    const scenario = ALL_25_SCENARIOS.find((s) => s.id === selectedScenarioId) || ALL_25_SCENARIOS[0];

    for (let i = 0; i < CONTROLLERS.length; i++) {
      const ctrl = CONTROLLERS[i];
      setBenchmarkProgress(Math.round(((i + 1) / CONTROLLERS.length) * 100));

      // Execute local deterministic simulation for the duration
      const testEngine = new TrafficSimulationEngine(scenario, selectedSeed);
      testEngine.setController(ctrl.id);

      const dt = 0.5;
      const totalSteps = Math.round(benchmarkDuration / dt);

      for (let s = 0; s < totalSteps; s++) {
        testEngine.step(dt);
      }

      const st = testEngine.getState();
      newResults.push({
        controller: ctrl.id,
        controllerName: ctrl.name,
        scenarioName: scenario.name,
        seed: selectedSeed,
        simDurationSec: benchmarkDuration,
        measuredAvgDelay: st.metrics.avgWaitTime,
        measuredP95Delay: st.metrics.p95WaitTime,
        measuredThroughput: st.metrics.throughputPerHour,
        measuredMaxQueue: st.metrics.maxQueueObserved,
        executionStatus: 'Measured (Local Browser Engine)',
      });

      // Yield briefly so UI updates progress
      await new Promise((resolve) => setTimeout(resolve, 30));
    }

    setResults(newResults);
    setIsRunningBenchmark(false);
  };

  const exportBenchmarkCSV = () => {
    if (results.length === 0) return;
    const headers = 'Controller,Scenario,Seed,DurationSec,MeasuredAvgDelaySec,MeasuredP95DelaySec,MeasuredThroughputVehHr,MeasuredMaxQueueVeh,ExecutionStatus\n';
    const rows = results
      .map(
        (r) =>
          `"${r.controllerName}","${r.scenarioName}",${r.seed},${r.simDurationSec},${r.measuredAvgDelay},${r.measuredP95Delay},${r.measuredThroughput},${r.measuredMaxQueue},"${r.executionStatus}"`
      )
      .join('\n');

    const blob = new Blob([headers + rows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `synchroflow_benchmark_seed${selectedSeed}_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto text-slate-200 select-none">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider">
            <Scale className="w-4 h-4" />
            Empirical Benchmark Runner & Controller Comparison
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1 font-sans">
            Controlled Scientific Benchmark Comparison
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Execute head-to-head simulations under identical pseudorandom seeds, arrival streams, and durations. Zero fabricated outcome metrics.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {results.length > 0 && (
            <button
              onClick={exportBenchmarkCSV}
              className="px-3.5 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-medium rounded-xl flex items-center gap-1.5 transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-cyan-400" />
              <span>Export CSV</span>
            </button>
          )}

          <button
            onClick={runBenchmark}
            disabled={isRunningBenchmark}
            className={`px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs rounded-xl shadow-lg shadow-cyan-500/20 transition-all flex items-center gap-2 ${
              isRunningBenchmark ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{isRunningBenchmark ? `Running Benchmark (${benchmarkProgress}%)` : 'Run Comparative Benchmark'}</span>
          </button>
        </div>
      </div>

      {results.length>0 && <section className="sf-benchmark-chart"><h2>Mean current wait by controller</h2><p className="sf-caption">Measured browser-engine outcomes; seconds; single run; no variability or statistical superiority established</p>{results.map(r=><div key={r.controller}><span>{r.controllerName}</span><i><b style={{width:`${Math.max(0,r.measuredAvgDelay)/Math.max(1,...results.map(x=>x.measuredAvgDelay))*100}%`}} /></i><strong>{r.measuredAvgDelay.toFixed(1)} s</strong></div>)}</section>}
      {/* Benchmark Experiment Configuration Parameters */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div>
          <label className="text-slate-400 font-medium block mb-1">Target Scenario</label>
          <select
            aria-label="Benchmark scenario"
            value={selectedScenarioId}
            onChange={(e) => setSelectedScenarioId(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200 font-sans focus:outline-none focus:border-cyan-500/50"
          >
            {ALL_25_SCENARIOS.map((sc) => (
              <option key={sc.id} value={sc.id}>
                {sc.name} ({sc.category})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-slate-400 font-medium block mb-1">Random Seed (PRNG Reproducibility)</label>
          <input
            aria-label="Benchmark seed"
            type="number"
            min="0"
            value={selectedSeed}
            onChange={(e) => { const seed = Number(e.target.value); if (Number.isInteger(seed) && seed >= 0) setSelectedSeed(seed); }}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-cyan-300 font-mono focus:outline-none focus:border-cyan-500/50"
          />
        </div>

        <div>
          <label className="text-slate-400 font-medium block mb-1">Simulated Duration per Controller</label>
          <select
            aria-label="Benchmark duration"
            value={benchmarkDuration}
            onChange={(e) => setBenchmarkDuration(parseInt(e.target.value))}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200 font-sans focus:outline-none focus:border-cyan-500/50"
          >
            <option value={60}>60 seconds (Fast Screen)</option>
            <option value={120}>120 seconds (Full 1-Cycle Benchmark)</option>
            <option value={240}>240 seconds (Multi-Cycle Equilibrium)</option>
          </select>
        </div>
      </div>

      {/* Scientific Transparency Disclaimer */}
      <div className="p-3.5 bg-slate-900/60 border border-slate-800 rounded-xl flex items-start gap-3 text-xs text-slate-400">
        <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <strong className="text-slate-200">Stage 1 Controller Execution Disclosure:</strong>
          <p className="mt-0.5">
            The results below are measured strictly from deterministic browser simulation execution. MAPPO-labelled rows use browser heuristics, not neural policy inference. Backend Phase5 policies were evaluated separately and failed qualification. These results cannot establish SUMO performance or learned-policy superiority.
          </p>
        </div>
      </div>

      {/* Benchmark Results Table */}
      <div className="bg-slate-950/90 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-cyan-400" />
            <span>Measured Comparative Results ({results.length} / 7 Controllers Evaluated)</span>
          </h3>
          {results.length > 0 && (
            <span className="text-[10px] text-emerald-400 font-mono bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-500/30">
              Deterministic Seed: {selectedSeed}
            </span>
          )}
        </div>

        {results.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-lg">
            No benchmark executed yet. Click &quot;Run Comparative Benchmark&quot; to execute all 7 controllers under identical traffic seeds.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-sans">
              <thead className="bg-slate-900/80 text-slate-400 font-mono text-[10px] uppercase border-b border-slate-800">
                <tr>
                  <th className="p-3">Controller Architecture</th>
                  <th className="p-3 text-center">Avg Delay</th>
                  <th className="p-3 text-center">P95 Delay</th>
                  <th className="p-3 text-center">Throughput Rate</th>
                  <th className="p-3 text-center">Peak Queue</th>
                  <th className="p-3 text-right">Execution Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px] tabular-nums">
                {results.map((r) => (
                  <tr key={r.controller} className="hover:bg-slate-900/40 transition-colors">
                    <td className="p-3 font-semibold text-slate-200 font-sans">
                      {r.controllerName}
                    </td>
                    <td className="p-3 text-center text-cyan-300 font-bold">
                      {r.measuredAvgDelay}s
                    </td>
                    <td className="p-3 text-center text-amber-300">
                      {r.measuredP95Delay}s
                    </td>
                    <td className="p-3 text-center text-emerald-400">
                      {r.measuredThroughput} veh/hr
                    </td>
                    <td className="p-3 text-center text-rose-300">
                      {r.measuredMaxQueue} veh
                    </td>
                    <td className="p-3 text-right text-slate-400 text-[10px]">
                      {r.executionStatus}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
