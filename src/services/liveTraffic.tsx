import React, { createContext, useContext, useEffect, useState } from 'react';
import type { Snapshot } from '../components/views/SumoLiveView';

export const backendApi = (import.meta.env.VITE_BACKEND_API_URL || 'http://127.0.0.1:8001/api/v1').replace(/\/$/, '');
export const backendSocket = backendApi.replace(/^http/, 'ws') + '/sumo/ws';
type QueuePoint = { time: number; queue: number };
type LiveState = { state: Snapshot | null; online: boolean; error: string; history: QueuePoint[]; refresh: () => Promise<void> };
const Context = createContext<LiveState | null>(null);

export async function requestBackend(path: string, options?: RequestInit) {
  const response = await fetch(backendApi + path, { ...options, signal: options?.signal ?? AbortSignal.timeout(10000) });
  const body = await response.json();
  if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail ?? `HTTP ${response.status}`));
  return body;
}

export function LiveTrafficProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<Snapshot | null>(null);
  const [online, setOnline] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<QueuePoint[]>([]);
  const refresh = async () => { setState(await requestBackend('/sumo/status')); };
  useEffect(() => {
    let disposed = false;
    let socket: WebSocket;
    let reconnect: ReturnType<typeof setTimeout>;
    let lastMessage = 0;
    const connect = () => {
      socket = new WebSocket(backendSocket);
      socket.onmessage = event => {
        if (disposed) return;
        try {
          const body = JSON.parse(event.data);
          if (typeof body.connected !== 'boolean' || !body.safetySupervisor) throw new Error();
          lastMessage = Date.now(); setState(body); setOnline(true); setError('');
          if (body.telemetry) {
            const raws = Object.keys(body.junctions ?? {}).length ? Object.values(body.junctions).map((j: any) => j.telemetry) : [body.telemetry];
            const point = { time: body.telemetry.simTime, queue: raws.reduce((sum: number, raw: any) => sum + Object.values(raw.approaches).reduce((n: number, row: any) => n + row.queued, 0), 0) };
            setHistory(previous => previous.at(-1)?.time === point.time ? previous : previous.at(-1) && point.time < previous.at(-1)!.time ? [point] : [...previous.slice(-119), point]);
          }
        } catch { setOnline(false); setError('Invalid backend telemetry; controls disabled.'); }
      };
      socket.onerror = () => { if (!disposed) { setOnline(false); setError('Backend unavailable; live controls disabled.'); } };
      socket.onclose = () => {
        if (!disposed) { setOnline(false); setError('Backend disconnected; displayed telemetry may be stale.'); reconnect = setTimeout(connect, 1500); }
      };
    };
    connect();
    const stale = setInterval(() => {
      if (lastMessage && Date.now() - lastMessage > 4000) { setOnline(false); setError('Backend telemetry is stale; controls disabled.'); }
    }, 1000);
    return () => { disposed = true; clearTimeout(reconnect); clearInterval(stale); socket.close(); };
  }, []);
  return <Context.Provider value={{ state, online, error, history, refresh }}>{children}</Context.Provider>;
}
export function useLiveTraffic() {
  const value = useContext(Context);
  if (!value) throw new Error('LiveTrafficProvider missing');
  return value;
}
