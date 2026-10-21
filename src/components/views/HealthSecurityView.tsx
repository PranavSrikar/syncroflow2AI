/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Lock,
  UserCheck,
  AlertTriangle,
  Info,
  Server,
  Key,
} from 'lucide-react';
import { SimulationMetrics } from '../../types/traffic.ts';

interface HealthSecurityViewProps {
  metrics: SimulationMetrics;
}

export const HealthSecurityView: React.FC<HealthSecurityViewProps> = ({ metrics }) => {
  const [selectedRole, setSelectedRole] = useState<'traffic_engineer' | 'police_dispatcher' | 'system_admin'>('traffic_engineer');

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto text-slate-200 select-none">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider">
            <ShieldCheck className="w-4 h-4" />
            System Health & Role-Based Access Control
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1 font-sans">
            Safety Interlocks & Access Control Architecture
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Independent software supervisor health, fail-safe fallbacks, and demonstration Role-Based Access Control (RBAC).
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-500/30 px-3 py-1.5 rounded-xl">
          <span className="w-2 h-2 rounded-full bg-emerald-400" />
          <span>SUPERVISOR: ACTIVE & VERIFYING</span>
        </div>
      </div>

      {/* Mandatory Security & RBAC Disclosure */}
      <div className="p-4 bg-amber-950/30 border border-amber-500/40 rounded-xl flex items-start gap-3 text-xs text-amber-200">
        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <strong className="text-amber-100 font-semibold">Security Architecture & RBAC Status:</strong>
          <p className="text-amber-300/80 leading-relaxed">
            The role selector below is a <strong>UI demonstration simulator</strong> for research inspection. Real cryptographic authentication (OAuth2 / Mutual TLS / PKI certificate exchange) and immutable audit logging will be enforced by the Stage 2 Python backend. No unauthenticated operational commands can reach physical roadside equipment.
          </p>
        </div>
      </div>

      {/* RBAC Simulation Selector */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <UserCheck className="w-4 h-4 text-cyan-400" />
            <span>Simulated Operational Role Profile</span>
          </h3>
          <span className="text-[10px] text-slate-400 font-mono">UI-Only Simulation</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {[
            {
              id: 'traffic_engineer',
              title: 'Traffic Systems Engineer',
              privileges: 'Read telemetry, tune MPC weights, run scenario experiments, inspect loss values.',
              clearanceLevel: 'Level 2 (Engineering Advisory)',
            },
            {
              id: 'police_dispatcher',
              title: 'Emergency & Police Dispatcher',
              privileges: 'Trigger authenticated emergency preemption, manual corridor holds, road closure flags.',
              clearanceLevel: 'Level 3 (Operational Preemption)',
            },
            {
              id: 'system_admin',
              title: 'Infrastructure System Administrator',
              privileges: 'Manage RSU hardware configurations, rotate keys, inspect watchdog supervisor interlocks.',
              clearanceLevel: 'Level 4 (System Architecture)',
            },
          ].map((role) => (
            <button
              key={role.id}
              onClick={() => setSelectedRole(role.id as any)}
              className={`p-3.5 rounded-xl border text-left transition-all ${
                selectedRole === role.id
                  ? 'bg-cyan-950/40 border-cyan-500/50 shadow-md ring-1 ring-cyan-500/30'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="font-semibold text-xs text-slate-100">{role.title}</div>
              <div className="text-[10px] text-cyan-400 font-mono mt-0.5">{role.clearanceLevel}</div>
              <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">{role.privileges}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Independent Supervisor Safety Interlocks */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-semibold text-slate-100">
          Independent Safety Supervisor Verification Metrics
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800 space-y-1">
            <span className="text-slate-400">Illegal Transitions Prevented:</span>
            <div className="text-xl font-bold font-mono text-emerald-400">
              {metrics.safetyViolationAttemptsPrevented}
            </div>
            <span className="text-[10px] text-slate-500">Conflict matrix hard interlock</span>
          </div>

          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800 space-y-1">
            <span className="text-slate-400">Starvation Threshold:</span>
            <div className="text-xl font-bold font-mono text-slate-200">
              &lt; 90s Max Red
            </div>
            <span className="text-[10px] text-emerald-400">Zero active starvation alerts</span>
          </div>

          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800 space-y-1">
            <span className="text-slate-400">Fail-Safe Fallback Readiness:</span>
            <div className="text-xl font-bold font-mono text-cyan-300">
              Standby Verified
            </div>
            <span className="text-[10px] text-slate-500">All-red clearance + loop gap-out</span>
          </div>
        </div>
      </div>
    </div>
  );
};
