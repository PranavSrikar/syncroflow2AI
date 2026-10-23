/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { Camera, Radio, CheckCircle2, AlertTriangle, Eye, ShieldCheck } from 'lucide-react';
import { IoTSensorNode } from '../../types/traffic.ts';

interface PerceptionCameraViewProps {
  sensors: IoTSensorNode[];
}

export const PerceptionCameraView: React.FC<PerceptionCameraViewProps> = ({ sensors }) => {
  const cameras = sensors.filter((s) => s.type === 'camera');
  const lidar = sensors.filter((s) => s.type === 'lidar');

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto text-slate-200 select-none">
      <div className="pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider">
          <Camera className="w-4 h-4" />
          Sensor Perception & Computer Vision Feeds
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1 font-sans">
          Optical & Solid-State LiDAR Perception Center
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Synthetic sensor model and fixed illustrative bounding boxes. For real recorded-video detection use the live SUMO workspace Sensor Perception page.
        </p>
      </div>

      {/* Optical PTZ Cameras Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {cameras.map((cam) => (
          <div key={cam.id} className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Camera className="w-4 h-4 text-rose-400" />
                <h3 className="text-xs font-semibold text-slate-100">{cam.name}</h3>
              </div>
              <span className="text-[10px] text-emerald-400 font-mono bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-500/30">
                {cam.coveragePct}% CONFIDENCE
              </span>
            </div>

            {/* Simulated 4K Perception Bounding Box Frame */}
            <div className="relative h-40 bg-slate-900 rounded-lg border border-slate-800 overflow-hidden flex items-center justify-center">
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent pointer-events-none" />
              <div className="text-center space-y-1">
                <Eye className="w-6 h-6 text-slate-600 mx-auto" />
                <div className="text-xs font-mono text-slate-400">Mock bounding-box illustration</div>
                <div className="text-[10px] text-cyan-400 font-mono">Stream: {cam.lastReading} · Latency: {cam.latencyMs}ms</div>
              </div>

              {/* Bounding box overlays */}
              <div className="absolute top-6 left-12 w-20 h-14 border border-cyan-400/80 bg-cyan-500/10 rounded flex items-start p-1">
                <span className="text-[8px] font-mono text-cyan-300">car 0.94</span>
              </div>
              <div className="absolute bottom-8 right-16 w-28 h-18 border border-amber-400/80 bg-amber-500/10 rounded flex items-start p-1">
                <span className="text-[8px] font-mono text-amber-300">bus 0.98</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
