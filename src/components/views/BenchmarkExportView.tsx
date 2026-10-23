/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Download, FileText, CheckCircle2, Copy } from 'lucide-react';
import { SimulationMetrics, TrafficScenario } from '../../types/traffic.ts';

interface BenchmarkExportViewProps {
  metrics: SimulationMetrics;
  scenario: TrafficScenario;
  seed: number;
  weather?: string;
  controller?: string;
}

export const BenchmarkExportView: React.FC<BenchmarkExportViewProps> = ({
  metrics,
  scenario,
  seed, weather, controller,
}) => {
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState('');

  const reportData = {
    metadata: {
      platform: 'SynchroFlow AI Scientific Research Platform',
      version: 'Frontend functionality repair',
      source: 'synthetic_browser_engine', controller, qualifiedMAPPO: false,
      generatedTimestamp: new Date().toISOString(),
      reproducibleSeed: seed,
    },
    scenario: {
      id: scenario.id,
      numericId: scenario.numericId,
      name: scenario.name,
      category: scenario.category,
      arrivalRates: scenario.arrivalRates,
      composition: scenario.composition,
      weather: weather ?? scenario.weather,
    },
    measuredMetrics: {
      totalVehiclesSpawned: metrics.totalVehiclesSpawned,
      totalVehiclesPassed: metrics.totalVehiclesPassed,
      totalCompletedTrips: metrics.totalCompletedTrips,
      averageDelaySeconds: metrics.avgWaitTime,
      p95DelaySeconds: metrics.p95WaitTime,
      maxWaitTimeSeconds: metrics.maxWaitTime,
      peakQueueObservedVehicles: metrics.maxQueueObserved,
      measuredThroughputVehPerHour: metrics.throughputPerHour,
      emergencyClearanceTrips: metrics.emergencyTripCount,
      emergencyAverageTravelTimeSec: metrics.emergencyAvgTravelTime,
      safetyInterlocksPrevented: metrics.safetyViolationAttemptsPrevented,
    },
    stage2Requirements: {
      sumoTraCIBackend: 'Available separately in live SUMO workspace; this export is synthetic',
      cvxpyMpcQP: 'This browser model does not run the backend MPC',
      pytorchMappoCheckpoint: 'No qualified operational MAPPO policy',
    },
  };

  const jsonStr = JSON.stringify(reportData, null, 2);

  const handleCopy = async () => {
    try { await navigator.clipboard.writeText(jsonStr); setCopied(true); setError(''); setTimeout(() => setCopied(false), 2000); }
    catch { setCopied(false); setError('Clipboard permission denied. Use Download Benchmark JSON instead.'); }
  };

  const handleDownload = () => {
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `synchroflow_experiment_run_${scenario.id}_seed${seed}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto text-slate-200 select-none">
      {error && <p role="alert">{error}</p>}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider">
            <FileText className="w-4 h-4" />
            Scientific Reproducibility & Benchmark Export
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1 font-sans">
            Experiment Run Data Export
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Export verified empirical metrics, random seed, boundary scenario arrival parameters, and interlock logs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="px-3.5 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-medium rounded-xl flex items-center gap-1.5 transition-colors"
          >
            {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied to Clipboard' : 'Copy JSON'}</span>
          </button>

          <button
            onClick={handleDownload}
            className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs rounded-xl shadow-lg shadow-cyan-500/20 transition-all flex items-center gap-2"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Benchmark JSON</span>
          </button>
        </div>
      </div>

      <pre className="p-4 bg-slate-950/90 border border-slate-800 rounded-xl text-xs font-mono text-cyan-300 overflow-x-auto max-h-[500px]">
        {jsonStr}
      </pre>
    </div>
  );
};
