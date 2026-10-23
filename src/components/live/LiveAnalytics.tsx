import React, { useState } from 'react';
import { useLiveTraffic } from '../../services/liveTraffic';
import { Badge, Panel } from './primitives';
export function Trend({ label, unit, points, color = '#49c9bd' }: { label: string; unit: string; points: {time:number;value:number|null}[]; color?: string }) {
  const valid = points.filter((p): p is {time:number;value:number} => p.value !== null && Number.isFinite(p.value));
  const maximum=Math.max(1,...valid.map(p=>p.value)); const start=points[0]?.time ?? 0, end=points.at(-1)?.time ?? start;
  const coordinates=(p:{time:number;value:number})=>`${36+(p.time-start)/Math.max(1,end-start)*520},${150-p.value/maximum*120}`;
  const segments: {time:number;value:number}[][] = [];
  for (const p of points) { if(p.value===null || !Number.isFinite(p.value)){ if(segments.at(-1)?.length)segments.push([]); } else { if(!segments.length)segments.push([]); segments.at(-1)!.push(p as {time:number;value:number}); } }
  return <figure className="sf-trend"><figcaption>{label}<span>{unit}</span></figcaption>{valid.length ? <svg role="img" aria-label={label} viewBox="0 0 580 185"><title>{label} from observed simulation samples, in {unit}. Missing observations are gaps.</title>{[0,0.5,1].map(f=><g key={f}><line x1="36" x2="556" y1={150-f*120} y2={150-f*120} stroke="#253449" strokeDasharray="3 4" /><text x="3" y={154-f*120} fill="#a3b3c8" fontSize="10">{(f*maximum).toFixed(f*maximum<10?1:0)}</text></g>)}{segments.map((s,i)=><polyline key={i} points={s.map(coordinates).join(' ')} fill="none" stroke={color} strokeWidth="2" />)}{valid.map((p,i)=>{const [cx,cy]=coordinates(p).split(',');return <circle key={i} cx={cx} cy={cy} r="3" fill={color}><title>{p.time} s: {p.value.toFixed(2)} {unit}</title></circle>})}<text x="36" y="178" fill="#a3b3c8" fontSize="10">{start}s</text><text x="518" y="178" fill="#a3b3c8" fontSize="10">{end}s</text></svg> : <p className="sf-empty">No observed samples yet. Start SUMO to collect this trend.</p>}<p className="sf-caption">SUMO observations · {valid.length} available samples · simulation seconds</p></figure>;
}
export function LiveAnalytics() {
  const { history, online } = useLiveTraffic();
  const [window,setWindow]=useState(120);
  const last=history.at(-1)?.time ?? 0;
  const samples=history.filter(p=>p.time>=last-window);
  return <Panel title="Measured traffic trends" eyebrow="LIVE SUMO / BOUNDED SESSION HISTORY">
    <div className="sf-map-toolbar"><Badge tone={online?'good':'warn'}>{online?'Observed samples':'Stale observations'}</Badge><label>Time window <select aria-label="Analytics time window" value={window} onChange={e=>setWindow(Number(e.target.value))}><option value={30}>Last 30 simulation seconds</option><option value={60}>Last 60 simulation seconds</option><option value={120}>Last 120 simulation seconds</option></select></label></div>
    <div className="sf-trends-grid"><Trend label="Network queue" unit="vehicles" points={samples.map(p=>({time:p.time,value:p.queue}))} /><Trend label="Current approach mean wait" unit="seconds" color="#b3a7d5" points={samples.map(p=>({time:p.time,value:p.wait}))} /><Trend label="Run throughput" unit="vehicles/hour" color="#91b8da" points={samples.map(p=>({time:p.time,value:p.throughput}))} /></div>
    <p className="sf-caption">Latest 120 distinct received samples. This is session history, not an archive. Wait is weighted by current approach vehicle counts. Run throughput counts completed SUMO arrivals; neither is completed-trip delay.</p>
    <div className="sf-table-scroll"><table><caption>Latest per-approach rates and queues · SUMO estimates</caption><thead><tr><th>Approach</th><th>Queue (veh)</th><th>Wait (s)</th><th>Arrivals (veh/s)</th><th>Discharge (veh/s)</th></tr></thead><tbody>{Object.entries(samples.at(-1)?.approaches ?? {}).map(([id,p])=><tr key={id}><td>{id}</td><td>{p.queue}</td><td>{p.wait.toFixed(1)}</td><td>{p.arrivals?.toFixed(3) ?? '—'}</td><td>{p.discharge?.toFixed(3) ?? '—'}</td></tr>)}</tbody></table></div>
  </Panel>;
}
