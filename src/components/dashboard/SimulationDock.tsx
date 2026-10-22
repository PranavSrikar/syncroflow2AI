/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import {
  Play,
  Pause,
  SkipForward,
  RotateCcw,
  Sun,
  Moon,
  CloudRain,
  CloudFog,
  Siren,
  Flame,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { WeatherMode, Direction } from '../../types/traffic.ts';

interface SimulationDockProps {
  isRunning: boolean;
  timeScale: number;
  weather: WeatherMode;
  onTogglePlay: () => void;
  onStep: () => void;
  onReset: () => void;
  onSetSpeed: (speed: number) => void;
  onSetWeather: (weather: WeatherMode) => void;
  onInjectAmbulance: (dir: Direction) => void;
  onInjectFireEngine: (dir: Direction) => void;
}

export const SimulationDock: React.FC<SimulationDockProps> = ({
  isRunning,
  timeScale,
  weather,
  onTogglePlay,
  onStep,
  onReset,
  onSetSpeed,
  onSetWeather,
  onInjectAmbulance,
  onInjectFireEngine,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [selectedEmergencyArm, setSelectedEmergencyArm] = useState<Direction>('north');

  return (
    <div className="flex flex-col items-center pointer-events-auto select-none transition-all duration-300">
      {/* Collapse / Expand Toggle Button */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="mb-1.5 px-3 py-1 bg-slate-900/90 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700/80 rounded-full text-[11px] font-medium flex items-center gap-1.5 shadow-lg backdrop-blur-md transition-colors"
      >
        {isCollapsed ? (
          <>
            <ChevronUp className="w-3.5 h-3.5 text-cyan-400" />
            <span>Show Simulation Dock</span>
          </>
        ) : (
          <>
            <ChevronDown className="w-3.5 h-3.5 text-cyan-400" />
            <span>Hide Controls</span>
          </>
        )}
      </button>

      {/* Main Control Dock */}
      {!isCollapsed && (
        <div className="bg-slate-950/95 backdrop-blur-md border border-slate-800 rounded-2xl p-2.5 px-4 shadow-2xl flex flex-wrap items-center justify-between gap-4 max-w-5xl w-full">
          {/* Transport Controls (Play, Step, Reset, Speeds) */}
          <div className="flex items-center gap-2">
            <button
              onClick={onTogglePlay}
              className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all ${
                isRunning
                  ? 'bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold shadow-md shadow-emerald-500/20'
                  : 'bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold shadow-md shadow-amber-500/20'
              }`}
              title={isRunning ? 'Pause Simulation' : 'Resume Simulation'}
            >
              {isRunning ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
            </button>

            <button
              onClick={onStep}
              disabled={isRunning}
              className={`w-8 h-8 rounded-lg flex items-center justify-center border transition-colors ${
                isRunning
                  ? 'border-slate-800 text-slate-600 cursor-not-allowed'
                  : 'border-slate-700 hover:border-slate-600 text-slate-300 hover:bg-slate-900'
              }`}
              title="Step Simulation Clock (Δt=0.5s)"
            >
              <SkipForward className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={onReset}
              className="w-8 h-8 rounded-lg border border-slate-700 hover:border-slate-600 text-slate-300 hover:bg-slate-900 flex items-center justify-center transition-colors"
              title="Reset Simulation"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>

            {/* Speed Multipliers */}
            <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800 ml-1">
              {[1, 2, 5, 10].map((spd) => (
                <button
                  key={spd}
                  onClick={() => onSetSpeed(spd)}
                  className={`px-2 py-0.5 rounded text-xs font-mono font-medium transition-all ${
                    timeScale === spd
                      ? 'bg-cyan-500 text-slate-950 font-bold'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {spd}x
                </button>
              ))}
            </div>
          </div>

          {/* Emergency Injection Buttons */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 bg-slate-900 p-0.5 rounded-lg border border-slate-800 text-[10px]">
              {(['north', 'south', 'east', 'west'] as Direction[]).map((arm) => (
                <button
                  key={arm}
                  onClick={() => setSelectedEmergencyArm(arm)}
                  className={`px-1.5 py-0.5 rounded font-mono uppercase font-semibold ${
                    selectedEmergencyArm === arm
                      ? 'bg-rose-500 text-white'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {arm[0]}
                </button>
              ))}
            </div>

            <button
              onClick={() => onInjectAmbulance(selectedEmergencyArm)}
              className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs rounded-xl flex items-center gap-1.5 shadow-md shadow-rose-600/30 transition-colors"
            >
              <Siren className="w-3.5 h-3.5" />
              <span>Inject Ambulance</span>
            </button>

            <button
              onClick={() => onInjectFireEngine(selectedEmergencyArm)}
              className="px-3 py-1.5 bg-red-700 hover:bg-red-600 text-white font-medium text-xs rounded-xl flex items-center gap-1.5 shadow-md shadow-red-700/30 transition-colors"
            >
              <Flame className="w-3.5 h-3.5" />
              <span>Fire Engine</span>
            </button>
          </div>

          {/* Weather Profiles (Day, Night, Monsoon, Fog) */}
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-slate-500 font-medium">WEATHER:</span>
            <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800">
              <button
                onClick={() => onSetWeather('day')}
                className={`px-2.5 py-1 rounded text-xs flex items-center gap-1.5 transition-all ${
                  weather === 'day'
                    ? 'bg-amber-500 text-slate-950 font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Sun className="w-3 h-3" />
                <span>Day</span>
              </button>

              <button
                onClick={() => onSetWeather('night')}
                className={`px-2.5 py-1 rounded text-xs flex items-center gap-1.5 transition-all ${
                  weather === 'night'
                    ? 'bg-indigo-600 text-white font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Moon className="w-3 h-3" />
                <span>Night</span>
              </button>

              <button
                onClick={() => onSetWeather('monsoon')}
                className={`px-2.5 py-1 rounded text-xs flex items-center gap-1.5 transition-all ${
                  weather === 'monsoon'
                    ? 'bg-cyan-600 text-white font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <CloudRain className="w-3 h-3" />
                <span>Monsoon</span>
              </button>

              <button
                onClick={() => onSetWeather('fog')}
                className={`px-2.5 py-1 rounded text-xs flex items-center gap-1.5 transition-all ${
                  weather === 'fog'
                    ? 'bg-slate-700 text-white font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <CloudFog className="w-3 h-3" />
                <span>Fog</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
