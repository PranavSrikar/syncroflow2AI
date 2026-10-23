import React from 'react';
import { useLiveTraffic } from '../../services/liveTraffic';

export function LiveQueueChart() {
  const { history, online } = useLiveTraffic();
  const first = history[0]?.time ?? 0;
  const span = Math.max(1, (history.at(-1)?.time ?? 0) - first);
  const maximum = Math.max(1, ...history.map(p => p.queue));
  return <figure className="bg-slate-900 rounded p-4 space-y-2">
    <figcaption>Measured network queue — {online ? 'backend observations' : 'stale observations'}</figcaption>
    {history.length ? <><svg role="img" aria-label="Measured queue chart" data-last-queue={history.at(-1)?.queue} viewBox="0 0 600 140" className="w-full max-h-40"><title>Halted approach vehicles; observed simulation time</title><polyline fill="none" stroke="#22d3ee" strokeWidth="2" points={history.map(p => `${10 + (p.time-first)/span*580},${130-p.queue/maximum*120}`).join(' ')} /></svg><p>{first}–{history.at(-1)?.time}s; latest queue {history.at(-1)?.queue} vehicles. Vertical range 0–{maximum} vehicles.</p></> : <p>No simulation samples yet. Start SUMO to collect observations.</p>}
    <p className="text-slate-400">Latest 120 distinct simulation samples. Corridor values sum both junctions. These are observations, not predictions or completed-trip delay.</p>
  </figure>;
}
