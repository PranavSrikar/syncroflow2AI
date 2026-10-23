import React, { useEffect, useState } from 'react';
import { useLiveTraffic, backendApi } from '../../services/liveTraffic';
import { TrafficInputsPanel } from './TrafficInputsPanel';
import { HybridTelemetryPanel, JunctionState } from './HybridTelemetryPanel';
import { LiveQueueChart } from './LiveQueueChart';

export type Snapshot = {
  connected: boolean; running: boolean; controller: string; error: string | null;
  scenario: string;
  seed?: number; junctions?: Record<string, JunctionState>; hybridPipeline?: string[];
  metrics?: { arrivedVehicles: number; queueVehicleSeconds: number; throughputVehiclesPerHour?: number | null; rewards?: number[] };
  controllerDiagnostics: unknown;
  mappoStatus?: { torchAvailable: boolean; operationalPolicyEnabled: boolean; reason: string; status?: string; inferenceCalls?: number; lastRecommendations?: number[] | null; smokeTrainingReport: { trainedDecisionSteps: number; status: string } | null };
  emergencyPriority?: {
    activeVehicleId: string | null;
    requests: { vehicleId: string; approach: string; priority: number; state: string; etaSec?: number }[];
    events: { simTime: number; vehicleId: string | null; event: string }[];
  };
  safetySupervisor: { status: string; reason: string };
  telemetry: null | {
    simTime: number;
    approaches: Record<string, { vehicles: number; queued: number; meanSpeedMps: number; avgWaitTimeSec: number }>;
    trafficLights: Record<string, { phaseIndex: number; signalState: string; nextSwitch: number }>;
    pedestrianSignals: { signalIndex: number; outgoingLane: string; state: string; occupants: string[]; waitingPersons: string[]; clearanceRequirementSec: number | null }[];
    pedestrians: Record<string, { roadId: string; waitingTimeSec: number }>;
    downstream: Record<string, { occupancyPercent: number; spillbackIndicator: boolean }>;
    stateEstimates: Record<string, { arrivalRatePerSec: number | null; observedDischargePerSec: number | null; rateWindowSec: number }>;
    permissionAnalysis: Record<string, { compatibleUnderSumoRules: boolean; incompatiblePermissions: unknown[]; yieldingInteractions: unknown[] }>;
  };
};
const api = backendApi + '/sumo';

