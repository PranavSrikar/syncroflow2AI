/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import {
  TrafficScenario,
  ControllerType,
  WeatherMode,
  Direction,
  SimulationMetrics,
} from '../../types/traffic.ts';
import { ALL_25_SCENARIOS } from '../../simulation/scenarios.ts';
import {
  FlaskConical,
  Sparkles,
  Sliders,
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Hash,
} from 'lucide-react';

interface ScenarioLabViewProps {
  currentScenario: TrafficScenario;
  activeController: ControllerType;
  metrics: SimulationMetrics;
  seed: number;
  onSetSeed: (seed: number) => void;
  onSelectScenario: (scenarioId: string) => void;
  onChangeController: (controller: ControllerType) => void;
  onCustomScenarioApply: (scenario: TrafficScenario) => void;
}

export const ScenarioLabView: React.FC<ScenarioLabViewProps> = ({
  currentScenario,
  activeController,
  metrics,
  seed,
  onSetSeed,
  onSelectScenario,
  onChangeController,
  onCustomScenarioApply,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [rates, setRates] = useState<Record<Direction, number>>(currentScenario.arrivalRates);
  const [weather, setWeather] = useState<WeatherMode>(currentScenario.weather);
  const [composition, setComposition] = useState(currentScenario.composition);
  const [inputSeed, setInputSeed] = useState(seed.toString());

  const categories = ['all', 'standard', 'rush_hour', 'incident', 'weather', 'emergency', 'network', 'failure'];

  const filteredScenarios = ALL_25_SCENARIOS.filter((sc) => {
    const matchesCat = selectedCategory === 'all' || sc.category === selectedCategory;
    const matchesSearch =
      sc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sc.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCat && matchesSearch;
  });

  const handleApplyCustom = () => {
    const updated: TrafficScenario = {
      ...currentScenario,
      arrivalRates: rates,
      weather,
      composition,
    };
    onCustomScenarioApply(updated);
  };

  const handleSeedChange = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = parseInt(inputSeed, 10);
    if (!isNaN(parsed) && parsed > 0) {
      onSetSeed(parsed);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto text-slate-200 select-none">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider">
            <FlaskConical className="w-4 h-4" />
            Scenario Laboratory & Stress-Testing Catalog (25 Scenarios)
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1 font-sans">
            Deterministic Scenario Benchmarking
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Every scenario creates reproducible physical differences in the underlying simulation state using seeded pseudorandom sequences.
          </p>
        </div>

        {/* Seed Config Bar */}
        <div className="flex items-center gap-3">
          <form onSubmit={handleSeedChange} className="flex items-center gap-1.5 bg-slate-900 border border-slate-700 rounded-xl px-2.5 py-1">
            <Hash className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-[11px] text-slate-400 font-mono">Seed:</span>
            <input
              type="number"
              value={inputSeed}
              onChange={(e) => setInputSeed(e.target.value)}
              className="w-16 bg-transparent text-xs font-mono text-cyan-300 focus:outline-none"
            />
            <button type="submit" className="text-[10px] bg-cyan-950 text-cyan-400 border border-cyan-500/40 px-2 py-0.5 rounded font-mono hover:bg-cyan-900">
              Set
            </button>
          </form>

          <button
            onClick={handleApplyCustom}
            className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs rounded-xl shadow-lg shadow-cyan-500/20 transition-all flex items-center gap-2"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Apply Parameter Overrides</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1 rounded-lg text-xs font-medium uppercase font-mono transition-colors ${
                selectedCategory === cat
                  ? 'bg-cyan-500 text-slate-950 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {cat.replace('_', ' ')}
            </button>
          ))}
        </div>

        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search 25 scenarios..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-slate-900/90 border border-slate-800 rounded-xl pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 w-64 focus:outline-none focus:border-cyan-500/50"
          />
        </div>
      </div>

      {/* 25 Scenario Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
        {filteredScenarios.map((sc) => {
          const isSelected = sc.id === currentScenario.id;
          return (
            <button
              key={sc.id}
              onClick={() => {
                onSelectScenario(sc.id);
                setRates(sc.arrivalRates);
                setWeather(sc.weather);
                setComposition(sc.composition);
              }}
              className={`text-left p-3.5 rounded-xl border transition-all flex flex-col justify-between ${
                isSelected
                  ? 'bg-cyan-950/40 border-cyan-500/60 shadow-lg shadow-cyan-950/40 ring-1 ring-cyan-500/40'
                  : 'bg-slate-950/80 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/50'
              }`}
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-100">{sc.name}</span>
                  <span className="text-[9px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
                    {sc.category}
                  </span>
                </div>

                <p className="text-[11px] text-slate-400 mt-2 line-clamp-2 leading-relaxed">
                  {sc.description}
                </p>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-900 flex items-center justify-between text-[10px] text-slate-400 font-mono">
                <span>Inflow: {Object.values(sc.arrivalRates).reduce((a, b) => a + b, 0)} v/h</span>
                <span className="text-cyan-400 uppercase">{sc.weather}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Inflow Rate Tuner */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-cyan-400" />
            Configurable Boundary Inflow Rates (Vehicles / Hour)
          </span>
          <span className="text-[10px] text-slate-400 font-mono">Active Scenario: {currentScenario.name}</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          {(['north', 'south', 'east', 'west'] as Direction[]).map((dir) => (
            <div key={dir} className="p-3 bg-slate-900/70 rounded-lg border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-[11px]">
                <span className="uppercase font-medium text-slate-300">{dir} Approach</span>
                <span className="font-mono text-cyan-400 font-bold">{rates[dir]} v/h</span>
              </div>
              <input
                type="range"
                min="0"
                max="2400"
                step="50"
                value={rates[dir]}
                onChange={(e) => setRates({ ...rates, [dir]: parseInt(e.target.value) })}
                className="w-full accent-cyan-400 bg-slate-800 h-1.5 rounded-lg cursor-pointer"
              />
              <div className="text-[9px] text-slate-400 flex justify-between font-mono">
                <span>0</span>
                <span>2400</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
