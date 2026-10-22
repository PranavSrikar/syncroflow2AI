/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { TrafficSimulationEngine, SimulationState } from './simulation/engine.ts';
import { trafficProvider } from './services/trafficProvider.ts';
import { Sidebar, NavTab } from './components/navigation/Sidebar.tsx';
import { OverviewCommandCenter } from './components/views/OverviewCommandCenter.tsx';
import { SumoLiveView } from './components/views/SumoLiveView.tsx';
import { ScenarioLabView } from './components/views/ScenarioLabView.tsx';
import { AnalyticsView } from './components/views/AnalyticsView.tsx';
import { ComparisonLabView } from './components/views/ComparisonLabView.tsx';
import { PredictionCenterView } from './components/views/PredictionCenterView.tsx';
import { NetworkCoordinationView } from './components/views/NetworkCoordinationView.tsx';
import { HealthSecurityView } from './components/views/HealthSecurityView.tsx';
import { ConfigApiView } from './components/views/ConfigApiView.tsx';
import { MathematicalModelExplorer } from './components/views/MathematicalModelExplorer.tsx';
import { V2IHardwareHub } from './components/v2i/V2IHardwareHub.tsx';
import { IncidentEmergencyView } from './components/views/IncidentEmergencyView.tsx';
import { PerceptionCameraView } from './components/views/PerceptionCameraView.tsx';
import { PedestrianCrossingView } from './components/views/PedestrianCrossingView.tsx';
import { BenchmarkExportView } from './components/views/BenchmarkExportView.tsx';
import {
  Direction,
  ControllerType,
  WeatherMode,
  CameraViewPreset,
  TrafficScenario,
} from './types/traffic.ts';
import { Siren, Activity, ShieldCheck } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<NavTab>('dashboard');
  const [sumoMode, setSumoMode] = useState(true);
  const engineRef = useRef<TrafficSimulationEngine>(trafficProvider.getEngine());

  // React state synchronized from provider & engine
  const [simState, setSimState] = useState<SimulationState>(engineRef.current.getState());
  const [showAnalyticsOverlay, setShowAnalyticsOverlay] = useState(true);

  // Subscribe to provider state updates
  useEffect(() => {
    const unsubscribe = trafficProvider.subscribe((latestState) => {
      setSimState(latestState);
    });
    return () => unsubscribe();
  }, []);

  // Main simulation tick loop
  useEffect(() => {
    let animId = 0;
    let lastTime = performance.now();
    let stateThrottle = 0;

    const tick = (now: number) => {
      animId = requestAnimationFrame(tick);
      const dt = Math.min(0.1, (now - lastTime) / 1000);
      lastTime = now;

      const engine = engineRef.current;
      if (!engine) return;

      const state = engine.getState();
      if (state.isRunning && trafficProvider.getMode() === 'local_demo') {
        engine.step(dt);
      }

      // Synchronize state at ~20Hz
      stateThrottle += dt;
      if (stateThrottle >= 0.05) {
        stateThrottle = 0;
        trafficProvider.notifySubscribers(engine.getState());
      }
    };

    animId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animId);
  }, []);

  // Simulation Control Handlers
  const handleTogglePlay = useCallback(() => {
    const currentState = engineRef.current.getState();
    engineRef.current.setPlaying(!currentState.isRunning);
    trafficProvider.notifySubscribers(engineRef.current.getState());
  }, []);

  const handleStep = useCallback(() => {
    engineRef.current.step(0.5);
    trafficProvider.notifySubscribers(engineRef.current.getState());
  }, []);

  const handleReset = useCallback(() => {
    engineRef.current.reset();
    trafficProvider.notifySubscribers(engineRef.current.getState());
  }, []);

  const handleSetSpeed = useCallback((speed: number) => {
    engineRef.current.setSpeed(speed);
    trafficProvider.notifySubscribers(engineRef.current.getState());
  }, []);

  const handleSetWeather = useCallback((weather: WeatherMode) => {
    engineRef.current.setWeather(weather);
    trafficProvider.notifySubscribers(engineRef.current.getState());
  }, []);

  const handleCameraChange = useCallback((preset: CameraViewPreset) => {
    engineRef.current.setCameraPreset(preset);
    trafficProvider.notifySubscribers(engineRef.current.getState());
  }, []);

  const handleInjectAmbulance = useCallback((dir: Direction) => {
    engineRef.current.injectEmergency(dir, 'ambulance');
    trafficProvider.notifySubscribers(engineRef.current.getState());
  }, []);

  const handleInjectFireEngine = useCallback((dir: Direction) => {
    engineRef.current.injectEmergency(dir, 'fire_engine');
    trafficProvider.notifySubscribers(engineRef.current.getState());
  }, []);

  const handleSelectScenario = useCallback((scenarioId: string) => {
    engineRef.current.loadScenario(scenarioId);
    trafficProvider.notifySubscribers(engineRef.current.getState());
  }, []);

  const handleChangeController = useCallback((controller: ControllerType) => {
    engineRef.current.setController(controller);
    trafficProvider.notifySubscribers(engineRef.current.getState());
  }, []);

  const handleSetSeed = useCallback((newSeed: number) => {
    engineRef.current.setSeed(newSeed);
    trafficProvider.notifySubscribers(engineRef.current.getState());
  }, []);

  const handleCustomScenarioApply = useCallback((scenario: TrafficScenario) => {
    engineRef.current.loadScenario(scenario.id);
    trafficProvider.notifySubscribers(engineRef.current.getState());
  }, []);

  const controllerDisplayName =
    simState.controllerType === 'synchroflow_hybrid'
      ? 'SynchroFlow Hybrid'
      : simState.controllerType === 'mappo_assisted_mpc'
      ? 'SynchroFlow (MAPPO+MPC)'
      : simState.controllerType === 'mpc_only'
      ? 'Receding-Horizon MPC'
      : simState.controllerType === 'max_pressure'
      ? 'Max-Pressure'
      : simState.controllerType === 'actuated'
      ? 'Semi-Actuated'
      : simState.controllerType === 'queue_adaptive'
      ? 'Queue-Adaptive'
      : 'Fixed-Time';

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans antialiased">
      {/* Sidebar Navigation across all 14 modules */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        controllerName={sumoMode ? 'SUMO telemetry' : controllerDisplayName}
        isSimulating={!sumoMode && simState.isRunning}
        onResetSim={handleReset}
      />

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Top Header Bar */}
        <header className="h-14 border-b border-slate-800/80 bg-slate-950/95 px-6 flex items-center justify-between gap-8 shrink-0 select-none z-20">
          {/* Zone 1: Location & Junction Node */}
          <div className="flex items-center gap-3 whitespace-nowrap shrink-0">
            <span className="text-sm font-bold tracking-tight text-slate-100">
              Oak Street & 5th Avenue
            </span>
            <span className="text-[11px] font-mono text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-500/30">
              NODE SC-INT-74
            </span>
            <span className="hidden sm:inline-flex items-center gap-1.5 text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-500/30">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              {sumoMode ? 'SUMO telemetry mode' : 'Synthetic demo mode'}
            </span>
          </div>

          {/* Zone 2: Fast Navigation Shortcuts */}
          <nav className="hidden lg:flex items-center gap-5 text-xs font-medium text-slate-400">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`hover:text-cyan-400 transition-colors whitespace-nowrap ${
                activeTab === 'dashboard' ? 'text-cyan-400 font-semibold' : ''
              }`}
            >
              Command View
            </button>
            <button
              onClick={() => setActiveTab('scenarios')}
              className={`hover:text-cyan-400 transition-colors whitespace-nowrap ${
                activeTab === 'scenarios' ? 'text-cyan-400 font-semibold' : ''
              }`}
            >
              Scenario Lab (25)
            </button>
            <button
              onClick={() => setActiveTab('comparison')}
              className={`hover:text-cyan-400 transition-colors whitespace-nowrap ${
                activeTab === 'comparison' ? 'text-cyan-400 font-semibold' : ''
              }`}
            >
              Benchmarks
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className={`hover:text-cyan-400 transition-colors whitespace-nowrap ${
                activeTab === 'analytics' ? 'text-cyan-400 font-semibold' : ''
              }`}
            >
              Analytics
            </button>
            <button
              onClick={() => setActiveTab('config_api')}
              className={`hover:text-cyan-400 transition-colors whitespace-nowrap ${
                activeTab === 'config_api' ? 'text-cyan-400 font-semibold' : ''
              }`}
            >
              Provider API
            </button>
          </nav>

          {/* Zone 3: Live Telemetry & Priority Preempt Action */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="hidden sm:flex items-center gap-4 text-xs font-mono text-slate-400">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span>
                  Index: <strong className="text-emerald-400 font-normal">{simState.metrics.performanceIndex}/100</strong>
                </span>
              </span>
              <span>
                Mean Delay: <strong className="text-cyan-400 font-normal">{simState.metrics.avgWaitTime}s</strong>
              </span>
            </div>

            <button
              disabled={sumoMode}
              title={sumoMode ? 'Use the SUMO telemetry emergency controls below' : 'Inject emergency into synthetic demo'}
              onClick={() => handleInjectAmbulance('north')}
              className="px-3 py-1.5 bg-rose-600/90 hover:bg-rose-500 text-white text-xs font-medium rounded-lg flex items-center gap-1.5 shadow-sm transition-colors whitespace-nowrap"
            >
              <Siren className="w-3.5 h-3.5" />
              <span>Priority Preempt</span>
            </button>
          </div>
        </header>

        {/* Dynamic View Router for All 14 Modules */}
        <main className="flex-1 overflow-hidden flex flex-col">
          {activeTab !== 'dashboard' && <div className="p-2 bg-amber-950 text-amber-200 text-sm">Synthetic demonstration module: these values and actions do not control SUMO.</div>}
          {/* Module 1: Overview Digital Twin Command Center (Animation on Left, Tables in Vertical Column on Right) */}
          {activeTab === 'dashboard' && <div className="p-2 border-b border-slate-800"><button className="px-4 py-2 bg-slate-800 rounded" onClick={() => setSumoMode(!sumoMode)}>{sumoMode ? 'Switch to synthetic demonstration' : 'Switch to SUMO telemetry'}</button></div>}
          {activeTab === 'dashboard' && sumoMode && <SumoLiveView />}
          {activeTab === 'dashboard' && !sumoMode && (
            <OverviewCommandCenter
              simState={simState}
              showAnalyticsOverlay={showAnalyticsOverlay}
              onToggleAnalyticsOverlay={() => setShowAnalyticsOverlay(!showAnalyticsOverlay)}
              onCameraChange={handleCameraChange}
              onTogglePlay={handleTogglePlay}
              onStep={handleStep}
              onReset={handleReset}
              onSetSpeed={handleSetSpeed}
              onSetWeather={handleSetWeather}
              onInjectAmbulance={handleInjectAmbulance}
              onInjectFireEngine={handleInjectFireEngine}
            />
          )}

          {/* Module 2: Scenario Laboratory (All 25 Scenarios & PRNG Seed) */}
          {activeTab === 'scenarios' && (
            <div className="flex-1 overflow-y-auto bg-slate-950">
              <ScenarioLabView
                currentScenario={simState.scenario}
                activeController={simState.controllerType}
                metrics={simState.metrics}
                seed={engineRef.current.getSeed()}
                onSetSeed={handleSetSeed}
                onSelectScenario={handleSelectScenario}
                onChangeController={handleChangeController}
                onCustomScenarioApply={handleCustomScenarioApply}
              />
            </div>
          )}

          {/* Module 3: Controller Benchmark Lab (7 Canonical Controllers) */}
          {activeTab === 'comparison' && (
            <div className="flex-1 overflow-y-auto bg-slate-950">
              <ComparisonLabView />
            </div>
          )}

          {/* Module 4: Analytics & Explainable AI */}
          {activeTab === 'analytics' && (
            <div className="flex-1 overflow-y-auto bg-slate-950">
              <AnalyticsView
                metrics={simState.metrics}
                mpcData={simState.mpcData}
                mappoData={simState.mappoData}
                telemetry={simState.telemetry}
              />
            </div>
          )}

          {/* Module 5: Traffic Prediction Center */}
          {activeTab === 'prediction' && (
            <div className="flex-1 overflow-y-auto bg-slate-950">
              <PredictionCenterView
                metrics={simState.metrics}
                telemetry={simState.telemetry}
              />
            </div>
          )}

          {/* Module 6: Network Coordination */}
          {activeTab === 'network' && (
            <div className="flex-1 overflow-y-auto bg-slate-950">
              <NetworkCoordinationView metrics={simState.metrics} />
            </div>
          )}

          {/* Module 7: Mathematical Model Explorer */}
          {activeTab === 'math_models' && (
            <div className="flex-1 overflow-y-auto bg-slate-950">
              <MathematicalModelExplorer />
            </div>
          )}

          {/* Module 8: V2I & Sensor Architecture */}
          {activeTab === 'v2i_hardware' && (
            <div className="flex-1 overflow-y-auto bg-slate-950">
              <V2IHardwareHub
                sensors={simState.sensorNodes}
                signals={simState.signals}
              />
            </div>
          )}

          {/* Module 9: Sensor Perception & LiDAR */}
          {activeTab === 'perception' && (
            <div className="flex-1 overflow-y-auto bg-slate-950">
              <PerceptionCameraView sensors={simState.sensorNodes} />
            </div>
          )}

          {/* Module 10: Pedestrian Actuation & Crossing Safety */}
          {activeTab === 'pedestrian' && (
            <div className="flex-1 overflow-y-auto bg-slate-950">
              <PedestrianCrossingView signals={simState.signals} />
            </div>
          )}

          {/* Module 11: Incident Management & Preemption Hub */}
          {activeTab === 'incidents' && (
            <div className="flex-1 overflow-y-auto bg-slate-950">
              <IncidentEmergencyView
                metrics={simState.metrics}
                signals={simState.signals}
                onInjectAmbulance={handleInjectAmbulance}
                onInjectFireEngine={handleInjectFireEngine}
              />
            </div>
          )}

          {/* Module 12: Safety Supervisor & Role-Based Access Control */}
          {activeTab === 'health_security' && (
            <div className="flex-1 overflow-y-auto bg-slate-950">
              <HealthSecurityView metrics={simState.metrics} />
            </div>
          )}

          {/* Module 13: Provider & Remote API Config */}
          {activeTab === 'config_api' && (
            <div className="flex-1 overflow-y-auto bg-slate-950">
              <ConfigApiView />
            </div>
          )}

          {/* Module 14: Scientific Data Export */}
          {activeTab === 'benchmark_export' && (
            <div className="flex-1 overflow-y-auto bg-slate-950">
              <BenchmarkExportView
                metrics={simState.metrics}
                scenario={simState.scenario}
                seed={engineRef.current.getSeed()}
              />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
