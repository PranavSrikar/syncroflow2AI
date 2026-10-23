import React, { useState } from 'react';
import { useLiveTraffic } from '../../services/liveTraffic';
import { LiveNetworkMap, signalColor } from './LiveNetworkMap';
import { Badge, Metric, Panel } from './primitives';
import type { Snapshot } from '../views/SumoLiveView';
export function LiveCommandCenter({ scope }: { scope: string }) {
  const { state, online, error } = useLiveTraffic();
  const [selection, setSelection] = useState('auto');
  const junctions = Object.keys(state?.junctions ?? {});
  const availableJunctions = junctions.length ? junctions : Object.keys(state?.telemetry?.trafficLights ?? {});
  const selected = selection === 'auto' && availableJunctions.length === 1 ? availableJunctions[0] : selection !== 'network' && availableJunctions.includes(selection) ? selection : null;
  const local = selected ? state?.junctions?.[selected] : null;
  const raw = local?.telemetry ?? state?.telemetry ?? null;
  const available = online && !!raw && !!state?.connected;
  const allRows = local ? Object.values(raw?.approaches ?? {}) : junctions.length ? Object.values(state!.junctions!).flatMap(j=>Object.values(j.telemetry.approaches)) : Object.values(raw?.approaches ?? {});
  const count=allRows.reduce((n,r)=>n+r.vehicles,0), queue=allRows.reduce((n,r)=>n+r.queued,0);
  const wait=count ? allRows.reduce((n,r)=>n+r.vehicles*r.avgWaitTimeSec,0)/count : null;
  const diagnostics = (local?.controllerDiagnostics ?? (junctions.length ? state?.junctions?.[junctions[0]]?.controllerDiagnostics : state?.controllerDiagnostics)) as Record<string, any> | null;
  const supervisor = local?.safetySupervisor ?? state?.safetySupervisor;
  const serviceAge = local?.serviceAge ?? state?.serviceAge;
  const policy = diagnostics?.policy;
  const policyText = policy === 'constrained_mpc' ? 'Constrained MPC selected a feasible timing candidate.' : policy === 'max_pressure_fallback' ? 'Max-Pressure fallback is active; the MPC candidate was unavailable.' : policy === 'emergency_priority' ? 'Emergency priority is requesting supervised timing.' : policy === 'phase_expiry_pending' ? 'The approved phase is due to expire; its scheduled transition is retained.' : policy ? 'Pressure-based extension within the approved cyclic program.' : 'No adaptive decision trace yet. Start an adaptive controller to inspect decisions.';
  const lights=Object.entries(raw?.trafficLights ?? {});
  const emergency=state?.emergencyPriority?.activeVehicleId;
  return <div className="sf-command-experience">
    <div className="sf-kpi-grid" aria-busy={!state && !error} aria-label="Live SUMO metrics">
      <Metric label="Approach vehicles" value={available ? count : '—'} unit="veh" hint={selected ? `Selected junction ${selected}` : 'All monitored junction approaches'} />
      <Metric label="Vehicles in queue" value={available ? queue : '—'} unit="veh" hint="Halted approach vehicles" />
      <Metric label="Current mean wait" value={available && wait !== null ? wait.toFixed(1) : '—'} unit="s" hint="Vehicle-weighted; current approaches" />
      <Metric label="Run throughput" value={available && state?.metrics?.throughputVehiclesPerHour != null ? state.metrics.throughputVehiclesPerHour.toFixed(0) : '—'} unit="veh/h" hint="Completed arrivals / elapsed run time" />
    </div>
    {scope !== 'analytics' && <div className="sf-command-grid">
      <Panel title="Live digital twin" eyebrow="SPATIAL OBSERVATIONS" className="sf-twin-panel">
        <div className="sf-map-toolbar"><Badge>SUMO / TraCI measurements</Badge><label>View <select aria-label="Digital twin junction" value={selected ?? 'network'} onChange={e=>setSelection(e.target.value)}><option value="network">Entire network</option>{(junctions.length ? junctions : Object.keys(raw?.trafficLights ?? {})).map(id=><option key={id} value={id}>{id}</option>)}</select></label></div>
        <LiveNetworkMap raw={raw} online={online} junction={selected ?? (selection !== 'network' && lights.some(([id])=>id===selection) ? selection : 'network')} />
        <div className="sf-phase-strip">{lights.length ? lights.map(([id,signal])=><div key={id}><span className="sf-eyebrow">{id} · PHASE {signal.phaseIndex}</span><div className="sf-signal-dots">{[...signal.signalState].map((s,index)=><i key={index} style={{background:signalColor(s)}} title={`Link ${index}: ${s}`} />)}</div><span>{online ? `Scheduled switch in ${Math.max(0,signal.nextSwitch-raw!.simTime).toFixed(0)} s` : 'Timing stale'}</span></div>) : <p>Signals appear after Start. Green = priority, pale green = yielding, amber = clearance, red = stop.</p>}</div>
        <p className="sf-caption">Positions update at observed simulation steps. Signal countdown is the current SUMO schedule and may change under adaptive control.</p>
      </Panel>
      <div className="sf-insights">
        <Panel title="Why this signal?" eyebrow="CONTROLLER INTELLIGENCE">
          <div className="sf-inline-badges"><Badge>{state?.controller ?? 'Not selected'}</Badge><Badge tone={diagnostics?.fallback ? 'warn' : 'neutral'}>{policy === 'constrained_mpc' ? 'MPC action' : diagnostics?.fallback ? 'Fallback' : 'Observed inputs'}</Badge></div>
          {!online && <p className="sf-warning">Connection lost. The following is the last received observation.</p>}
          <p className="sf-decision-summary">{policyText}</p>
          {junctions.length && !selected ? <p className="sf-caption">Decision summary: primary junction {junctions[0]}. Select a junction to inspect its inputs.</p> : null}
          <dl className="sf-facts"><div><dt>Forecast influence</dt><dd>{diagnostics?.arrivalForecastSource === 'seasonal_shrinkage_baseline' ? 'Historical arrival estimate' : diagnostics?.arrivalForecastSource === 'recent_observations' ? 'Observed arrival rates' : 'Not reported'}</dd></div><div><dt>Pedestrian / emergency</dt><dd>{emergency ? 'Emergency request active' : raw?.pedestrianSignals.length ? 'Protected crossing programme' : 'No crossing in selected network'}</dd></div><div><dt>Independent supervisor</dt><dd>{supervisor?.status?.startsWith('enforcing') ? 'Enforcing timing constraints' : supervisor?.status ?? 'Unavailable'}</dd></div></dl>
          {diagnostics?.fallback && <p className="sf-warning">Fallback reason: {diagnostics.fallback}</p>}
          {serviceAge && <div className="sf-service-age"><span className="sf-eyebrow">PHASE SERVICE AGE · LIMIT {serviceAge.maximumRedSec} S</span>{Object.entries(serviceAge.phaseAgeSec).map(([p,age])=><div key={p}><span>Phase {p}</span><meter min={0} max={serviceAge.maximumRedSec} value={age} aria-label={`Phase ${p} service age`} /><b>{age.toFixed(0)} s</b></div>)}<p className="sf-caption">Time since phase was last observed green, not vehicle delay.</p></div>}
          <details><summary>Verified controller telemetry</summary><dl className="sf-facts"><div><dt>Reported policy</dt><dd>{policy ?? 'No decision yet'}</dd></div><div><dt>Pressure by phase (PCU)</dt><dd>{Object.entries(diagnostics?.phasePressurePcu ?? {}).map(([id,n])=>`${id}: ${Number(n).toFixed(1)}`).join(' · ') || 'Not reported'}</dd></div><div><dt>Receiving supply (heuristic)</dt><dd>{Object.entries(diagnostics?.receivingSupply ?? {}).map(([id,n])=>`${id}: ${Number(n).toFixed(2)}`).join(' · ') || 'Not reported'}</dd></div></dl><p className="sf-caption">Observed inputs and reported policy are a summary, not a reconstructed causal proof. Raw supervisor decisions remain in technical telemetry below.</p></details>
          <Badge tone="warn">MAPPO: Experimental — Not Qualified</Badge>
        </Panel>
        <Panel title="Approach conditions" eyebrow={selected ? `JUNCTION ${selected}` : 'PRIMARY JUNCTION'}>
          {raw ? Object.entries(raw.approaches).map(([direction,row])=><div key={direction} className="sf-approach-row"><span>{direction}<small>{row.vehicles} vehicles · {row.avgWaitTimeSec.toFixed(1)} s wait</small></span><div className="sf-queue-bar"><i style={{width:`${row.vehicles ? Math.min(100,row.queued/row.vehicles*100) : 0}%`}} /></div><strong data-testid={`queue-${direction}`}>{row.queued}<small>queued</small></strong></div>) : <p className="sf-caption">Approach counts will appear when SUMO is connected.</p>}
          {Object.entries(raw?.downstream ?? {}).filter(([,r])=>r.spillbackIndicator).map(([d,r])=><p className="sf-warning" key={d}>{d} receiver: {r.occupancyPercent.toFixed(1)}% occupied. Spillback heuristic triggered.</p>)}
        </Panel>
      </div>
    </div>}
  </div>;
}
