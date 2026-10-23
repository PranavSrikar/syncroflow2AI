import React, { useEffect, useState } from 'react';
import { backendApi, requestBackend } from '../../services/liveTraffic';

type Inputs = {
  source: string; fallback: string | null;
  perception: {
    available: boolean;
    unavailableApproaches: string[]; partialCoverage: boolean;
    cameras: Record<string, { state: string; sourceKind?: string; observationAgeSec?: number | null; timestampBasis?: string; fresh: boolean; error: string | null; lastFrame: { timestamp?: number; approaches: Record<string, { vehicles: number; queued: number; lineCrossings: number; regionUniqueTrackEntries: number; maxObservedWaitSec: number; queueLengthM: number | null; densityVehiclesPerM2: number | null; confidence: number | null }> } | null }>;
    fused: { approaches: Record<string, { vehicles: number; queued: number }>; warnings: string[] } | null;
  };
  forecasts: { generatedAt?: string; horizonSec?: number; source?: string; enabled: boolean; available: boolean; exampleData: boolean; fallback: string | null; weatherAvailable: boolean; rainfallMmH: number | null; uncertainty: string;
    approaches: Record<string, { confidence: string; steps: { offsetSec?: number; arrivalRatePcuPerSec: number; lowerPcuPerSec: number; upperPcuPerSec: number }[] }> };
};
const api = backendApi;

