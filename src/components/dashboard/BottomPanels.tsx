/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import {
  IoTSensorNode,
  AnomalyAlert,
  SimulationMetrics,
  Direction,
  ApproachTelemetry,
} from '../../types/traffic.ts';
import {
  Maximize2,
  ZoomIn,
  ZoomOut,
  AlertTriangle,
  Info,
  ShieldAlert,
  CheckCircle2,
  Camera,
  Activity,
  Radio,
  Sliders,
  Table,
} from 'lucide-react';

interface BottomPanelsProps {
  sensorNodes: IoTSensorNode[];
  alerts: AnomalyAlert[];
  metrics: SimulationMetrics;
  telemetry: Record<Direction, ApproachTelemetry>;
}

export const BottomPanels: React.FC<BottomPanelsProps> = ({
  sensorNodes,
  alerts,
  metrics,
  telemetry,
}) => {
  const [selectedSensorType, setSelectedSensorType] = useState<string>('all');
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [activeSensor, setActiveSensor] = useState<IoTSensorNode | null>(null);

  const filteredSensors =
    selectedSensorType === 'all'
      ? sensorNodes
      : sensorNodes.filter((s) => s.type === selectedSensorType);

  // Calculate volume distribution
  const northVol = telemetry.north.queuedVehicles * 25 + 640;
  const southVol = telemetry.south.queuedVehicles * 22 + 580;
  const eastVol = telemetry.east.queuedVehicles * 28 + 720;
  const westVol = telemetry.west.queuedVehicles * 20 + 490;
  const maxVol = Math.max(northVol, southVol, eastVol, westVol, 1000);

  const directions: Direction[] = ['north', 'south', 'east', 'west'];

  return (
    <div className="flex flex-col gap-3.5 select-none text-slate-200">
      {/* 1. Real-time Approach Telemetry Table */}
      <div className="bg-slate-950/95 border border-slate-800/90 rounded-xl p-3.5 shadow-xl space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
          <div className="flex items-center gap-2">
            <Table className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-semibold text-slate-100 uppercase tracking-wider">
              Approach Queue & Discharge Telemetry
            </h3>
          </div>
          <span className="text-[10px] text-slate-400 font-mono">
            Total Queue: <strong className="text-cyan-300 font-normal">{metrics.totalQueueLength} veh</strong>
          </span>
        </div>

        {/* Tabular Telemetry Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead className="bg-slate-900/70 text-slate-400 font-mono text-[10px] uppercase border-b border-slate-800">
              <tr>
                <th className="py-2 px-2.5">Approach Arm</th>
                <th className="py-2 px-2 text-center">Queued</th>
                <th className="py-2 px-2 text-center">Discharge</th>
                <th className="py-2 px-2 text-center">Max-P</th>
                <th className="py-2 px-2 text-right">Avg Wait</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px] tabular-nums">
              {directions.map((dir) => {
                const tel = telemetry[dir];
                return (
                  <tr key={dir} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-2 px-2.5 font-medium text-slate-200 font-sans">
                      <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                        <span className="truncate max-w-[120px]">{tel.name}</span>
                      </div>
                    </td>
                    <td className="py-2 px-2 text-center font-bold text-cyan-300">
                      {tel.queuedVehicles}
                      <span className="text-[9px] text-slate-400 font-normal ml-1">
                        ({tel.laneQueues.left}L/{tel.laneQueues.through}T/{tel.laneQueues.right}R)
                      </span>
                    </td>
                    <td className="py-2 px-2 text-center text-slate-300">
                      {tel.dischargeRate} v/s
                    </td>
                    <td className="py-2 px-2 text-center text-amber-300">
                      {tel.maxPressureScore}
                    </td>
                    <td className="py-2 px-2 text-right text-emerald-400">
                      {tel.avgWaitTime}s
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 2. Traffic Data Analytics & Performance Index Card */}
      <div className="bg-slate-950/95 border border-slate-800/90 rounded-xl p-3.5 shadow-xl space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <h3 className="text-xs font-semibold text-slate-100 uppercase tracking-wider">
              Real-Time Traffic Analytics
            </h3>
          </div>
          <span className="text-[10px] text-slate-400 font-mono">
            Active: <strong className="text-cyan-300 font-normal">{metrics.totalActiveVehicles} veh</strong>
          </span>
        </div>

        {/* Volume Bars & Performance Gauge */}
        <div className="grid grid-cols-12 gap-3 pt-1">
          {/* Volume Bar Chart */}
          <div className="col-span-7 bg-slate-900/50 rounded-lg border border-slate-800/80 p-2.5 flex flex-col justify-between">
            <div className="flex items-center justify-between text-[11px] mb-1">
              <span className="text-slate-300 font-medium">Approach Inflow</span>
              <span className="font-mono text-[10px] text-slate-400">Veh/hr</span>
            </div>

            <div className="flex items-end justify-between gap-1.5 h-20 px-1 pt-2">
              {[
                { label: 'North', val: northVol, color: 'bg-cyan-500' },
                { label: 'South', val: southVol, color: 'bg-emerald-500' },
                { label: 'East', val: eastVol, color: 'bg-sky-400' },
                { label: 'West', val: westVol, color: 'bg-indigo-400' },
              ].map((bar) => {
                const heightPct = Math.round((bar.val / maxVol) * 100);
                return (
                  <div key={bar.label} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
                    <span className="text-[9px] font-mono text-slate-300">{bar.val}</span>
                    <div
                      style={{ height: `${heightPct}%` }}
                      className={`w-full rounded-t-sm ${bar.color} opacity-85 transition-all duration-300`}
                    />
                    <span className="text-[9px] text-slate-400 uppercase font-mono">{bar.label[0]}</span>
                  </div>
                );
              })}
            </div>

            <div className="text-[10px] text-slate-400 text-center pt-1 border-t border-slate-800/60 font-mono">
              Capacity: <strong className="text-cyan-400 font-normal">{metrics.throughputPerHour} v/h</strong>
            </div>
          </div>

          {/* Performance Index Gauge */}
          <div className="col-span-5 bg-slate-900/50 rounded-lg border border-slate-800/80 p-2 flex flex-col items-center justify-between">
            <span className="text-[10px] text-slate-300 font-medium text-center">
              Performance Index
            </span>

            {/* Circular Arc / Gauge (78/100) */}
            <div className="relative w-20 h-20 flex items-center justify-center my-0.5">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r="38"
                  fill="none"
                  stroke="#1e293b"
                  strokeWidth="8"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="38"
                  fill="none"
                  stroke={metrics.performanceIndex >= 75 ? '#10b981' : '#f59e0b'}
                  strokeWidth="8"
                  strokeDasharray="238.7"
                  strokeDashoffset={238.7 * (1 - metrics.performanceIndex / 100)}
                  strokeLinecap="round"
                  className="transition-all duration-500"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-lg font-bold font-mono text-slate-100">
                  {metrics.performanceIndex}
                </span>
                <span className="text-[8px] text-slate-400 font-mono">/ 100</span>
              </div>
            </div>

            <span className="text-[9px] text-emerald-400 font-mono text-center">
              Level: Optimal
            </span>
          </div>
        </div>

        {/* Anomaly Alerts Feed */}
        <div className="bg-slate-900/50 rounded-lg border border-slate-800/80 p-2.5 space-y-2">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-300 font-medium flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              Real-Time Anomaly Feed
            </span>
            <span className="text-[9px] text-slate-400 font-mono">Live</span>
          </div>

          <div className="space-y-1.5 max-h-24 overflow-y-auto pr-1 text-[10px]">
            {alerts.slice(0, 3).map((alert) => (
              <div
                key={alert.id}
                className={`p-1.5 rounded border ${
                  alert.severity === 'critical'
                    ? 'bg-rose-950/40 border-rose-500/40 text-rose-200'
                    : alert.severity === 'warning'
                    ? 'bg-amber-950/40 border-amber-500/40 text-amber-200'
                    : 'bg-slate-950/60 border-slate-800 text-slate-300'
                }`}
              >
                <div className="font-semibold truncate flex items-center justify-between">
                  <span>{alert.title}</span>
                  <span className="text-[9px] font-mono text-slate-400">{alert.timestamp}</span>
                </div>
                <div className="text-[9px] text-slate-400 truncate mt-0.5">{alert.description}</div>
              </div>
            ))}
          </div>

          <div className="text-[9px] text-slate-400 pt-1 border-t border-slate-800/60 flex items-center justify-between font-mono">
            <span>Avg Delay: <strong className="text-cyan-400 font-normal">{metrics.avgWaitTime}s</strong></span>
            <span>CO2 Saved: <strong className="text-emerald-400 font-normal">{metrics.carbonEmissionsSavedKg.toFixed(1)}kg</strong></span>
          </div>
        </div>
      </div>

      {/* 3. IoT Sensor Network Map Overlay & Status */}
      <div className="bg-slate-950/95 border border-slate-800/90 rounded-xl p-3.5 shadow-xl space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
          <div className="flex items-center gap-2">
            <Radio className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-semibold text-slate-100 uppercase tracking-wider">
              IoT Sensor Network Map Overlay
            </h3>
          </div>
          <span className="text-[10px] text-slate-400 font-mono">
            {sensorNodes.filter((s) => s.status === 'active').length}/{sensorNodes.length} Online
          </span>
        </div>

        {/* 2D Intersection Radar / Satellite Overlay */}
        <div className="relative bg-slate-950 rounded-lg border border-slate-800 overflow-hidden flex items-center justify-center h-44">
          <svg
            className="w-full h-full absolute inset-0 opacity-40 pointer-events-none"
            viewBox="0 0 200 200"
          >
            <defs>
              <pattern id="radarGrid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#1e293b" strokeWidth="0.8" />
              </pattern>
            </defs>
            <rect width="200" height="200" fill="url(#radarGrid)" />

            {/* Roads */}
            <rect x="85" y="0" width="30" height="200" fill="#0f172a" stroke="#334155" strokeWidth="1" />
            <rect x="0" y="85" width="200" height="30" fill="#0f172a" stroke="#334155" strokeWidth="1" />
            <rect x="85" y="85" width="30" height="30" fill="#1e293b" />
            <line x1="85" y1="75" x2="115" y2="75" stroke="#94a3b8" strokeWidth="2" />
            <line x1="85" y1="125" x2="115" y2="125" stroke="#94a3b8" strokeWidth="2" />
            <line x1="75" y1="85" x2="75" y2="115" stroke="#94a3b8" strokeWidth="2" />
            <line x1="125" y1="85" x2="125" y2="115" stroke="#94a3b8" strokeWidth="2" />

            <circle cx="100" cy="100" r="35" fill="none" stroke="#0ea5e9" strokeWidth="0.5" strokeDasharray="3,3" />
            <circle cx="100" cy="100" r="70" fill="none" stroke="#0ea5e9" strokeWidth="0.5" strokeDasharray="4,4" />
          </svg>

          {/* Plotted Sensor Dots */}
          <div className="absolute inset-0">
            {filteredSensors.map((node) => {
              const colorClass =
                node.type === 'camera'
                  ? 'bg-rose-500 ring-rose-500/30'
                  : node.type === 'lidar'
                  ? 'bg-cyan-400 ring-cyan-400/30'
                  : node.type === 'loop'
                  ? 'bg-emerald-400 ring-emerald-400/30'
                  : 'bg-amber-400 ring-amber-400/30';

              return (
                <button
                  key={node.id}
                  onClick={() => setActiveSensor(node)}
                  style={{
                    left: `${node.position[0] * 100}%`,
                    top: `${node.position[1] * 100}%`,
                  }}
                  title={`${node.name} (${node.lastReading})`}
                  className={`absolute -translate-x-1/2 -translate-y-1/2 w-3.5 h-3.5 rounded-full ${colorClass} ring-4 transition-transform hover:scale-150 cursor-pointer shadow-lg`}
                />
              );
            })}
          </div>

          {/* Active Sensor Inspect Banner */}
          {activeSensor && (
            <div className="absolute bottom-2 left-2 right-2 bg-slate-900/95 border border-cyan-500/50 p-2 rounded text-[11px] flex items-center justify-between z-10 shadow-xl">
              <div>
                <div className="font-semibold text-cyan-300">{activeSensor.name}</div>
                <div className="text-[10px] text-slate-400">
                  Latency: {activeSensor.latencyMs}ms · Reading: {activeSensor.lastReading}
                </div>
              </div>
              <button
                onClick={() => setActiveSensor(null)}
                className="text-slate-400 hover:text-slate-200 text-xs px-1"
              >
                ✕
              </button>
            </div>
          )}

          {/* Map Controls */}
          <div className="absolute top-2 right-2 flex flex-col gap-1">
            <button
              onClick={() => setZoomLevel((z) => Math.min(1.5, z + 0.1))}
              className="w-6 h-6 rounded bg-slate-900/80 border border-slate-700 flex items-center justify-center text-slate-300 hover:text-cyan-400"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setZoomLevel((z) => Math.max(0.8, z - 0.1))}
              className="w-6 h-6 rounded bg-slate-900/80 border border-slate-700 flex items-center justify-center text-slate-300 hover:text-cyan-400"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Sensor Types Buttons Strip */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <button
            onClick={() => setSelectedSensorType(selectedSensorType === 'camera' ? 'all' : 'camera')}
            className={`p-2 rounded-lg border text-left transition-all ${
              selectedSensorType === 'camera' || selectedSensorType === 'all'
                ? 'bg-slate-900/90 border-slate-700'
                : 'bg-slate-900/30 border-transparent opacity-60'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 font-medium text-[11px]">
                <span className="w-2 h-2 rounded-full bg-rose-500" />
                Cameras (4K)
              </span>
              <span className="text-[9px] text-emerald-400 font-mono">98%</span>
            </div>
          </button>

          <button
            onClick={() => setSelectedSensorType(selectedSensorType === 'lidar' ? 'all' : 'lidar')}
            className={`p-2 rounded-lg border text-left transition-all ${
              selectedSensorType === 'lidar' || selectedSensorType === 'all'
                ? 'bg-slate-900/90 border-slate-700'
                : 'bg-slate-900/30 border-transparent opacity-60'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 font-medium text-[11px]">
                <span className="w-2 h-2 rounded-full bg-cyan-400" />
                LiDAR 360°
              </span>
              <span className="text-[9px] text-emerald-400 font-mono">99.4%</span>
            </div>
          </button>

          <button
            onClick={() => setSelectedSensorType(selectedSensorType === 'loop' ? 'all' : 'loop')}
            className={`p-2 rounded-lg border text-left transition-all ${
              selectedSensorType === 'loop' || selectedSensorType === 'all'
                ? 'bg-slate-900/90 border-slate-700'
                : 'bg-slate-900/30 border-transparent opacity-60'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 font-medium text-[11px]">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                Loop Detectors
              </span>
              <span className="text-[9px] text-emerald-400 font-mono">100%</span>
            </div>
          </button>

          <button
            onClick={() => setSelectedSensorType(selectedSensorType === 'rsu' ? 'all' : 'rsu')}
            className={`p-2 rounded-lg border text-left transition-all ${
              selectedSensorType === 'rsu' || selectedSensorType === 'all'
                ? 'bg-slate-900/90 border-slate-700'
                : 'bg-slate-900/30 border-transparent opacity-60'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 font-medium text-[11px]">
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                RSU (C-V2X)
              </span>
              <span className="text-[9px] text-emerald-400 font-mono">10Hz</span>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};
