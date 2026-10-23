/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { ModelGuide } from '../live/ControllerIntelligence';
import { BookOpen, Calculator, CheckCircle2, ShieldCheck } from 'lucide-react';

export const MathematicalModelExplorer: React.FC = () => {
  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto text-slate-200 select-none">
      <div className="pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider">
          <BookOpen className="w-4 h-4" />
          Theoretical Formulations & Algorithmic Foundations
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1 font-sans">
          Mathematical Model Explorer
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Implemented backend models first; educational reference equations are available separately below.
        </p>
      </div>

      <ModelGuide />
      <details className="sf-reference-equations"><summary>Educational browser and theoretical reference formulations</summary><p>Reference examples only. The QP and unrestricted Max-Pressure formulations below are not executed by the current live backend. Example IDM parameters describe an illustrative browser model, not SUMO calibration.</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
        {/* Model 1: IDM Car-Following */}
        <div className="p-5 bg-slate-950/90 border border-slate-800 rounded-xl space-y-3">
          <h3 className="font-semibold text-slate-100 flex items-center gap-2">
            <Calculator className="w-4 h-4 text-cyan-400" />
            <span>1. Intelligent Driver Model (IDM) Kinematics</span>
          </h3>
          <pre className="p-3 bg-slate-900 rounded font-mono text-cyan-300 overflow-x-auto text-[11px]">
{`dv/dt = a * [ 1 - (v / v_0)^4 - (s*(v, Δv) / s)^2 ]

Where:
  s*(v, Δv) = s_0 + max(0, v*T + (v*Δv) / (2 * sqrt(a*b)))
  s_0 : minimum safe headway distance (2.5m)
  T   : safe time headway (1.4s)
  a   : maximum comfortable acceleration (1.8 m/s²)
  b   : comfortable deceleration (3.5 m/s²)`}
          </pre>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            Governs individual vehicle acceleration, deceleration, and braking as a function of current speed, distance to lead vehicle or stop line, and velocity differential.
          </p>
        </div>

        {/* Model 2: MPC Receding Horizon Optimization */}
        <div className="p-5 bg-slate-950/90 border border-slate-800 rounded-xl space-y-3">
          <h3 className="font-semibold text-slate-100 flex items-center gap-2">
            <Calculator className="w-4 h-4 text-emerald-400" />
            <span>2. Constrained MPC Quadratic Cost Function</span>
          </h3>
          <pre className="p-3 bg-slate-900 rounded font-mono text-emerald-300 overflow-x-auto text-[11px]">
{`min_g J = Σ_{k=1}^N [ w_q * ||q(k)||^2 + w_d * ||d(k)||^2 + w_s * ||Δg||^2 ]

Subject to:
  g_min ≤ g_p ≤ g_max  (∀ phase p)
  Σ_{p=1}^P g_p = C_cycle
  q(k+1) = q(k) + λ(k)*Δt - μ(k)*g(k)*Δt`}
          </pre>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            Evaluates 15-step predictive queue trajectories. The displayed QP is a theoretical reference. The actual backend enumerates finite cyclic timing candidates; see its implemented model above.
          </p>
        </div>

        {/* Model 3: Max-Pressure Dynamic Stability */}
        <div className="p-5 bg-slate-950/90 border border-slate-800 rounded-xl space-y-3">
          <h3 className="font-semibold text-slate-100 flex items-center gap-2">
            <Calculator className="w-4 h-4 text-amber-400" />
            <span>3. Max-Pressure Movement Score (Varaiya Model)</span>
          </h3>
          <pre className="p-3 bg-slate-900 rounded font-mono text-amber-300 overflow-x-auto text-[11px]">
{`Pressure P(m) = x_inbound(m) - Σ_l p_out(m, l) * x_outbound(l)

Phase Selection:
  S* = argmax_{S ∈ Phases} Σ_{m ∈ S} C(m) * P(m)`}
          </pre>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            This theoretical stability motivation requires assumptions not validated here. The implemented controller extends a legal cyclic phase and establishes no general throughput guarantee.
          </p>
        </div>

        {/* Model 4: Independent Safety Interlock */}
        <div className="p-5 bg-slate-950/90 border border-slate-800 rounded-xl space-y-3">
          <h3 className="font-semibold text-slate-100 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-rose-400" />
            <span>4. NEMA Conflict Matrix & Clearance Bounds</span>
          </h3>
          <pre className="p-3 bg-slate-900 rounded font-mono text-rose-300 overflow-x-auto text-[11px]">
{`Conflict Interlock:
  (G_NS_thru ∧ G_EW_thru) = FALSE
  (G_NS_left ∧ G_EW_thru) = FALSE
  (G_EW_left ∧ G_NS_thru) = FALSE

Mandatory Transition Intervals:
  t_yellow ≥ 3.5s (4.5s monsoon)
  t_allred ≥ 2.0s
  t_green  ≥ 7.0s (min-green guardrail)`}
          </pre>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            Deterministic software interlocks prevent conflicting movements, ensure yellow/all-red clearance intervals, and safeguard emergency preemption.
          </p>
        </div>
      </div>
      </details>
    </div>
  );
};
