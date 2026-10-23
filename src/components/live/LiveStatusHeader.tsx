import React, { useEffect, useState } from 'react';
import { useLiveTraffic } from '../../services/liveTraffic';
import { Badge } from './primitives';
export function LiveStatusHeader({ synthetic }: { synthetic: boolean }) {
  const { state, online, receivedAt } = useLiveTraffic();
  const [now,setNow] = useState(Date.now());
  const networks: Record<string,string> = { vehicle: 'Central research junction', pedestrian: 'Protected pedestrian junction', corridor: 'Two-junction research corridor', unequal: 'Unequal-demand junction', spillback: 'Downstream spillback junction' };
  useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),1000);return()=>clearInterval(timer)},[]);
  return <header className="sf-status-header">
    <div><span className="sf-eyebrow">SYNCHROFLOW / TRAFFIC INTELLIGENCE</span><div className="sf-header-title">{synthetic ? 'Synthetic Oak Street' : networks[state?.scenario ?? ''] ?? 'Intersection operations'}<span data-testid="simulation-state" data-status={synthetic?'synthetic':!online?'disconnected':!state?.connected?'stopped':state.running?'running':'paused'}><Badge tone={synthetic ? 'warn' : online ? 'good' : 'warn'}>{synthetic ? 'Browser demonstration' : online ? state?.connected ? state.running ? 'Running' : 'Paused' : 'Ready to start' : 'Disconnected'}</Badge></span></div></div>
    <div className="sf-connection-cluster" aria-label="Header telemetry">
      <span>Backend: <b>{online ? 'connected' : 'disconnected'}</b> · WS: <b>{online ? 'receiving' : 'offline'}</b></span>
      <span>SUMO: <b>{online ? state?.connected ? 'connected' : 'stopped' : 'unknown'}</b> · Controller: <b>{online ? state?.controller ?? 'unavailable' : 'unavailable'}</b></span>
      <span>Sample age: <b>{receivedAt ? `${Math.max(0,(now-receivedAt)/1000).toFixed(0)} s` : 'waiting'}</b> · Simulation: <b>{state?.telemetry?.simTime ?? '—'} s</b></span>
      <span>Safety: <b>{!synthetic && online && state?.connected && state.safetySupervisor.status.startsWith('enforcing') ? 'Enforcing timing constraints' : synthetic ? 'Browser model only' : 'Unavailable'}</b></span>
    </div>
  </header>;
}
