/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import {
  Direction,
  IntersectionSignalState,
  ApproachTelemetry,
  CameraViewPreset,
  SimulationMetrics,
} from '../../types/traffic.ts';
import {
  Radio,
  Activity,
  Layers,
  Camera,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Siren,
  SlidersHorizontal,
} from 'lucide-react';

interface ViewportHUDProps {
  signals: IntersectionSignalState;
  telemetry: Record<Direction, ApproachTelemetry>;
  metrics: SimulationMetrics;
  cameraPreset: CameraViewPreset;
  onCameraChange: (preset: CameraViewPreset) => void;
  showAnalyticsOverlay: boolean;
  onToggleAnalyticsOverlay: () => void;
  onInjectEmergency: (dir: Direction) => void;
}

export const ViewportHUD: React.FC<ViewportHUDProps> = ({
  signals,
  telemetry,
  metrics,
  cameraPreset,
  onCameraChange,
  showAnalyticsOverlay,
  onToggleAnalyticsOverlay,
  onInjectEmergency,
}) => {
  const [selectedApproach, setSelectedApproach] = useState<Direction>('north');
  const [isTelemetryCollapsed, setIsTelemetryCollapsed] = useState(false);
  const [showV2IModal, setShowV2IModal] = useState(false);

  const activeAppTelemetry = telemetry[selectedApproach];

  return (
    <div className="absolute inset-0 pointer-events-none p-3.5 flex flex-col justify-between select-none">
      {/* Top HUD Row */}
      <div className="flex items-start justify-between gap-4">
        {/* Top-Left: V2I Communication Hardware Module (Matching Image 1) */}
        <div className="pointer-events-auto bg-slate-950/85 backdrop-blur-md border border-cyan-500/25 rounded-xl p-3 w-80 text-xs text-slate-200 shadow-xl">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <div className="font-semibold text-slate-100 flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5 text-cyan-400" />
              <span>V2I Communication Module</span>
            </div>
            <span className="font-mono text-[10px] text-cyan-400 bg-cyan-950/50 px-1.5 py-0.5 rounded border border-cyan-500/30">
              SC-INT-74
            </span>
          </div>

          {/* V2I Architecture Diagram */}
          <div className="py-2.5 grid grid-cols-3 gap-1.5 text-center text-[10px]">
            <div className="p-1.5 bg-slate-900/80 rounded border border-slate-800">
              <div className="text-slate-400">On-Board Unit</div>
              <div className="font-mono text-cyan-300 font-semibold mt-0.5">(OBU)</div>
              <div className="text-[9px] text-slate-400 mt-1">BSM 10Hz</div>
            </div>

            <div className="p-1.5 bg-cyan-950/40 rounded border border-cyan-500/40 relative">
              <div className="text-cyan-200">Roadside Unit</div>
              <div className="font-mono text-cyan-400 font-semibold mt-0.5">(RSU-74)</div>
              <div className="text-[9px] text-cyan-300 mt-1">MAP / SPaT</div>
            </div>

            <div className="p-1.5 bg-slate-900/80 rounded border border-slate-800">
              <div className="text-slate-400">Edge Controller</div>
              <div className="font-mono text-emerald-400 font-semibold mt-0.5">SynchroFlow</div>
              <div className="text-[9px] text-slate-400 mt-1">MPC + MAPPO</div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-1 text-[11px] text-slate-400 border-t border-slate-900">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span>V2I Status: <strong className="text-emerald-400 font-normal">Active</strong></span>
            </span>
            <span>Latency: <strong className="text-cyan-400 font-mono font-normal">12ms</strong></span>
          </div>
        </div>

        {/* Top-Center: Approach Status Breakdown (Matching Image 1) */}
        <div className="pointer-events-auto bg-slate-950/85 backdrop-blur-md border border-slate-800 rounded-xl px-4 py-2 shadow-xl flex items-center gap-6 text-xs">
          <div>
            <div className="text-[10px] text-slate-400 font-medium">Oak St. (N/S)</div>
            <div className="font-mono text-slate-200 flex items-center gap-2 mt-0.5">
              <span className="text-rose-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                {signals.approachSignals.north.through === 'red' ? `${Math.round(signals.approachSignals.north.remainingGreen || 42)}s` : 'STOP'}
              </span>
              <span className="text-slate-600">/</span>
              <span className="text-emerald-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                {signals.approachSignals.north.through === 'green' ? `${Math.round(signals.approachSignals.north.remainingGreen)}s left` : 'WAIT'}
              </span>
            </div>
          </div>

          <div className="h-6 w-px bg-slate-800" />

          <div>
            <div className="text-[10px] text-slate-400 font-medium">5th Ave. (E/W)</div>
            <div className="font-mono text-slate-200 flex items-center gap-2 mt-0.5">
              <span className="text-emerald-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                {signals.approachSignals.east.through === 'green' ? `${Math.round(signals.approachSignals.east.remainingGreen)}s left` : 'WAIT'}
              </span>
              <span className="text-slate-600">/</span>
              <span className="text-cyan-400">
                {telemetry.east.queuedVehicles + telemetry.west.queuedVehicles} queued
              </span>
            </div>
          </div>

          {signals.isPreemptActive && (
            <div className="bg-rose-500/20 border border-rose-500/50 px-2.5 py-1 rounded-lg flex items-center gap-1.5 text-rose-300 font-medium text-[11px]">
              <Siren className="w-3.5 h-3.5 text-rose-400 animate-bounce" />
              <span>PREEMPTION ACTIVE</span>
            </div>
          )}
        </div>

        {/* Top-Right: Camera Presets & Adaptive Controller Card (Matching Image 1) */}
        <div className="pointer-events-auto space-y-2">
          {/* Camera View Switcher Pills */}
          <div className="bg-slate-950/85 backdrop-blur-md border border-slate-800 rounded-xl p-1 flex items-center gap-1 text-xs shadow-xl">
            {(
              [
                { id: 'aerial', label: 'AERIAL' },
                { id: 'street', label: 'STREET' },
                { id: 'top_down', label: 'TOP DOWN' },
              ] as const
            ).map((cam) => (
              <button
                key={cam.id}
                onClick={() => onCameraChange(cam.id)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all ${
                  cameraPreset === cam.id
                    ? 'bg-cyan-500 text-slate-950 shadow-sm font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                {cam.label}
              </button>
            ))}

            <button
              onClick={onToggleAnalyticsOverlay}
              title="Toggle 3D Analytics Trajectories"
              className={`p-1.5 rounded-lg border transition-colors ${
                showAnalyticsOverlay
                  ? 'bg-cyan-950/50 border-cyan-500/40 text-cyan-400'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Adaptive Signal Control Metrics Dashboard */}
          <div className="bg-slate-950/85 backdrop-blur-md border border-slate-800 rounded-xl p-3 w-80 text-xs text-slate-200 shadow-xl">
            <div className="flex items-center justify-between pb-1.5 border-b border-slate-800 text-[11px]">
              <span className="font-semibold text-slate-100 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-cyan-400" />
                Adaptive Traffic Signal Dashboard
              </span>
              <span className="font-mono text-slate-400">112s Cycle</span>
            </div>

            <div className="grid grid-cols-2 gap-2 py-2 text-[11px]">
              <div>
                <span className="text-slate-400 text-[10px]">Current Phase</span>
                <div className="font-mono font-semibold text-cyan-300 mt-0.5 truncate">
                  Phase {signals.currentPhaseIndex + 1} → {signals.nextPhaseIndex + 1}
                </div>
              </div>
              <div className="text-right">
                <span className="text-slate-400 text-[10px]">Intersection Occupancy</span>
                <div className="font-mono font-semibold text-emerald-400 mt-0.5">
                  {metrics.intersectionOccupancy}%
                </div>
              </div>
            </div>

            {/* Queue Lengths Live Curve SVG */}
            <div className="pt-1 border-t border-slate-900">
              <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                <span>Approach Queue Distribution</span>
                <span className="font-mono text-cyan-400">{metrics.totalQueueLength} vehicles</span>
              </div>
              <svg className="w-full h-9 stroke-cyan-400 fill-cyan-500/10" viewBox="0 0 200 40">
                <polyline
                  fill="none"
                  strokeWidth="2"
                  points="0,30 25,28 50,18 75,10 100,12 125,22 150,26 175,16 200,20"
                />
                <circle cx="75" cy="10" r="3" fill="#00f2fe" />
                <circle cx="100" cy="12" r="3" fill="#10b981" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Middle HUD: Left Telemetry Flyout Drawer (Matching Image 2) */}
      <div className="pointer-events-auto flex items-start">
        <div className="bg-slate-950/90 backdrop-blur-md border border-slate-800 rounded-xl p-3 w-72 text-xs shadow-xl space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="font-semibold text-slate-200 text-xs flex items-center gap-1.5">
              <span>APPROACH TELEMETRY</span>
            </div>
            {/* Approach Selector Pills */}
            <div className="flex items-center gap-1 bg-slate-900 p-0.5 rounded-lg border border-slate-800">
              {(['north', 'south', 'east', 'west'] as Direction[]).map((d) => (
                <button
                  key={d}
                  onClick={() => setSelectedApproach(d)}
                  className={`w-5 h-5 rounded text-[10px] font-bold font-mono transition-colors ${
                    selectedApproach === d
                      ? 'bg-cyan-500 text-slate-950'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {d[0].toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-1.5 text-[11px]">
            {/* Through Lane */}
            <div className="p-2 bg-slate-900/60 rounded-lg border border-slate-800/80 flex items-center justify-between">
              <div>
                <div className="text-slate-300 font-medium flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                  THROUGH
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  Discharge: <span className="font-mono text-slate-300">{activeAppTelemetry.dischargeRate} v/s</span> · Max-P: <span className="font-mono text-cyan-400">{activeAppTelemetry.maxPressureScore}</span>
                </div>
              </div>
              <div className="font-mono font-bold text-sm text-cyan-300">
                {activeAppTelemetry.laneQueues.through} <span className="text-[10px] font-normal text-slate-400">queued</span>
              </div>
            </div>

            {/* Left Lane */}
            <div className="p-2 bg-slate-900/60 rounded-lg border border-slate-800/80 flex items-center justify-between">
              <div>
                <div className="text-slate-300 font-medium flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  PROTECTED LEFT
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  Discharge: <span className="font-mono text-slate-300">0.52 v/s</span> · Max-P: <span className="font-mono text-amber-400">8.4</span>
                </div>
              </div>
              <div className="font-mono font-bold text-sm text-amber-300">
                {activeAppTelemetry.laneQueues.left} <span className="text-[10px] font-normal text-slate-400">queued</span>
              </div>
            </div>

            {/* Right Lane */}
            <div className="p-2 bg-slate-900/60 rounded-lg border border-slate-800/80 flex items-center justify-between">
              <div>
                <div className="text-slate-300 font-medium flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  RIGHT TURN / SLIP
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  Discharge: <span className="font-mono text-slate-300">0.48 v/s</span> · Free-flow slip
                </div>
              </div>
              <div className="font-mono font-bold text-sm text-emerald-300">
                {activeAppTelemetry.laneQueues.right} <span className="text-[10px] font-normal text-slate-400">queued</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Center-Bottom Floating Badge (Matching Image 1) */}
      <div className="flex items-center justify-center pointer-events-none pb-1">
        <div className="pointer-events-auto bg-slate-950/90 backdrop-blur-md border border-cyan-500/30 rounded-full px-5 py-1.5 text-xs text-slate-300 shadow-2xl flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="text-slate-400">Digital Twin</span>
            <strong className="font-mono text-rose-400 font-medium">ID. SC-INT-74</strong>
          </span>
          <span className="text-slate-600">|</span>
          <span className="flex items-center gap-1.5">
            <span className="text-slate-400">V2I Status:</span>
            <strong className="text-emerald-400 font-medium">Active (DSRC)</strong>
          </span>
          <span className="text-slate-600">|</span>
          <span className="flex items-center gap-1.5">
            <span className="text-slate-400">Occupancy:</span>
            <strong className="font-mono text-cyan-300 font-medium">{metrics.intersectionOccupancy}%</strong>
          </span>
          <span className="text-slate-600">|</span>
          <span className="flex items-center gap-1.5">
            <span className="text-slate-400">Latency:</span>
            <strong className="font-mono text-slate-200 font-medium">12ms</strong>
          </span>
        </div>
      </div>
    </div>
  );
};
