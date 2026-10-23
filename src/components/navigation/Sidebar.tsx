/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import {
  LayoutDashboard,
  FlaskConical,
  LineChart,
  Scale,
  TrendingUp,
  Network,
  ShieldCheck,
  Radio,
  Camera,
  Users,
  Siren,
  BookOpen,
  Server,
  Download,
  Cpu,
  RefreshCw,
} from 'lucide-react';

export type NavTab =
  | 'dashboard'
  | 'scenarios'
  | 'comparison'
  | 'analytics'
  | 'prediction'
  | 'network'
  | 'math_models'
  | 'v2i_hardware'
  | 'perception'
  | 'pedestrian'
  | 'incidents'
  | 'health_security'
  | 'config_api'
  | 'benchmark_export';

interface SidebarProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  controllerName: string;
  isSimulating: boolean;
  onResetSim: () => void;
  liveMode?: boolean;
  resetDisabled?: boolean;
  supervisorStatus?: string;
}

interface NavCategory {
  category: string;
  items: {
    id: NavTab;
    label: string;
    icon: React.ReactNode;
    desc: string;
  }[];
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  controllerName,
  isSimulating,
  onResetSim,
  liveMode, supervisorStatus, resetDisabled,
}) => {
  const navCategories: NavCategory[] = [
    {
      category: 'Monitor traffic',
      items: [
        {
          id: 'dashboard',
          label: 'Digital Twin Command',
          icon: <LayoutDashboard className="w-4 h-4" />,
          desc: '3D viewport & telemetry column',
        },
        {
          id: 'scenarios',
          label: 'Scenario Laboratory',
          icon: <FlaskConical className="w-4 h-4" />,
          desc: 'All 25 stress scenarios & PRNG seeds',
        },
        {
          id: 'comparison',
          label: 'Controller Benchmark Lab',
          icon: <Scale className="w-4 h-4" />,
          desc: '7 canonical controllers comparison',
        },
      ],
    },
    {
      category: 'Understand & analyze',
      items: [
        {
          id: 'analytics',
          label: 'Analytics & Explainable AI',
          icon: <LineChart className="w-4 h-4" />,
          desc: 'Empirical wait times, P95 & throughput',
        },
        {
          id: 'prediction',
          label: 'Traffic Prediction Center',
          icon: <TrendingUp className="w-4 h-4" />,
          desc: 'Rolling Poisson demand forecasts',
        },
        {
          id: 'network',
          label: 'Network Coordination',
          icon: <Network className="w-4 h-4" />,
          desc: 'Live A0/B0 or demo corridor',
        },
        {
          id: 'math_models',
          label: 'Mathematical Model Explorer',
          icon: <BookOpen className="w-4 h-4" />,
          desc: 'IDM kinematics & MPC formulations',
        },
      ],
    },
    {
      category: 'Safety & observations',
      items: [
        {
          id: 'v2i_hardware',
          label: 'V2I & Sensor Architecture',
          icon: <Radio className="w-4 h-4" />,
          desc: 'DSRC/C-V2X RSU, OBU & SPaT streams',
        },
        {
          id: 'perception',
          label: 'Sensor Perception & LiDAR',
          icon: <Camera className="w-4 h-4" />,
          desc: 'Camera telemetry & bounding boxes',
        },
        {
          id: 'pedestrian',
          label: 'Pedestrian Actuation',
          icon: <Users className="w-4 h-4" />,
          desc: 'Pushbutton calls & crosswalk walk safety',
        },
        {
          id: 'incidents',
          label: 'Incident & Preemption Hub',
          icon: <Siren className="w-4 h-4" />,
          desc: 'Emergency clearance & staged transitions',
        },
        {
          id: 'health_security',
          label: 'Safety Supervisor & RBAC',
          icon: <ShieldCheck className="w-4 h-4" />,
          desc: 'Research safety status; no certification',
        },
      ],
    },
    {
      category: 'System & data',
      items: [
        {
          id: 'config_api',
          label: 'Provider & Remote API Config',
          icon: <Server className="w-4 h-4" />,
          desc: 'Local PRNG vs WebSocket backend switcher',
        },
        {
          id: 'benchmark_export',
          label: 'Scientific Data Export',
          icon: <Download className="w-4 h-4" />,
          desc: 'Reproducible experiment JSON exporter',
        },
      ],
    },
  ];

  const byId = new Map(navCategories.flatMap(group=>group.items).map(item=>[item.id,item]));
  const organized: NavCategory[] = [
    { category: 'Monitor', items: ['dashboard','network'].map(id=>byId.get(id as NavTab)!) },
    { category: 'Intelligence', items: ['analytics','prediction','math_models'].map(id=>byId.get(id as NavTab)!) },
    { category: 'Safety & perception', items: ['perception','pedestrian','incidents','health_security'].map(id=>byId.get(id as NavTab)!) },
    { category: 'Research lab', items: ['scenarios','comparison','v2i_hardware'].map(id=>byId.get(id as NavTab)!) },
    { category: 'System & data', items: ['config_api','benchmark_export'].map(id=>byId.get(id as NavTab)!) },
  ];
  return (
    <aside className="sf-sidebar w-64 bg-slate-950/95 border-r border-slate-800/80 flex flex-col shrink-0 z-30 select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <div className="text-sm font-bold tracking-tight text-slate-100 font-sans flex items-center gap-1.5">
              SYNCHROFLOW <span className="text-cyan-400 font-mono text-xs">AI</span>
            </div>
            <div className="text-[10px] text-slate-400 font-mono tracking-wide">
              {liveMode ? 'SUMO / TraCI' : 'BROWSER DEMONSTRATION'}
            </div>
          </div>
        </div>

        <button
          disabled={resetDisabled}
          onClick={onResetSim}
          title={liveMode ? 'Stop and restart SUMO in the live workspace' : 'Reset Synthetic Demonstration Clock'}
          className="p-1.5 text-slate-400 hover:text-cyan-400 hover:bg-slate-900 rounded-md transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Navigation Links Grouped by Category */}
      <nav className="flex-1 p-3 space-y-4 overflow-y-auto">
        {organized.map((group) => (
          <div key={group.category} className="space-y-1">
            <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-2 py-0.5">
              {group.category}
            </div>
            {group.items.map((item) => {
              const isActive = activeTab === item.id;
              const liveLabels: Partial<Record<NavTab,string>> = { dashboard: 'Live Traffic Command', analytics: 'Traffic Analytics', prediction: 'Traffic Predictions', math_models: 'Controller Intelligence', perception: 'Camera & Sensor Monitoring', pedestrian: 'Pedestrian Protection', incidents: 'Emergency Management', health_security: 'System Health & Safety', config_api: 'System Settings' };
              const label = liveMode ? liveLabels[item.id] ?? item.label : item.label;
              return (
                <button
                  key={item.id}
                  data-nav={item.id}
                  aria-current={isActive ? 'page' : undefined}
                  title={label + ' — ' + item.desc}
                  onClick={() => onTabChange(item.id)}
                  className={`w-full text-left p-2 rounded-lg transition-all flex items-start gap-2.5 ${
                    isActive
                      ? 'bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
                  }`}
                >
                  <div className={`mt-0.5 shrink-0 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`}>
                    {item.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium truncate">{label}</div>
                    <div className="text-[10px] text-slate-400 truncate leading-tight">
                      {item.desc}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        ))}

        {/* Intersection Location Spec */}
        <div className="pt-2 px-1">
          <div className="p-3 bg-slate-900/70 border border-slate-800 rounded-lg space-y-1.5 text-[11px]">
            <div className="text-slate-200 font-medium">{liveMode ? 'SUMO research scenario' : 'Synthetic Oak Street'}</div>
            <div className="text-slate-400 text-[10px] flex items-center justify-between">
              <span>Layout</span>
              <span className="font-mono text-cyan-400">4-Arm Dual Ring</span>
            </div>
            <div className="text-slate-400 text-[10px] flex items-center justify-between">
              <span>Controller</span>
              <span className="font-mono text-emerald-400 truncate max-w-[90px]">{controllerName}</span>
            </div>
          </div>
        </div>
      </nav>

      {/* Footer System Status */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-950 text-[11px] space-y-1.5">
        <div className="flex items-center justify-between text-slate-400 text-[10px]">
          <span>Safety status</span>
          <span className="font-mono text-emerald-400 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
            {supervisorStatus ?? 'unavailable'}
          </span>
        </div>
        <div className="flex items-center justify-between text-slate-400 text-[10px]">
          <span>Data source</span>
          <span className="font-mono text-cyan-400">{liveMode ? 'Backend telemetry stream' : 'Browser simulation ticks'}</span>
        </div>
        <div className="pt-1 border-t border-slate-900 flex items-center justify-between text-[10px] text-slate-400">
          <span>Frontend Architecture</span>
          <span className="font-mono text-slate-400">Research prototype</span>
        </div>
      </div>
    </aside>
  );
};
