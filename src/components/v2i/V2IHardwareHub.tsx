/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import {
  Radio,
  Cpu,
  Camera,
  Layers,
  Activity,
  CheckCircle2,
  AlertCircle,
  Wifi,
  ShieldCheck,
  Server,
} from 'lucide-react';
import { IoTSensorNode, IntersectionSignalState } from '../../types/traffic.ts';

interface V2IHardwareHubProps {
  sensors: IoTSensorNode[];
  signals: IntersectionSignalState;
}

export const V2IHardwareHub: React.FC<V2IHardwareHubProps> = ({ sensors, signals }) => {
  const [selectedProtocol, setSelectedProtocol] = useState<'spat' | 'map' | 'bsm'>('spat');

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto text-slate-200 select-none">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider">
            <Radio className="w-4 h-4" />
            Vehicle-to-Infrastructure (V2I) Telematics Hub
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1 font-sans">
            Edge Hardware & Connected Vehicle Protocol Stream
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time DSRC / C-V2X roadside telematics broadcasting SAE J2735 SPaT, MAP, and BSM telemetry messages to connected vehicles.
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-500/30 px-3 py-1.5 rounded-xl">
          <span className="w-2 h-2 rounded-full bg-emerald-400" />
          <span>RSU SC-INT-74: ONLINE (12ms)</span>
        </div>
      </div>

      {/* Hardware Architecture Diagram */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Unit 1: Roadside Unit (RSU) */}
        <div className="p-5 bg-slate-950/80 border border-cyan-500/30 rounded-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                <Radio className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-xs font-semibold text-slate-100">Roadside Unit (RSU)</h3>
                <span className="text-[10px] text-cyan-400 font-mono">SC-INT-74</span>
              </div>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 border border-emerald-500/40 text-emerald-400 font-mono">
              ACTIVE
            </span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Dual-band DSRC 5.9 GHz and 3GPP Rel-16 C-V2X transceiver mounted on corner mast arm. Broadcasts intersection geometry (MAP) and signal timing (SPaT).
          </p>

          <div className="text-xs space-y-1.5 pt-2 border-t border-slate-900 font-mono text-[11px]">
            <div className="flex justify-between text-slate-400">
              <span>Coverage Radius:</span>
              <span className="text-slate-200">350 meters</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Broadcast Frequency:</span>
              <span className="text-cyan-400">10 Hz (100ms)</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Security Credential:</span>
              <span className="text-emerald-400">SCMS IEEE 1609.2</span>
            </div>
          </div>
        </div>

        {/* Unit 2: Smart Edge Traffic Controller */}
        <div className="p-5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <Cpu className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-xs font-semibold text-slate-100">Edge Controller Cabinet</h3>
                <span className="text-[10px] text-slate-400 font-mono">SynchroFlow Edge-X86</span>
              </div>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 border border-emerald-500/40 text-emerald-400 font-mono">
              SYNCHRONIZED
            </span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Ruggedized roadside industrial computer running real-time MPC optimization and MAPPO RL model inference with NEMA TS-2 hardware interface.
          </p>

          <div className="text-xs space-y-1.5 pt-2 border-t border-slate-900 font-mono text-[11px]">
            <div className="flex justify-between text-slate-400">
              <span>Inference Time:</span>
              <span className="text-cyan-400">12ms avg</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Fail-Safe Mode:</span>
              <span className="text-slate-200">Watchdog Loop Fallback</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Hardware Standard:</span>
              <span className="text-slate-200">NEMA TS-2 Type 1</span>
            </div>
          </div>
        </div>

        {/* Unit 3: On-Board Unit (OBU) & Vehicle Interconnect */}
        <div className="p-5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                <Wifi className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-xs font-semibold text-slate-100">Vehicle OBU Fleet</h3>
                <span className="text-[10px] text-slate-400 font-mono">Connected Transceivers</span>
              </div>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950 border border-cyan-500/40 text-cyan-400 font-mono">
              36 UNITS
            </span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Transmits Basic Safety Messages (BSM) containing GNSS positioning, kinematic speed, heading, and emergency vehicle status priority flags.
          </p>

          <div className="text-xs space-y-1.5 pt-2 border-t border-slate-900 font-mono text-[11px]">
            <div className="flex justify-between text-slate-400">
              <span>Speed Advisory (GLOSA):</span>
              <span className="text-emerald-400">48 km/h optimal</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Emergency Preemption:</span>
              <span className="text-rose-400">Level-1 EVP Active</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Packet Reception:</span>
              <span className="text-cyan-400">99.8% Success</span>
            </div>
          </div>
        </div>
      </div>

      {/* Protocol Payload Inspector */}
      <div className="bg-slate-950/90 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-semibold text-slate-100">
              SAE J2735 Telematics Message Inspector
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Live broadcast data payload transmitted over air to approaching connected vehicles.
            </p>
          </div>

          <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs">
            {(['spat', 'map', 'bsm'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setSelectedProtocol(p)}
                className={`px-3 py-1 rounded font-mono uppercase font-semibold transition-colors ${
                  selectedProtocol === p
                    ? 'bg-cyan-500 text-slate-950'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* JSON Payload Display */}
        <pre className="p-4 bg-slate-900/80 border border-slate-800 rounded-lg text-xs font-mono text-cyan-300 overflow-x-auto leading-relaxed">
          {selectedProtocol === 'spat' &&
            JSON.stringify(
              {
                messageType: 'SPaT (Signal Phase and Timing)',
                standard: 'SAE J2735_202007',
                intersectionId: 'SC-INT-74',
                timestamp: new Date().toISOString(),
                status: 'operational',
                currentPhase: signals.currentPhaseIndex + 1,
                phaseName: signals.phaseName,
                remainingGreenSeconds: Math.round(signals.approachSignals.north.remainingGreen || 0),
                allRedClearanceDuration: 2.0,
                yellowDuration: 3.5,
                GLOSA_speedAdvisory_kmh: 46.5,
                emergencyPreemptionActive: signals.isPreemptActive,
              },
              null,
              2
            )}

          {selectedProtocol === 'map' &&
            JSON.stringify(
              {
                messageType: 'MAP (Intersection Geometry)',
                intersectionId: 'SC-INT-74',
                name: 'Oak Street & 5th Avenue',
                referencePoint: { latitude: 37.774929, longitude: -122.419416, elevationMeters: 16.4 },
                approaches: [
                  { id: 1, direction: 'North', lanes: 3, speedLimitKmH: 50 },
                  { id: 2, direction: 'South', lanes: 3, speedLimitKmH: 50 },
                  { id: 3, direction: 'East', lanes: 3, speedLimitKmH: 50 },
                  { id: 4, direction: 'West', lanes: 3, speedLimitKmH: 50 },
                ],
              },
              null,
              2
            )}

          {selectedProtocol === 'bsm' &&
            JSON.stringify(
              {
                messageType: 'BSM (Basic Safety Message Part I & II)',
                temporaryId: 'OBU-VEH-084',
                transmissionCount: 1420,
                speedKmh: 42.4,
                headingDegrees: 180.0,
                acceleration_m_s2: 0.12,
                steeringWheelAngle: 0.0,
                emergencyVehicleAlert: {
                  sirenActive: signals.isPreemptActive,
                  lightbarActive: signals.isPreemptActive,
                  priorityRequest: signals.isPreemptActive ? 'Level_1_Medical' : 'None',
                },
              },
              null,
              2
            )}
        </pre>
      </div>

      {/* Sensor Ingestion Health Table */}
      <div className="bg-slate-950/90 border border-slate-800 rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-semibold text-slate-100">
          Connected Sensor Node Health & Latency Table
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead className="bg-slate-900/60 text-slate-400 font-mono text-[10px] uppercase border-b border-slate-800">
              <tr>
                <th className="p-3">Sensor Identifier</th>
                <th className="p-3">Modality Type</th>
                <th className="p-3">Assigned Approach</th>
                <th className="p-3">Operational Status</th>
                <th className="p-3">Telemetry Reading</th>
                <th className="p-3">Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
              {sensors.map((s) => (
                <tr key={s.id} className="hover:bg-slate-900/40 transition-colors">
                  <td className="p-3 font-semibold text-slate-200">{s.id}</td>
                  <td className="p-3 text-cyan-400 uppercase">{s.type}</td>
                  <td className="p-3 text-slate-300 uppercase">{s.assignedApproach}</td>
                  <td className="p-3">
                    <span className="text-emerald-400 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      {s.status}
                    </span>
                  </td>
                  <td className="p-3 text-slate-400">{s.lastReading}</td>
                  <td className="p-3 text-cyan-300">{s.latencyMs}ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
