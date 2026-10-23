"""Serialized real SUMO lifecycle; never shares synthetic demo measurements."""
from threading import RLock
from pathlib import Path
import importlib.util
import json
from datetime import datetime, timezone, timedelta
from math import isfinite
from app.services.sumo_adapter import sumo_adapter
from app.services.traffic_estimation import TrafficEstimator
from app.services.sumo_network_safety import NetworkSafetyModel
from app.services.max_pressure_controller import MaxPressureController
from app.services.constrained_mpc import ConstrainedMPC
from app.services.emergency_priority import EmergencyPriority
from app.services.forecasting import forecast_service
from app.services.hybrid_network import HybridNetwork
from app.services.mappo_coordination import MAPPOCoordinator, local_observations
import traci


class SumoRuntime:
    def __init__(self, adapter=sumo_adapter):
        self.adapter = adapter
        self.lock = RLock()
        self.running = False
        self.error = None
        self.sequence = 0
        self.telemetry = None
        self.estimator = TrafficEstimator()
        self.scenario = "vehicle"
        self.network_model = None
        self.controller = None
        self.controller_mode = "sumo_fixed_time"
        self.emergencies = EmergencyPriority()
        self.forecast_epoch = datetime.now(timezone.utc)
        self.forecasts = None
        self.network = None
        self.coordinator = None
        self.seed = 23423  # SUMO's prior implicit default; preserve existing demand.
        self.metrics = {'source': 'sumo_traci', 'arrivedVehicles': 0, 'queueVehicleSeconds': 0.0}

    def emergency_request(self, vehicle_id, priority=1, junction_id=None):
        with self.lock:
            if self.network and self.adapter.connected:
                agent = junction_id or self.network.agents[0]
                if agent not in self.network.controllers:
                    raise ValueError('Emergency priority requires a supervised junction')
                emergency = self.network.emergencies[agent]
                result = emergency.register(self.network.raw[agent], vehicle_id, priority)
                emergency.update(self.network.raw[agent])
                return result
            if not self.adapter.connected or self.controller is None:
                raise ValueError("Emergency priority requires a running supervised adaptive scenario")
            request = self.emergencies.register(self.telemetry, vehicle_id, priority)
            self.emergencies.update(self.telemetry)
            return request

    def inject_emergency(self, approach, priority=1, junction_id=None):
        with self.lock:
            if self.network and self.adapter.connected:
                agent = junction_id or self.network.agents[0]
                if agent not in self.network.controllers:
                    raise ValueError('Emergency priority requires a supervised junction')
                return self.network.emergencies[agent].inject(approach, priority)
            if not self.adapter.connected or self.controller is None:
                raise ValueError("Emergency injection requires a running supervised adaptive scenario")
            return self.emergencies.inject(approach, priority)

    def _advance(self):
        try:
            if self.network:
                self.network.before_step()
                traci.simulationStep()
                self.network.after_step()
                self.telemetry = self._network_telemetry()
                self.sequence += 1
                return
            if self.controller is not None:
                if self.coordinator:
                    agent = self.controller.tls
                    recommendations = self.coordinator.recommend(local_observations({agent: self.telemetry}, {agent: self.controller}, (agent,)))
                    self.controller.coordination_hint = int(recommendations[0]) if recommendations is not None else None
                self.controller.before_step(self.telemetry)
            self.telemetry = self._observe(self.adapter.step())
            self.metrics['arrivedVehicles'] += traci.simulation.getArrivedNumber()
            self.metrics['queueVehicleSeconds'] += sum(a['queued'] for a in self.telemetry['approaches'].values())
            self.metrics['throughputVehiclesPerHour'] = self.metrics['arrivedVehicles']*3600/self.telemetry['simTime'] if self.telemetry['simTime'] else None
            self.sequence += 1
        except Exception as exc:
            self.running = False
            self.error = str(exc)
            raise

    def _network_telemetry(self):
        primary = self.network.agents[0]
        raw = dict(self.network.raw[primary])
        raw['primaryJunctionId'] = primary
        raw['trafficLights'] = {agent: data['trafficLights'][agent] for agent, data in self.network.raw.items()}
        raw['permissionAnalysis'] = {agent: data['permissionAnalysis'][agent] for agent, data in self.network.raw.items()}
        self.forecasts = self.network.raw[primary]['arrivalForecast']
        return raw

    def _observe(self, raw):
        raw["stateEstimates"] = self.estimator.update(raw)
        self.forecasts = forecast_service.predict(self.forecast_epoch + timedelta(seconds=raw['simTime']), for_mpc=True)
        raw['arrivalForecast'] = self.forecasts
        if self.network_model is not None:
            raw["permissionAnalysis"] = {
                tls: self.network_model.analyze_state(tls, light["signalState"])
                for tls, light in raw["trafficLights"].items()
            }
            raw["pedestrianSignals"] = [
                {**movement, "state": raw["trafficLights"][tls]["signalState"][movement["signalIndex"]],
                 "occupants": [p for p, d in raw["pedestrians"].items() if d["roadId"] == movement["outgoingLane"].rsplit("_", 1)[0]],
                 "waitingPersons": [p for p, d in raw["pedestrians"].items() if d["nextEdge"] == movement["outgoingLane"].rsplit("_", 1)[0] and d["waitingTimeSec"] > 0],
                 "clearanceRequirementSec": getattr(self.controller.supervisor, "required_clearance", None) if self.controller else None}
                for tls, movements in self.network_model.movements.items()
                for movement in movements if movement["pedestrian"]
            ]
        if self.controller is not None:
            self.controller.supervisor.check_observation(raw)
        self.emergencies.update(raw)
        return raw

    def command(self, action, scenario=None, controller=None, seed=None, paused=False, mpc_budget_ms=None):
        with self.lock:
            if action == "start":
                requested = scenario or self.scenario
                requested_controller = controller or self.controller_mode
                if requested_controller not in {"sumo_fixed_time", "max_pressure", "mpc", "hybrid"}:
                    raise ValueError("Unknown or unimplemented controller")
                if requested not in {"vehicle", "pedestrian", "corridor", "unequal", "spillback"}:
                    raise ValueError("Unknown SUMO scenario")
                if self.adapter.connected and requested != self.scenario:
                    raise RuntimeError("Stop SUMO before changing networks")
                if self.adapter.connected and requested_controller != self.controller_mode:
                    raise RuntimeError("Stop SUMO before changing controllers")
                if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 2147483647):
                    raise ValueError('Seed must be an integer from 0 to 2147483647')
                if self.adapter.connected and seed is not None and seed != self.seed:
                    raise RuntimeError('Stop SUMO before changing seed')
                if mpc_budget_ms is not None and (not isfinite(mpc_budget_ms) or not 0 <= mpc_budget_ms <= 1000):
                    raise ValueError('MPC budget must be finite, 0 to 1000 ms')
                if self.adapter.connected and mpc_budget_ms is not None:
                    raise RuntimeError('Stop SUMO before changing solver budget')
                if not self.adapter.connected:
                    name = "junction.pedestrian.sumocfg" if requested == "pedestrian" else "junction.sumocfg"
                    self.adapter.config_path = Path(__file__).resolve().parents[2] / "sumo_scenarios" / "four_way_basic" / name
                    if requested == 'corridor':
                        self.adapter.config_path = Path(__file__).resolve().parents[2] / 'sumo_scenarios/two_junction/corridor.sumocfg'
                    elif requested in {'unequal', 'spillback'}:
                        self.adapter.config_path = Path(__file__).resolve().parents[2] / 'sumo_scenarios/demo' / (requested+'.sumocfg')
                    self.scenario = requested
                    net_name = "junction.pedestrian-test.net.xml" if requested == "pedestrian" else "junction.net.xml"
                    if requested == 'corridor':
                        net_name = 'corridor.net.xml'
                    network_path = self.adapter.config_path.parent / net_name
                    if requested in {'unequal', 'spillback'}:
                        network_path = Path(__file__).resolve().parents[2] / 'sumo_scenarios/four_way_basic/junction.net.xml'
                    self.network_model = NetworkSafetyModel(network_path)
                    self.estimator = TrafficEstimator()
                    self.emergencies = EmergencyPriority()
                    self.forecast_epoch = datetime.now(timezone.utc)
                    self.seed = 23423 if seed is None else seed
                    self.adapter.start(self.seed)
                    try:
                        self.controller = None
                        self.network = None
                        self.coordinator = None
                        self.metrics = {'source': 'sumo_traci', 'arrivedVehicles': 0, 'queueVehicleSeconds': 0.0}
                        self.controller_mode = requested_controller
                        if requested == 'corridor':
                            self.network = HybridNetwork(self.network_model, requested_controller, self.forecast_epoch)
                            self.telemetry = self._network_telemetry()
                        elif requested_controller in {"max_pressure", "mpc", "hybrid"}:
                            controller_class = ConstrainedMPC if requested_controller == "mpc" else MaxPressureController
                            if requested_controller == 'hybrid':
                                controller_class = ConstrainedMPC
                            self.controller = controller_class(self.network_model, self.adapter.get_telemetry())
                            self.controller.emergencies = self.emergencies
                            if requested_controller == 'hybrid':
                                self.coordinator = MAPPOCoordinator((self.controller.tls,))
                        if requested != 'corridor':
                            self.telemetry = self._observe(self.adapter.get_telemetry())
                        if mpc_budget_ms is not None:
                            controllers = self.network.controllers.values() if self.network else ([self.controller] if self.controller else [])
                            for active_controller in controllers:
                                if isinstance(active_controller, ConstrainedMPC):
                                    active_controller.SOLVE_BUDGET_SEC = mpc_budget_ms/1000
                    except Exception:
                        self.adapter.stop()
                        self.controller = None
                        self.network = None
                        raise
                self.running = not paused
                self.error = None
            elif action == "pause":
                self.running = False
            elif action == "stop":
                self.running = False
                self.emergencies.cancel_all(self.telemetry["simTime"] if self.telemetry else 0.0)
                if self.network and self.adapter.connected:
                    self.network.cancel()
                self.adapter.stop()
                self.telemetry = None
                self.controller = None
                self.forecasts = None
            elif action == "step":
                if self.running:
                    raise RuntimeError("Pause before single stepping")
                self._advance()
            else:
                raise ValueError("Unknown lifecycle command")
            return self.snapshot()

    def tick(self):
        with self.lock:
            if self.running:
                try:
                    self._advance()
                except Exception as exc:
                    self.running = False
                    self.error = str(exc)
            return self.snapshot()

    def snapshot(self):
        with self.lock:
            network = self.network.snapshot() if self.network else None
            result = {
                "source": "sumo_traci", "connected": self.adapter.connected,
                "running": self.running, "sequence": self.sequence,
                "controller": self.controller_mode, "error": self.error,
                "scenario": self.scenario,
                'seed': self.seed,
                "safetySupervisor": self.controller.supervisor.report() if self.controller else {"status": "unavailable", "reason": "No active adaptive supervisor: simulation is stopped or using the fixed-time baseline"},
                "controllerDiagnostics": self.controller.diagnostics if self.controller else None,
                "forecasts": self.forecasts, "telemetry": self.telemetry,
                "emergencyPriority": self.emergencies.snapshot(),
                "mappoStatus": self.mappo_status(),
                'junctions': network['junctions'] if network else {},
                'metrics': network['metrics'] if network else self.metrics,
                'hybridPipeline': ['SUMO observations', 'state estimation', 'historical/weather forecasts or observed PCU arrivals',
                                   'movement Max-Pressure', 'qualified MAPPO preferences or no learned hint', 'constrained MPC / Max-Pressure fallback',
                                   'independent supervisor', 'TraCI', 'API/WebSocket'],
            }
            if network:
                result['mappoStatus'].update(network['mappoStatus'])
                if self.adapter.connected:
                    result['safetySupervisor'] = {'status': 'enforcing_multi_junction_timing' if self.network.controllers else 'unavailable',
                                                   'reason': 'Each junction has its own independent supervisor; invalid safety feedback pauses the whole simulation'}
                result['controllerDiagnostics'] = {agent: data['controllerDiagnostics'] for agent, data in network['junctions'].items()}
                result['emergencyPriority'] = {
                    'activeVehicleId': next((e.selected for e in self.network.emergencies.values() if e.selected), None),
                    'requests': [dict(junctionId=a, **r) for a, e in self.network.emergencies.items() for r in e.snapshot()['requests']],
                    'events': [dict(junctionId=a, **r) for a, e in self.network.emergencies.items() for r in e.snapshot()['events']]}
            elif self.coordinator:
                result['mappoStatus'].update(self.coordinator.snapshot())
            # Read-only visibility into existing fairness gates; never changes
            # supervisor state or manufactures an explanation for an action.
            def service_age(controller, raw):
                if controller is None or raw is None:
                    return None
                supervisor = controller.supervisor
                return {'phaseAgeSec': {str(p): max(0.0, raw['simTime'] - t)
                                         for p, t in supervisor.last_served.items()},
                        'maximumRedSec': supervisor.MAX_RED,
                        'definition': 'Time since phase last observed green; not individual vehicle delay'}
            result['serviceAge'] = service_age(self.controller, self.telemetry)
            if network:
                for agent, row in result['junctions'].items():
                    row['serviceAge'] = service_age(self.network.controllers.get(agent), row['telemetry'])
            return result

    def mappo_status(self):
        folder = Path(__file__).resolve().parents[3] / '.checkpoints'
        report_path = folder / 'stage2-mappo-smoke.json'
        if not report_path.is_file():
            report_path = folder / 'mappo-smoke.json'
        report = None
        if report_path.is_file():
            try:
                report = json.loads(report_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pass
        return {"torchAvailable": importlib.util.find_spec("torch") is not None,
                "operationalPolicyEnabled": False,
                "reason": "Research-only checkpoint; full training and policy validation required before operational activation",
                "smokeTrainingReport": report}


sumo_runtime = SumoRuntime()
