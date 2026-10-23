import React, { useState } from 'react';
import { backendApi, backendSocket, requestBackend, useLiveTraffic } from '../../services/liveTraffic';

export function LiveUtilities({ kind }: { kind: 'config' | 'export' }) {
  const { state, online, refresh } = useLiveTraffic();
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const check = async () => {
    setBusy(true);
    try { const health = await requestBackend('/health'); await refresh(); setMessage(`Backend health: ${health.status}; version ${health.version}.`); }
    catch (error) { setMessage(String(error)); }
    finally { setBusy(false); }
  };
  const download = () => {
    if (!state || !online) return;
    const blob = new Blob([JSON.stringify({ source: 'sumo_traci', capturedAt: new Date().toISOString(),
      limitations: 'Current/last-run snapshot, not a completed-trip benchmark or field measurement', snapshot: state }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'synchroflow-sumo-snapshot.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  return <section className="p-6 space-y-4 overflow-auto">
    <h1 className="text-2xl">{kind === 'config' ? 'Live backend connection' : 'Export SUMO telemetry'}</h1>
    <p>REST API: {backendApi}</p><p>SUMO WebSocket: {backendSocket}</p>
    <p>Connection: {online ? 'live telemetry received' : 'disconnected or stale'}. Simulation: {online ? state?.connected ? state.running ? 'running' : 'paused' : 'stopped' : 'unknown'}.</p>
    {kind === 'config' ? <><button className="bg-cyan-900 p-2" disabled={busy} onClick={check}>Check backend health</button><p>Signal controller and network are configured in the live workspace after Stop. Camera device/weights paths are configured on the server. Authentication/RBAC and roadside hardware are not implemented; use this local research prototype in a trusted environment.</p></> : <><button className="bg-cyan-900 p-2 disabled:opacity-40" disabled={!online || !state} onClick={download}>Download live snapshot JSON</button><p>Exports actual backend state with source and capture time. A stopped simulation contains last-run data. Offline research benchmarking is documented in PHASE5_EXPERIMENT_RESULTS.md; the browser demonstration benchmark is a separate model.</p></>}
    <p role="status">{message}</p>
  </section>;
}
