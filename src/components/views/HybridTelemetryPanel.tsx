import React from 'react';
import type { Snapshot } from './SumoLiveView';

export type JunctionState = {
  telemetry: NonNullable<Snapshot['telemetry']>;
  serviceAge?: Snapshot['serviceAge'];
  safetySupervisor: { status: string; acceptedActions?: number; rejectedActions?: number; lastDecision?: unknown; decisions?: unknown[] };
  controllerDiagnostics: { policy?: string; phasePressurePcu?: Record<string, number>; movementPressure?: unknown[]; fallback?: string | null; recommendedRemainingSec?: number; coordinationHint?: number | null; arrivalForecastSource?: string } | null;
  forecasts: { available: boolean; fallback: string | null };
  emergencyPriority: { activeVehicleId: string | null };
};
export function HybridTelemetryPanel({ junctions, metrics, connected, pipeline, seed }: {
  junctions: Record<string, JunctionState>; metrics?: { arrivedVehicles: number; queueVehicleSeconds: number; throughputVehiclesPerHour?: number | null; rewards?: number[] };
  connected: boolean; pipeline?: string[]; seed?: number;
}) {
  return <div className="space-y-3">
    <h2 className="text-lg">Hybrid control pipeline</h2>
    <p className="text-slate-400">{pipeline?.join(' → ') ?? 'Awaiting backend state'}</p>
    <p>SUMO seed: {seed ?? 'unavailable'}. Measurements: {connected ? 'current' : 'last run; simulation stopped'}.</p>
    {metrics && <p>Arrived vehicles: {metrics.arrivedVehicles}; measured queue integral: {metrics.queueVehicleSeconds.toFixed(1)} vehicle-seconds; throughput: {metrics.throughputVehiclesPerHour?.toFixed(1) ?? 'unavailable'} vehicles/hour. {metrics.rewards && `Research rewards: ${metrics.rewards.map(x => x.toFixed(2)).join(', ')}.`}</p>}
    <p className="text-slate-400">Metrics describe this simulation run. They do not establish improvement over another controller.</p>
    {Object.entries(junctions).map(([id, junction]) => <article key={id} className="bg-slate-900 rounded p-4 space-y-2" aria-label={'Junction telemetry ' + id}>
      <h3 className="text-lg">Junction {id} control state</h3>
      <p>Policy: {junction.controllerDiagnostics?.policy ?? 'fixed time / no adaptive decision'}. Safety: {junction.safetySupervisor.status}; accepted actions {junction.safetySupervisor.acceptedActions ?? 0}, rejected {junction.safetySupervisor.rejectedActions ?? 0}.</p>
      <p>Emergency: {junction.emergencyPriority.activeVehicleId ?? 'none'}. Forecast: {junction.forecasts.available ? 'available' : junction.forecasts.fallback}. MPC arrival source: {junction.controllerDiagnostics?.arrivalForecastSource ?? 'no solve yet'}.</p>
      <p>Coordination preference to MPC: {junction.controllerDiagnostics?.coordinationHint ?? 'none (policy unavailable or unqualified)'}. MPC remaining: {junction.controllerDiagnostics?.recommendedRemainingSec ?? 'no solve yet'} s. Fallback: {junction.controllerDiagnostics?.fallback ?? 'none'}.</p>
      {Object.entries(junction.telemetry.trafficLights).map(([signal, light]) => <p key={signal}>Signal {signal}: phase {light.phaseIndex}, <span className="font-mono">{light.signalState}</span></p>)}
      <table className="w-full text-left"><thead><tr><th>Approach</th><th>Vehicles</th><th>Queue</th><th>Current wait s</th></tr></thead><tbody>{Object.entries(junction.telemetry.approaches).map(([direction, row]) => <tr key={direction}><td>{direction}</td><td>{row.vehicles}</td><td>{row.queued}</td><td>{row.avgWaitTimeSec.toFixed(2)}</td></tr>)}</tbody></table>
      <p>Max-Pressure PCU scores: {Object.entries(junction.controllerDiagnostics?.phasePressurePcu ?? {}).map(([p, score]) => `${p}: ${score.toFixed(2)}`).join('; ') || 'no green-phase decision yet'}</p>
      <details><summary>Movement pressure and supervisor decisions for {id}</summary><pre className="text-xs overflow-auto max-h-64">{JSON.stringify({ movementPressure: junction.controllerDiagnostics?.movementPressure, decisions: junction.safetySupervisor.decisions?.slice(-10) }, null, 2)}</pre></details>
    </article>)}
  </div>;
}
