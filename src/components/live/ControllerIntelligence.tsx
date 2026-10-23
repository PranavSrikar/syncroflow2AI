import React, { useState } from 'react';
import { useLiveTraffic } from '../../services/liveTraffic';
import { policySummary } from '../../services/trafficPresentation';
import { Badge, Panel } from './primitives';

export function ModelGuide() {
  const models = [
    ['Max-Pressure extension', 'P(phase) = Σ weight(link) × movement pressure', 'Stopped vehicles are PCU-weighted. Movement pressure uses upstream minus downstream queues; a flagged receiver uses negative upstream minus downstream. Priority-green weight is 1; yielding-green weight is 0.5. The controller extends the incumbent within its legal cyclic programme; it is not unrestricted network phase optimization.'],
    ['Finite-candidate constrained MPC', 'q[d,t+1] = max(0, q[d,t] + arrivals[d,t] − service[d,t])', 'The backend enumerates feasible remaining/next-green candidates over 60 one-second steps. Service is 0.5 PCU/s × route-weighted receiving supply for served approaches; the saturation value is uncalibrated. It minimizes accumulated queue + 5 × terminal queue + 2 × switch count, with an optional qualified coordination penalty. It does not solve a continuous quadratic programme. Default solve budget is 50ms, with Max-Pressure fallback.'],
    ['State estimation', 'arrival rate = unique observed arrivals / observation window', 'The estimator tracks vehicle identities over up to 60 seconds. Arrival/discharge observations are estimates, not field ground truth or trained neural forecasts. Current wait averages concern vehicles presently on approaches; they are not completed-trip delays.'],
    ['Historical forecasting', 'arrival estimate → seasonal / aggregate shrinkage baseline', 'History is filtered by junction, time and age. Heuristic uncertainty widens with rain and missing weather; it is not calibrated statistical coverage. Example data is explicitly identified and barred from MPC by default.'],
    ['Independent safety supervision', 'candidate → timing / clearance / occupancy / fairness gates → actuation', 'Existing green, yellow, all-red, pedestrian and maximum-red constraints remain authoritative. Invalid feedback or infeasible safety observations can pause the simulation. Phase service age is time since green was last observed; it does not itself prove a particular action was fairness-driven.'],
    ['MAPPO research infrastructure', 'qualified recommendation (optional) → constrained MPC → supervisor', 'Training, inference and qualification infrastructure are implemented. Phase 5 candidates failed qualification, so operational MAPPO is disabled. The current Hybrid uses MPC and Max-Pressure fallback; no learned-policy benefit is established.'],
  ];
  return <div className="sf-model-guide">{models.map(([title,equation,description])=><details key={title}><summary>{title}</summary><div className="sf-model-equation">{equation}</div><p>{description}</p></details>)}<p className="sf-caption">Implementation references: max_pressure_controller.py, constrained_mpc.py, traffic_estimation.py, forecasting.py and signal/pedestrian supervisors. The separate browser model's IDM equations do not define SUMO's car-following behaviour.</p></div>;
}

export function ControllerIntelligence() {
  const {state,online}=useLiveTraffic();const [tab,setTab]=useState('Decision trace');const [junction,setJunction]=useState('');
  const ids=Object.keys(state?.junctions ?? {});const id=ids.includes(junction)?junction:ids[0];
  const local=id?state?.junctions?.[id]:null;
  const diagnostics=(local?.controllerDiagnostics ?? state?.controllerDiagnostics) as Record<string,any>|null;
  const supervisor=(local?.safetySupervisor ?? state?.safetySupervisor) as {status?:string;decisions?:{simTime:number;accepted:boolean;reason:string;phaseIndex?:number;remainingSec?:number}[]}|undefined;
  const raw=local?.telemetry ?? state?.telemetry;const age=local?.serviceAge ?? state?.serviceAge;
  return <Panel title="Controller intelligence" eyebrow="REPORTED DECISIONS / NO RECONSTRUCTED CAUSAL CLAIMS">
    <div className="sf-tabs" role="tablist" aria-label="Controller information">{['Decision trace','Architecture','Models & assumptions'].map(t=><button key={t} role="tab" aria-selected={t===tab} onClick={()=>setTab(t)}>{t}</button>)}</div>
    <div role="tabpanel" aria-label={tab}>
      {tab==='Decision trace' && <><div className="sf-map-toolbar"><Badge tone={online?'good':'warn'}>{online?'Actual backend state':'Stale / unavailable'}</Badge>{ids.length>0 && <label>Junction <select aria-label="Controller junction" value={id} onChange={e=>setJunction(e.target.value)}>{ids.map(id=><option key={id}>{id}</option>)}</select></label>}</div><div className="sf-controller-summary"><article><h3>Reported policy</h3><strong>{policySummary(diagnostics?.policy)}</strong><p>Exact policy: {diagnostics?.policy ?? 'unavailable'}</p><p>Forecast source: {diagnostics?.arrivalForecastSource ?? 'not reported'}</p><p>Fallback: {diagnostics?.fallback ?? 'none reported'}</p></article><article><h3>Current observation</h3><p>Simulation time: {raw?.simTime ?? '—'} s</p><p>Signal phase: {raw ? Object.entries(raw.trafficLights).map(([id,l])=>`${id}: ${l.phaseIndex}`).join(' · ') : 'unavailable'}</p><p>Safety: {supervisor?.status ?? 'unavailable'}</p><p>Emergency: {local?.emergencyPriority.activeVehicleId ?? state?.emergencyPriority?.activeVehicleId ?? 'none reported'}</p></article></div>
        <div className="sf-pressure-grid">{Object.entries(diagnostics?.phasePressurePcu ?? {}).map(([p,n])=><article key={p}><span>Phase {p} pressure</span><strong>{Number(n).toFixed(2)} <small>PCU</small></strong></article>)}</div>
        {age && <p className="sf-caption">Observed phase service age: {Object.entries(age.phaseAgeSec).map(([p,n])=>`${p}: ${n.toFixed(0)}s`).join(' · ')}; maximum-red gate {age.maximumRedSec}s. Not individual wait or proof of intervention.</p>}
        <div className="sf-table-scroll"><table><caption>Latest actual supervisor decisions · trace time can precede current observation</caption><thead><tr><th>Time (s)</th><th>Phase</th><th>Decision</th><th>Reason</th></tr></thead><tbody>{supervisor?.decisions?.slice(-12).reverse().map((d,i)=><tr key={i}><td>{d.simTime}</td><td>{d.phaseIndex ?? '—'}</td><td>{d.accepted?'Accepted':'Rejected'}</td><td>{d.reason}</td></tr>)}</tbody></table>{!supervisor?.decisions?.length && <p className="sf-empty">No timing action trace yet. Observing a signal does not imply a new controller action.</p>}</div></>}
      {tab==='Architecture' && <><div className="sf-pipeline">{['SUMO observations','State estimation','Historical forecasts (optional)','Max-Pressure / qualified hints only','Constrained MPC or fallback','Independent safety supervisor','SUMO actuation'].map((s,i)=><article key={s}><small>0{i+1}</small><strong>{s}</strong></article>)}</div><Badge tone="warn">MAPPO recommendations disabled: experimental, not qualified</Badge><p className="sf-caption">Architecture illustration, not a claim that every optional stage ran for the current action. Reported policy and trace identify observed runtime behaviour.</p></>}
      {tab==='Models & assumptions' && <ModelGuide />}
    </div>
  </Panel>;
}
