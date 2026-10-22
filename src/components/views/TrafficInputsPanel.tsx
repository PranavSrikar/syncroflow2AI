import React, { useEffect, useState } from 'react';

type Inputs = {
  source: string; fallback: string | null;
  perception: {
    available: boolean;
    unavailableApproaches: string[]; partialCoverage: boolean;
    cameras: Record<string, { state: string; fresh: boolean; error: string | null; lastFrame: { approaches: Record<string, { vehicles: number; queued: number; lineCrossings: number; regionUniqueTrackEntries: number; maxObservedWaitSec: number; queueLengthM: number | null; densityVehiclesPerM2: number | null; confidence: number | null }> } | null }>;
    fused: { approaches: Record<string, { vehicles: number; queued: number }>; warnings: string[] } | null;
  };
  forecasts: { enabled: boolean; available: boolean; exampleData: boolean; fallback: string | null; weatherAvailable: boolean; rainfallMmH: number | null; uncertainty: string;
    approaches: Record<string, { confidence: string; steps: { arrivalRatePcuPerSec: number; lowerPcuPerSec: number; upperPcuPerSec: number }[] }> };
};
const api = (import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');

export function TrafficInputsPanel() {
  const [state, setState] = useState<Inputs | null>(null);
  const [source, setSource] = useState('sumo');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const abort = new AbortController();
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const response = await fetch(api + '/traffic-state?source=' + source, { signal: abort.signal });
        if (!response.ok) throw new Error('Input telemetry unavailable');
        const body = await response.json();
        if (!disposed) setState(body);
      } catch (err) { if (!disposed) { setError(String(err)); setState(null); } }
      if (!disposed) timer = setTimeout(poll, 1500);
    };
    void poll();
    return () => { disposed = true; clearTimeout(timer); abort.abort(); };
  }, [source]);
  const command = async (path: string, body?: unknown) => {
    setBusy(true);
    try {
      const response = await fetch(api + path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : JSON.stringify(result.detail));
      setError('');
    } catch (err) { setError(String(err)); } finally { setBusy(false); }
  };
  return <div className="bg-slate-900 p-4 rounded space-y-3">
    <h2 className="text-lg">Camera observations and arrival forecasts</h2>
    <label>Observation source: <select aria-label="Observation source" value={source} className="bg-slate-800 p-2" onChange={e => setSource(e.target.value)}><option value="sumo">SUMO (default)</option><option value="camera">Configured cameras</option></select></label>
    <p>Selected data: {state?.source ?? 'unavailable'}. {state?.fallback}</p>
    <p className="text-slate-400">Camera mode displays measurements. Signal control continues to use supervised SUMO state. Configure camera sources on the backend before starting.</p>
    {state?.perception.partialCoverage && <p className="text-amber-300">Partial camera coverage. Unavailable approaches: {state.perception.unavailableApproaches.join(', ')}.</p>}
    <div className="flex gap-3"><button disabled={busy} onClick={() => command('/perception/start')} className="bg-cyan-900 p-2 rounded">Start cameras</button><button disabled={busy} onClick={() => command('/perception/stop')} className="bg-slate-800 p-2 rounded">Stop cameras</button></div>
    {Object.entries(state?.perception.cameras ?? {}).map(([id, camera]) => <div key={id}><p>{id}: {camera.state}; {camera.fresh ? 'fresh' : 'unavailable or stale'} {camera.error}</p>
      {Object.entries(camera.lastFrame?.approaches ?? {}).map(([direction, row]) => <p key={direction}>{direction}: {row.vehicles} vehicles, {row.queued} queued, {row.lineCrossings} line crossings, {row.regionUniqueTrackEntries} unique region track entries; visible wait {row.maxObservedWaitSec.toFixed(1)} s; queue length {row.queueLengthM?.toFixed(1) ?? 'uncalibrated'} m; density {row.densityVehiclesPerM2?.toFixed(4) ?? 'uncalibrated'} vehicles/m²; detector confidence {row.confidence?.toFixed(2) ?? 'unavailable'}. {!camera.fresh && 'Last frame only.'}</p>)}</div>)}
    {state?.perception.fused && <><p>Fused counts: {Object.entries(state.perception.fused.approaches).map(([d, r]) => `${d} ${r.vehicles} (${r.queued} queued)`).join('; ')}</p>{state.perception.fused.warnings.map(w => <p key={w}>{w}</p>)}</>}
    <p>Forecasts: {state?.forecasts.enabled ? 'enabled' : 'disabled'}; {state?.forecasts.available ? 'available' : state?.forecasts.fallback ?? 'unavailable'}. {state?.forecasts.exampleData && 'EXAMPLE DATA — blocked for MPC by default.'}</p>
    <button disabled={busy} className="bg-cyan-900 p-2 rounded" onClick={() => command('/forecast/enabled?enabled=' + !state?.forecasts.enabled)}>{state?.forecasts.enabled ? 'Disable forecasts' : 'Enable forecasts'}</button>
    <p>Weather: {state?.forecasts.weatherAvailable ? `${state.forecasts.rainfallMmH} mm/h` : 'missing; wider uncertainty'}.</p>
    {Object.entries(state?.forecasts.approaches ?? {}).map(([direction, row]) => <p key={direction}>{direction}: next arrival rate {row.steps[0].arrivalRatePcuPerSec.toFixed(3)} PCU/s; range {row.steps[0].lowerPcuPerSec.toFixed(3)}–{row.steps[0].upperPcuPerSec.toFixed(3)}; confidence {row.confidence}.</p>)}
    <p className="text-slate-400">{state?.forecasts.uncertainty}</p>
    {error && <p role="alert" className="text-red-400">{error}</p>}
  </div>;
}