export function TrafficInputsPanel({ kind = 'camera' }: { kind?: 'camera' | 'forecast' }) {
  const [state, setState] = useState<Inputs | null>(null);
  const [source, setSource] = useState('sumo');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [pollError, setPollError] = useState('');
  const [csv, setCsv] = useState('');
  const [example, setExample] = useState(false);
  const [rain, setRain] = useState('0');
  const [config, setConfig] = useState<Record<string, unknown> | null>(null);
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [provider, setProvider] = useState('manual');
  const [horizon, setHorizon] = useState(60);
  useEffect(() => {
    let disposed = false;
    requestBackend('/forecast/config').then(value => {
      if (!disposed) { setConfig(value); setLatitude(value.latitude?.toString() ?? ''); setLongitude(value.longitude?.toString() ?? ''); setProvider(value.weather_provider); }
    }).catch(err => { if (!disposed) setError(String(err)); });
    return () => { disposed = true; };
  }, []);
  useEffect(() => {
    const abort = new AbortController();
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const response = await fetch(api + '/traffic-state?source=' + source, { signal: abort.signal });
        if (!response.ok) throw new Error('Input telemetry unavailable');
        const body = await response.json();
        body.forecasts = await requestBackend('/forecast?horizon_sec=' + horizon, { signal: abort.signal });
        if (!disposed) { setState(body); setPollError(''); }
      } catch (err) { if (!disposed) { setPollError(String(err)); setState(null); } }
      if (!disposed) timer = setTimeout(poll, 1500);
    };
    void poll();
    return () => { disposed = true; clearTimeout(timer); abort.abort(); };
  }, [source, horizon]);
  const command = async (path: string, body?: unknown) => {
    setBusy(true);
    try {
      const response = await fetch(api + path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(12000) });
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : JSON.stringify(result.detail));
      const [next, settings, forecast] = await Promise.all([requestBackend('/traffic-state?source=' + source), requestBackend('/forecast/config'), requestBackend('/forecast?horizon_sec=' + horizon)]);
      next.forecasts = forecast; setState(next); setConfig(settings); setError('');
    } catch (err) { setError(String(err)); } finally { setBusy(false); }
  };
  return <div className="sf-inputs-panel bg-slate-900 p-4 rounded space-y-3">
    <h2 className="text-lg">{kind === 'camera' ? 'Camera observations' : 'Arrival forecasts'}</h2>
    <details className="sf-input-section" open={kind === 'camera'}><summary>Camera inputs</summary>
    <label>Observation source: <select aria-label="Observation source" value={source} className="bg-slate-800 p-2" onChange={e => setSource(e.target.value)}><option value="sumo">SUMO (default)</option><option value="camera">Configured cameras</option></select></label>
    <p>Selected data: {state?.source ?? 'unavailable'}. {state?.fallback}</p>
    <p className="text-slate-400">Camera mode displays measurements. Signal control continues to use supervised SUMO state. Configure camera sources on the backend before starting.</p>
    {state?.perception.partialCoverage && <p className="text-amber-300">Partial camera coverage. Unavailable approaches: {state.perception.unavailableApproaches.join(', ')}.</p>}
    <div className="flex gap-3"><button disabled={busy || !state} onClick={() => command('/perception/start')} className="bg-cyan-900 p-2 rounded">Start cameras</button><button disabled={busy || !state} onClick={() => command('/perception/stop')} className="bg-slate-800 p-2 rounded">Stop cameras</button></div>
    {Object.entries(state?.perception.cameras ?? {}).map(([id, camera]) => <article className="sf-camera-tile" key={id}><div className="sf-preview-unavailable">Preview unavailable<span>Detection telemetry available below; no frame-streaming API</span></div><p>{id}: {camera.state}; {camera.fresh ? 'fresh' : 'unavailable or stale'} {camera.error}</p>
      <div className="sf-camera-source"><span className="sf-badge sf-warn">{camera.sourceKind === 'recorded_video' ? 'Recorded video · replayed observations' : camera.sourceKind === 'live_camera' ? 'Live camera source' : 'Source type unavailable'}</span><span className="sf-caption">Observation age: {camera.observationAgeSec?.toFixed(1) ?? '—'} s · timestamp {camera.lastFrame?.timestamp?.toFixed(2) ?? '—'} ({camera.timestampBasis ?? 'unspecified'})</span></div>
      {Object.entries(camera.lastFrame?.approaches ?? {}).map(([direction, row]) => <p key={direction}>{direction}: {row.vehicles} vehicles, {row.queued} queued, {row.lineCrossings} line crossings, {row.regionUniqueTrackEntries} unique region track entries; visible wait {row.maxObservedWaitSec.toFixed(1)} s; queue length {row.queueLengthM?.toFixed(1) ?? 'uncalibrated'} m; density {row.densityVehiclesPerM2?.toFixed(4) ?? 'uncalibrated'} vehicles/m²; detector confidence {row.confidence?.toFixed(2) ?? 'unavailable'}. {!camera.fresh && 'Last frame only.'}</p>)}</article>)}
    {state?.perception.fused && <><p>Fused counts: {Object.entries(state.perception.fused.approaches).map(([d, r]) => `${d} ${r.vehicles} (${r.queued} queued)`).join('; ')}</p>{state.perception.fused.warnings.map(w => <p key={w}>{w}</p>)}</>}
    </details>
    <details className="sf-input-section" open={kind === 'forecast'}><summary>Forecast configuration</summary>
    <p>Forecasts: {state?.forecasts.enabled ? 'enabled' : 'disabled'}; {state?.forecasts.available ? 'available' : state?.forecasts.fallback ?? 'unavailable'}. {state?.forecasts.exampleData && 'EXAMPLE DATA — blocked for MPC by default.'}</p>
    <button disabled={busy || !state} className="bg-cyan-900 p-2 rounded" onClick={() => command('/forecast/enabled?enabled=' + !state?.forecasts.enabled)}>{state?.forecasts.enabled ? 'Disable forecasts' : 'Enable forecasts'}</button>
    <p>Weather: {state?.forecasts.weatherAvailable ? `${state.forecasts.rainfallMmH} mm/h` : 'missing; wider uncertainty'}.</p>
    <label>Prediction horizon <select aria-label="Prediction horizon" value={horizon} onChange={e=>setHorizon(Number(e.target.value))}><option value={60}>60 seconds</option><option value={120}>120 seconds</option><option value={300}>300 seconds</option></select></label>
    <p className="sf-caption">Forecast estimate · {state?.forecasts.source ?? 'source unavailable'} · generated {state?.forecasts.generatedAt ?? 'unavailable'} · horizon {state?.forecasts.horizonSec ?? '—'} s. Generated time is the forecast query time, not the age of historical observations.</p>
    {Object.entries(state?.forecasts.approaches ?? {}).filter(([, row]) => row.steps.length > 0).map(([direction, row]) => <p key={direction}>{direction}: next arrival rate {row.steps[0].arrivalRatePcuPerSec.toFixed(3)} PCU/s; range {row.steps[0].lowerPcuPerSec.toFixed(3)}–{row.steps[0].upperPcuPerSec.toFixed(3)}; confidence {row.confidence}.</p>)}
    <p className="text-slate-400">{state?.forecasts.uncertainty}</p>
    <div className="sf-forecast-grid">{Object.entries(state?.forecasts.approaches ?? {}).filter(([,r])=>r.steps.length).map(([direction,row])=>{
      const maximum=Math.max(.01,...row.steps.map(p=>p.upperPcuPerSec));
      const point=(p: typeof row.steps[number], field:'arrivalRatePcuPerSec'|'lowerPcuPerSec'|'upperPcuPerSec')=>`${30+(p.offsetSec ?? 0)/horizon*300},${110-p[field]/maximum*85}`;
      return <figure key={direction} className="sf-crossing"><figcaption>{direction} · forecast estimate (PCU/s)</figcaption><svg role="img" aria-label={`${direction} forecast uncertainty`} viewBox="0 0 350 135"><title>Arrival estimate with heuristic lower and upper bounds, not calibrated confidence coverage.</title><polygon points={[...row.steps.map(p=>point(p,'upperPcuPerSec')),...row.steps.slice().reverse().map(p=>point(p,'lowerPcuPerSec'))].join(' ')} fill="#49c9bd" opacity=".15" /><polyline points={row.steps.map(p=>point(p,'arrivalRatePcuPerSec')).join(' ')} fill="none" stroke="#49c9bd" strokeWidth="2" />{row.steps.map((p,i)=>{const [x,y]=point(p,'arrivalRatePcuPerSec').split(',');return <circle key={i} cx={x} cy={y} r="3" fill="#81d8ce"><title>+{p.offsetSec}s: {p.arrivalRatePcuPerSec.toFixed(3)} PCU/s; heuristic range {p.lowerPcuPerSec.toFixed(3)}–{p.upperPcuPerSec.toFixed(3)}</title></circle>})}<text x="4" y="25" fill="#a3b3c8" fontSize="9">{maximum.toFixed(2)}</text><text x="10" y="113" fill="#a3b3c8" fontSize="9">0</text><text x="30" y="130" fill="#a3b3c8" fontSize="9">now</text><text x="280" y="130" fill="#a3b3c8" fontSize="9">+{horizon}s</text></svg></figure>;
    })}</div>
    <details className="space-y-3"><summary>Historical CSV and weather configuration</summary>
      <p>Upload historical arrivals (timestamp, approach, arrivals_pcu, interval_sec; optional junction_id). Timestamps require a timezone. Test data must be marked as demonstration data; it remains blocked for MPC unless explicitly authorized on the backend.</p>
      <label>Historical arrival CSV<textarea aria-label="Historical arrival CSV" className="block bg-slate-800 w-full p-2" value={csv} onChange={e => setCsv(e.target.value)} /></label>
      <label><input aria-label="CSV is demonstration data" type="checkbox" checked={example} onChange={e => setExample(e.target.checked)} /> CSV is demonstration/test data</label>
      <button className="bg-cyan-900 p-2" disabled={busy || !state || !csv.trim()} onClick={() => command('/forecast/history', { csv, example_data: example })}>Upload history CSV</button>
      <label>Weather provider <select aria-label="Weather provider" value={provider} onChange={e => setProvider(e.target.value)} className="bg-slate-800 p-2"><option value="disabled">Disabled</option><option value="manual">Manual input</option><option value="open_meteo">Open-Meteo</option></select></label>
      <label>Latitude <input aria-label="Weather latitude" type="number" value={latitude} onChange={e => setLatitude(e.target.value)} className="bg-slate-800 p-2" /></label>
      <label>Longitude <input aria-label="Weather longitude" type="number" value={longitude} onChange={e => setLongitude(e.target.value)} className="bg-slate-800 p-2" /></label>
      <button className="bg-cyan-900 p-2" disabled={busy || !config || !state || (provider === 'open_meteo' && (!latitude || !longitude))} onClick={() => command('/forecast/config', { ...config, enabled: state?.forecasts.enabled, weather_provider: provider, latitude: latitude ? Number(latitude) : null, longitude: longitude ? Number(longitude) : null })}>Apply weather configuration</button>
      <label>Manual rainfall mm/h <input aria-label="Manual rainfall mm/h" type="number" min="0" max="500" value={rain} onChange={e => setRain(e.target.value)} className="bg-slate-800 p-2" /></label>
      <button className="bg-cyan-900 p-2" disabled={busy || !state || !Number.isFinite(Number(rain)) || Number(rain) < 0 || Number(rain) > 500} onClick={() => command('/forecast/weather', { timestamp: new Date().toISOString(), rainfall_mm_h: Number(rain), source: 'manual_browser_input' })}>Set manual weather</button>
      <button className="bg-slate-800 p-2" disabled={busy || !state} onClick={() => command('/forecast/weather/refresh')}>Refresh configured weather provider</button>
      <p>Manual weather is user input, not a live sensor measurement. Open-Meteo needs coordinates and network access. No calibrated forecast accuracy is established.</p>
    </details>
    </details>
    {pollError && <p role="alert" className="text-red-400">{pollError}</p>}
    {error && <p role="alert" className="text-red-400">{error}</p>}
  </div>;
}