export function SumoLiveView({ scope = 'dashboard' }: { scope?: string }) {
  const { state, online, error: connectionError, refresh } = useLiveTraffic();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [scenario, setScenario] = useState('vehicle');
  const [controller, setController] = useState('hybrid');
  const [seed, setSeed] = useState(23423);
  const [emergencyJunction, setEmergencyJunction] = useState('A0');
  const show = (...views: string[]) => scope === 'dashboard' || views.includes(scope);
  useEffect(() => {
    if (state?.connected) {
      setScenario(state.scenario); setController(state.controller); setSeed(state.seed ?? 23423);
    }
  }, [state?.connected, state?.scenario, state?.controller, state?.seed]);
  const command = async (action: string) => {
    setBusy(true);
    try {
      const response = await fetch(api + '/' + action + (action === 'start' ? '?scenario=' + scenario + '&controller=' + controller + '&seed=' + seed : ''), { method: 'POST', signal: AbortSignal.timeout(10000) });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || 'Command failed');
      await refresh(); setError('');
    } catch (err) { setError(String(err)); } finally { setBusy(false); }
  };
  const injectEmergency = async (approach: string) => {
    setBusy(true);
    try {
      const response = await fetch(api + '/emergencies/inject', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approach, priority: 3, junctionId: state?.scenario === 'corridor' ? emergencyJunction : undefined }), signal: AbortSignal.timeout(10000),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || 'Emergency request failed');
      await refresh(); setError('');
    } catch (err) { setError(String(err)); } finally { setBusy(false); }
  };
  return <section className="flex-1 overflow-auto p-6 space-y-5">
    <h1 className="text-2xl font-semibold">SUMO simulation telemetry</h1>
    <p className="text-cyan-300">Live workspace: {scope}</p>
    <p className="text-slate-400">Source: SUMO / TraCI simulated measurements. Optional camera observations and historical forecasts appear below; learned operational policy remains disabled.</p>
    {show('perception', 'prediction') && <TrafficInputsPanel />}
    {scope === 'pedestrian' && <p>Choose the pedestrian network to observe protected WALK and clearance. This backend has no manual pedestrian-call endpoint; people originate in the scenario.</p>}
    {scope === 'network' && <p>Choose the two-junction corridor to view A0/B0 coordination. No live three-node offset editor is implemented.</p>}
    <label>Network: <select aria-label="SUMO network" className="bg-slate-800 p-2" value={scenario} disabled={state?.connected || busy} onChange={event => setScenario(event.target.value)}><option value="vehicle">Original vehicle junction</option><option value="pedestrian">Experimental pedestrian junction</option><option value="corridor">Two-junction research corridor</option><option value="unequal">Demo: unequal north demand</option><option value="spillback">Demo: blocked south exit</option></select></label>
    <label className="ml-4">Controller: <select aria-label="SUMO controller" className="bg-slate-800 p-2" value={controller} disabled={state?.connected || busy} onChange={event => setController(event.target.value)}><option value="sumo_fixed_time">SUMO fixed-time baseline</option><option value="max_pressure">Max-Pressure with protected pedestrian service</option><option value="mpc">Constrained MPC with protected pedestrian service</option><option value="hybrid">Hybrid MPC / Max-Pressure fallback (MAPPO disabled unless qualified)</option></select></label>
    <label>Simulation seed: <input aria-label="SUMO seed" type="number" min="0" max="2147483647" className="bg-slate-800 p-2" value={seed} disabled={state?.connected || busy} onChange={e => setSeed(Number(e.target.value))} /></label>
    <div className="flex gap-3">{['start', 'pause', 'step', 'stop'].map(action =>
      <button key={action} disabled={busy || !online || (action === 'start' && !!state?.connected && !!state.running) || (action === 'pause' && !state?.running) || (action === 'step' && (!state?.connected || !!state.running)) || (action === 'stop' && !state?.connected)} onClick={() => command(action)} className="rounded bg-cyan-900 px-4 py-2 disabled:opacity-40">{action}</button>)}</div>
    <p>Stream: {online ? 'connected' : 'disconnected; data may be stale'} | Simulation: {!online ? 'unknown (backend unavailable)' : state?.connected ? state.running ? 'running' : 'paused' : 'stopped'} | Time: {state?.telemetry?.simTime ?? 'unavailable'} s</p>
    <p>Controller: {state?.controller ?? 'unavailable'} | Independent safety supervisor: {online ? state?.safetySupervisor.status ?? 'unavailable' : 'unavailable (stale)'}</p>
    <p className="text-amber-300">{state?.safetySupervisor.reason}</p>
    {show('network','analytics','health_security') && <>
    <LiveQueueChart />
    <HybridTelemetryPanel junctions={state?.junctions ?? {}} metrics={state?.metrics} connected={state?.connected ?? false} pipeline={state?.hybridPipeline} seed={state?.seed} />
    </>}
    {state?.scenario === 'corridor' && <p>Approach table below: primary junction A0. Both junctions are shown above. The supplied corridor has no pedestrian crossings; pedestrian protection is verified on the separate pedestrian scenario.</p>}
    {show('analytics','health_security','scenarios') && <>
    {state?.controllerDiagnostics != null && <details open className="bg-slate-900 p-3 rounded"><summary>Controller diagnostics and MPC queue projections</summary><pre className="text-xs overflow-auto max-h-64 mt-3">{JSON.stringify(state.controllerDiagnostics, null, 2)}</pre></details>}
    </>}
    {(error || connectionError || state?.error) && <p role="alert" className="text-red-400">{error || connectionError || state?.error}</p>}
    {show('analytics','network','scenarios') && <>
    <table className="w-full text-left"><thead><tr>{['Approach', 'Vehicles', 'Queue (halted)', 'Speed m/s', 'Current wait s'].map(x => <th key={x} className="p-3">{x}</th>)}</tr></thead>
      <tbody>{Object.entries(state?.telemetry?.approaches ?? {}).map(([direction, row]) => <tr key={direction} className="border-t border-slate-800"><td className="p-3">{direction}</td><td>{row.vehicles}</td><td>{row.queued}</td><td>{row.meanSpeedMps.toFixed(2)}</td><td>{row.avgWaitTimeSec.toFixed(2)}</td></tr>)}</tbody></table>
    {Object.entries(state?.telemetry?.trafficLights ?? {}).map(([id, signal]) => <div key={id} className="p-4 bg-slate-900 rounded">Junction {id}: phase {signal.phaseIndex} | Remaining {Math.max(0, signal.nextSwitch - (state?.telemetry?.simTime ?? 0)).toFixed(1)} s <p className="font-mono mt-2">{signal.signalState}</p><p className="text-slate-400">G: priority green, g: yielding green, y: yellow, r: red (SUMO link order)</p></div>)}
    {Object.entries(state?.telemetry?.permissionAnalysis ?? {}).map(([id, analysis]) => <p key={id}>Permission monitor {id}: {analysis.incompatiblePermissions.length} incompatible pairs; {analysis.yieldingInteractions.length} yielding interactions. Permission analysis complements the active controller supervisor; neither establishes real-road certification.</p>)}
    <h2 className="text-lg">Downstream observations and estimated rates</h2>
    {Object.entries(state?.telemetry?.downstream ?? {}).map(([direction, row]) => <p key={direction}>{direction}: occupancy {row.occupancyPercent.toFixed(1)}%; spillback heuristic {row.spillbackIndicator ? 'triggered' : 'not triggered'}; arrivals {state?.telemetry?.stateEstimates[direction]?.arrivalRatePerSec?.toFixed(3) ?? 'unavailable'} vehicles/s, observed discharge {state?.telemetry?.stateEstimates[direction]?.observedDischargePerSec?.toFixed(3) ?? 'unavailable'} vehicles/s.</p>)}
    <p className="text-slate-400">Spillback indicator: edge occupancy at least 80%. Rates use up to 60 seconds of unique vehicle identities; they are estimates, not forecasts.</p>
    </>}
    {show('pedestrian','health_security') && <>
    <h2 className="text-lg">Pedestrian telemetry</h2>
    <p>Observed pedestrians: {state?.telemetry ? Object.keys(state.telemetry.pedestrians).length : 'unavailable'}</p>
    {(state?.telemetry?.pedestrianSignals ?? []).map(crossing => <p key={crossing.signalIndex}>Crossing {crossing.outgoingLane}, link {crossing.signalIndex}: {crossing.state} | Occupied: {crossing.occupants?.length ?? 'unavailable'}, waiting: {crossing.waitingPersons?.length ?? 'unavailable'}, timed clearance: {crossing.clearanceRequirementSec ?? 'unavailable'} s</p>)}
    </>}
    {show('incidents','health_security') && <>
    <h2 className="text-lg">SUMO emergency priority</h2>
    {state?.scenario === 'corridor' && <label>Emergency junction: <select aria-label="Emergency junction" value={emergencyJunction} onChange={e => setEmergencyJunction(e.target.value)} className="bg-slate-800 p-2"><option>A0</option><option>B0</option></select></label>}
    <div className="flex gap-2">{['north', 'south', 'east', 'west'].map(approach => <button key={approach} className="rounded bg-rose-900 p-2 disabled:opacity-40" disabled={busy || !online || !state?.connected || state.controller === 'sumo_fixed_time'} onClick={() => injectEmergency(approach)}>Inject emergency {approach}</button>)}</div>
    <p>Priority vehicle: {state?.emergencyPriority?.activeVehicleId ?? 'none'}. Requests require observed SUMO emergency-class vehicles. Pending injections activate after departure.</p>
    {(state?.emergencyPriority?.requests ?? []).map(request => <p key={request.vehicleId}>{request.vehicleId} | {request.approach} | priority {request.priority} | {request.state} | ETA {request.etaSec?.toFixed(1) ?? 'unavailable'} s</p>)}
    <details><summary>Emergency audit events</summary>{(state?.emergencyPriority?.events ?? []).slice(-20).map((event, index) => <p key={index}>{event.simTime}s: {event.vehicleId ?? 'controller'} — {event.event}</p>)}</details>
    </>}
    {show('network','analytics','health_security') && <>
    <h2 className="text-lg">MAPPO research status</h2>
    <p>PyTorch: {state?.mappoStatus?.torchAvailable ? 'available' : 'unavailable'}. Operational learned policy: {state?.mappoStatus?.operationalPolicyEnabled ? 'enabled' : 'disabled'}.</p>
    <p>{state?.mappoStatus?.reason ?? 'Status unavailable'}</p>
    <p>Inference status: {state?.mappoStatus?.status ?? 'not selected'}; successful runtime inference calls: {state?.mappoStatus?.inferenceCalls ?? 0}; recommendations: {state?.mappoStatus?.lastRecommendations?.join(', ') ?? 'none'}. Training/inference readiness does not establish a useful trained policy.</p>
    {state?.mappoStatus?.smokeTrainingReport && <p>Smoke training: {state.mappoStatus.smokeTrainingReport.trainedDecisionSteps} decision steps; {state.mappoStatus.smokeTrainingReport.status}.</p>}
    </>}
    <p className="text-slate-400">Adaptive modes use a supervised cyclic program with protected pedestrian service. Emergency priority preserves required service and clearance stages. MPC uses a 60-second queue model, optional historical arrival forecasts, and Max-Pressure fallback. Phase5 policies failed qualification; no general performance superiority or road certification is established.</p>
  </section>;
}
