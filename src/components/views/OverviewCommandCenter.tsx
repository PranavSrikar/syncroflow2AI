/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { TrafficScene } from '../3d/TrafficScene.tsx';
import { ViewportHUD } from '../dashboard/ViewportHUD.tsx';
import { BottomPanels } from '../dashboard/BottomPanels.tsx';
import { SimulationDock } from '../dashboard/SimulationDock.tsx';
import { SimulationState } from '../../simulation/engine.ts';
import { Direction, WeatherMode, CameraViewPreset } from '../../types/traffic.ts';

interface OverviewCommandCenterProps {
  simState: SimulationState;
  showAnalyticsOverlay: boolean;
  onToggleAnalyticsOverlay: () => void;
  onCameraChange: (preset: CameraViewPreset) => void;
  onTogglePlay: () => void;
  onStep: () => void;
  onReset: () => void;
  onSetSpeed: (speed: number) => void;
  onSetWeather: (weather: WeatherMode) => void;
  onInjectAmbulance: (dir: Direction) => void;
  onInjectFireEngine: (dir: Direction) => void;
}

export const OverviewCommandCenter: React.FC<OverviewCommandCenterProps> = ({
  simState,
  showAnalyticsOverlay,
  onToggleAnalyticsOverlay,
  onCameraChange,
  onTogglePlay,
  onStep,
  onReset,
  onSetSpeed,
  onSetWeather,
  onInjectAmbulance,
  onInjectFireEngine,
}) => {
  return (
    <div className="flex-1 flex flex-col lg:flex-row h-full overflow-hidden">
      {/* Left Viewport: 3D Digital Twin Centerpiece */}
      <div className="flex-1 h-full min-h-[460px] relative bg-slate-950 border-r border-slate-800/80 overflow-hidden min-w-0">
        <TrafficScene
          vehicles={simState.vehicles}
          signals={simState.signals}
          weather={simState.weather}
          cameraPreset={simState.cameraPreset}
          showAnalyticsOverlay={showAnalyticsOverlay}
        />

        {/* Viewport HUD Overlays */}
        <ViewportHUD
          signals={simState.signals}
          telemetry={simState.telemetry}
          metrics={simState.metrics}
          cameraPreset={simState.cameraPreset}
          onCameraChange={onCameraChange}
          showAnalyticsOverlay={showAnalyticsOverlay}
          onToggleAnalyticsOverlay={onToggleAnalyticsOverlay}
          onInjectEmergency={onInjectAmbulance}
        />

        {/* Bottom Simulation Dock */}
        <div className="absolute bottom-3 left-0 right-0 z-20 pointer-events-none flex justify-center px-4">
          <SimulationDock
            isRunning={simState.isRunning}
            timeScale={simState.timeScale}
            weather={simState.weather}
            onTogglePlay={onTogglePlay}
            onStep={onStep}
            onReset={onReset}
            onSetSpeed={onSetSpeed}
            onSetWeather={onSetWeather}
            onInjectAmbulance={onInjectAmbulance}
            onInjectFireEngine={onInjectFireEngine}
          />
        </div>
      </div>

      {/* Right Column: Telemetry Tables, Real-Time Analytics & IoT Sensor Radar */}
      <div className="w-full lg:w-[460px] xl:w-[500px] h-full overflow-y-auto bg-slate-950 p-3.5 shrink-0 border-l border-slate-800/80">
        <BottomPanels
          sensorNodes={simState.sensorNodes}
          alerts={simState.recentAlerts}
          metrics={simState.metrics}
          telemetry={simState.telemetry}
        />
      </div>
    </div>
  );
};
