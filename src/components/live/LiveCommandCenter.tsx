import React, { useState } from 'react';
import { useLiveTraffic } from '../../services/liveTraffic';
import { approachPermission, policySummary } from '../../services/trafficPresentation';
import { LiveNetworkMap } from './LiveNetworkMap';
import { Badge, Metric, Panel } from './primitives';

export function LiveCommandCenter({ scope }: { scope: string }) {
  const { state, online, error } = useLiveTraffic();
  const [selection, setSelection] = useState('auto');
  const junctions = Object.keys(state?.junctions ?? {});
  const choices = junctions.length ? junctions : Object.keys(state?.telemetry?.trafficLights ?? {});
  const selected = selection === 'auto' && choices.length === 1 ? choices[0] : choices.includes(selection) ? selection : null;
  const local = selected ? state?.junctions?.[selected] : null;
  const raw = local?.telemetry ?? state?.telemetry ?? null;
  const available = online && !!raw && !!state?.connected;
  const rows = local ? Object.values(raw?.approaches ?? {}) : junctions.length ? Object.values(state!.junctions!).flatMap(j=>Object.values(j.telemetry.approaches)) : Object.values(raw?.approaches ?? {});
  const count=rows.reduce((n,r)=>n+r.vehicles,0), queue=rows.reduce((n,r)=>n+r.queued,0);
  const wait=count ? rows.reduce((n,r)=>n+r.vehicles*r.avgWaitTimeSec,0)/count : null;
  const diagnostics = (local?.controllerDiagnostics ?? (junctions.length ? state?.junctions?.[junctions[0]]?.controllerDiagnostics : state?.controllerDiagnostics)) as Record<string, any> | null;
  const supervisor = (local?.safetySupervisor ?? state?.safetySupervisor) as {status?:string; lastDecision?:{accepted?:boolean;phaseIndex?:number;reason?:string};decisions?:{simTime:number;accepted:boolean;reason:string;phaseIndex?:number}[]} | undefined;
  const serviceAge = local?.serviceAge ?? state?.serviceAge;
  const emergency = local?.emergencyPriority.activeVehicleId ?? state?.emergencyPriority?.activeVehicleId;
  const lastDecision = supervisor?.decisions?.at(-1);
  const lights = Object.entries(raw?.trafficLights ?? {});
  const primary = selected ?? junctions[0] ?? lights[0]?.[0];
  const light = raw?.trafficLights[primary];
  const crossings = raw?.pedestrianSignals ?? [];
  const spillbacks = Object.entries(raw?.downstream ?? {}).filter(([,r])=>r.spillbackIndicator);
  return <div className="sf-command-experience">
    <div className="sf-kpi-grid" aria-busy={!state && !error} aria-label="Live SUMO metrics">
      <Metric label="Approach vehicles" value={available ? count : '—'} unit="veh" hint={selected ? `Approaches at ${selected}` : 'All monitored approaches'} />
      <Metric label="Vehicles in queue" value={available ? queue : '—'} unit="veh" hint="Halted approach vehicles" />
      <Metric label="Current mean wait" value={available && wait!==null ? wait.toFixed(1) : '—'} unit="s" hint="Current vehicles, weighted mean" />
      <Metric label="Run throughput" value={available && state?.metrics?.throughputVehiclesPerHour!=null ? state.metrics.throughputVehiclesPerHour.toFixed(0) : '—'} unit="veh/h" hint="Network arrivals / elapsed time" />
    </div>
    {scope !== 'analytics' && <div className="sf-command-grid">
      <Panel title="Live digital twin" className="sf-twin-panel">
        <div className="sf-map-toolbar"><Badge tone={online?'good':'warn'}>{online?selected?`Selected junction ${selected}`:'SUMO observations':'Waiting / stale'}</Badge><label>Junction <select aria-label="Digital twin junction" value={selected ?? 'network'} onChange={e=>setSelection(e.target.value)}><option value="network">Entire network</option>{choices.map(id=><option key={id} value={id}>{id}</option>)}</select></label></div>
        <LiveNetworkMap raw={raw} online={online} junction={selected ?? 'network'} />
      </Panel>
      <aside className="sf-insights" aria-label="Signal intelligence and safety">
        <section className="sf-signal-card">
          <div className="sf-insight-heading"><h2>Current signal</h2><Badge>{primary ? `${primary} · P${light?.phaseIndex ?? '—'}` : 'No active phase'}</Badge></div>
          <div className="sf-permissions">{['north','south','east','west'].map(direction=>{
            const p=raw ? approachPermission(raw,direction) : {label:'Unavailable',states:'',tone:'neutral'};
            return <div key={direction} className={`sf-permission sf-permission-${p.tone}`} title={`${direction}: ${p.label}. Actual link states: ${p.states || 'unavailable'}. Mixed permissions do not grant every movement.`}><span>{direction[0].toUpperCase()}</span><small>{available?p.label:'Unavailable'}</small></div>;
          })}</div>
          <p className="sf-switch-time">{light && online ? `Scheduled switch in ${Math.max(0,light.nextSwitch-raw!.simTime).toFixed(0)} s` : 'Timing unavailable'}<small>Adaptive timing may change</small></p>
        </section>
        <section className="sf-decision-card">
          <div className="sf-insight-heading"><h2>Why this signal?</h2><span className="sf-policy-label">{diagnostics?.policy==='constrained_mpc'?'MPC':diagnostics?.fallback?'Fallback':'Reported policy'}</span></div>
          <p className="sf-decision-summary">{policySummary(diagnostics?.policy)}</p>
          <p className="sf-trace-verdict" data-has-trace={!!lastDecision}>{lastDecision ? `${lastDecision.accepted?'Accepted':'Rejected'} by supervisor at ${lastDecision.simTime}s${lastDecision.phaseIndex!==undefined ? ` · phase ${lastDecision.phaseIndex}` : ''}` : 'No supervisor action trace yet.'}</p>
          <details className="sf-decision-details"><summary>Inputs & decision trace</summary>
            <p>Reported policy: {diagnostics?.policy ?? 'not reported'}</p>
            <p>Last supervisor reason: {lastDecision?.reason ?? supervisor?.lastDecision?.reason ?? 'not reported'}. This trace can precede the current phase.</p>
            <p>Arrival source: {diagnostics?.arrivalForecastSource ?? 'not reported'}. Fallback: {diagnostics?.fallback ?? 'none reported'}.</p>
            <p>Pressure by phase (PCU): {Object.entries(diagnostics?.phasePressurePcu ?? {}).map(([id,n])=>`${id}: ${Number(n).toFixed(1)}`).join(' · ') || 'not reported'}.</p>
            <p>Receiving supply (heuristic): {Object.entries(diagnostics?.receivingSupply ?? {}).map(([id,n])=>`${id}: ${Number(n).toFixed(2)}`).join(' · ') || 'not reported'}.</p>
            {serviceAge && <p>Observed service ages: {Object.entries(serviceAge.phaseAgeSec).map(([p,age])=>`phase ${p}: ${age.toFixed(0)}s`).join(' · ')}. Gate: {serviceAge.maximumRedSec}s. These are phase service ages, not individual waits or proof that fairness changed this action.</p>}
            <p>Inputs are an observation summary. Only the reported policy and supervisor trace establish a recorded decision; no causal explanation is reconstructed.</p>
          </details>
        </section>
        <section className="sf-conditions-card"><div className="sf-insight-heading"><h2>Approach queues</h2><small>{primary ?? 'Awaiting SUMO'} · vehicles</small></div>
          {raw ? Object.entries(raw.approaches).map(([direction,row])=><div key={direction} className="sf-approach-row"><span>{direction}<small>{row.avgWaitTimeSec.toFixed(1)} s current wait</small></span><div className="sf-queue-bar"><i style={{width:`${row.vehicles ? Math.min(100,row.queued/row.vehicles*100):0}%`}} /></div><strong data-testid={`queue-${direction}`}>{row.queued}</strong></div>) : <p className="sf-caption">Queues appear after Start.</p>}
        </section>
        <section className="sf-events-card"><div className="sf-insight-heading"><h2>Safety events</h2><span className="sf-safety-dot" data-active={!!emergency || spillbacks.length>0} /></div>
          <p>{!online?'Backend unavailable; last state may be stale.':emergency?`Priority vehicle: ${emergency}`:spillbacks.length?`${spillbacks.map(([d])=>d).join(', ')} receiving occupancy ≥80%.`:crossings.some(c=>c.occupants.length)?'Pedestrians occupying protected crossings.':state?.connected?'No active priority or spillback event.':'Start SUMO to observe safety events.'}</p>
        </section>
      </aside>
    </div>}
  </div>;
}
