"""Shared executable multi-junction control path for API runtime and CTDE training."""
from datetime import datetime, timezone, timedelta
import numpy as np
import traci
from app.services.sumo_adapter import SumoAdapter
from app.services.traffic_estimation import TrafficEstimator
from app.services.constrained_mpc import ConstrainedMPC
from app.services.max_pressure_controller import MaxPressureController
from app.services.emergency_priority import EmergencyPriority
from app.services.forecasting import forecast_service
from app.services.mappo_coordination import MAPPOCoordinator, local_observations


def direction(dx, dy):
    return ('east' if dx > 0 else 'west') if abs(dx) > abs(dy) else ('north' if dy > 0 else 'south')


class HybridNetwork:
    def __init__(self, model, mode='hybrid', epoch=None):
        self.model, self.mode = model, mode
        self.epoch = epoch or datetime.now(timezone.utc)
        self.agents = tuple(sorted(model.movements))
        self.readers, self.estimators, self.controllers, self.emergencies = {}, {}, {}, {}
        self.coordinator = MAPPOCoordinator(self.agents)
        self.last_coordination = -5
        self.total_arrived = self.queue_seconds = 0
        self.previous_time = 0.0
        self.reward_totals = np.zeros(len(self.agents))
        self.latest_rewards = np.zeros(len(self.agents))
        self.last_service = {a: {0: 0.0, 1: 0.0} for a in self.agents}
        for agent in self.agents:
            node = model.net.getNode(agent)
            x, y = node.getCoord()
            incoming = [e for e in node.getIncoming() if e.getFunction() != 'internal']
            outgoing = [e for e in node.getOutgoing() if e.getFunction() != 'internal']
            approaches = {direction(e.getFromNode().getCoord()[0]-x, e.getFromNode().getCoord()[1]-y): e.getID() for e in incoming}
            departures = {direction(e.getToNode().getCoord()[0]-x, e.getToNode().getCoord()[1]-y): e.getID() for e in outgoing}
            if set(approaches) != {'north', 'south', 'east', 'west'} or len(approaches) != len(incoming) or len(departures) != 4:
                raise ValueError('Hybrid scenario requires one incoming edge per compass approach')
            reader = SumoAdapter(approaches, departures, {agent})
            reader.connected = True
            self.readers[agent] = reader
            self.estimators[agent] = TrafficEstimator()
            routes = {}
            for d in approaches:
                opposite = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[d]
                route_id = 'synchroflow_'+agent+'_'+d
                traci.route.add(route_id, traci.simulation.findRoute(approaches[d], departures[opposite]).edges)
                routes[d] = route_id
            self.emergencies[agent] = EmergencyPriority(approaches, routes, 'synchroflow_emergency_'+agent)
            if mode != 'sumo_fixed_time':
                cls = MaxPressureController if mode == 'max_pressure' else ConstrainedMPC
                controller = cls(model, reader.get_telemetry())
                controller.emergencies = self.emergencies[agent]
                self.controllers[agent] = controller
        self.raw = self.read()

    def read(self):
        result = {}
        priorities = {}
        for emergency in self.emergencies.values():
            for vehicle, request in emergency.requests.items():
                priorities[vehicle] = max(priorities.get(vehicle, 1), request['priority'])
        for agent, reader in self.readers.items():
            raw = reader.get_telemetry()
            raw['stateEstimates'] = self.estimators[agent].update(raw)
            raw['arrivalForecast'] = forecast_service.predict(self.epoch+timedelta(seconds=raw['simTime']), for_mpc=True, junction_id=agent)
            raw['permissionAnalysis'] = {agent: self.model.analyze_state(agent, raw['trafficLights'][agent]['signalState'])}
            raw['pedestrianSignals'] = []  # supplied corridor has no pedestrian crossings
            controller = self.controllers.get(agent)
            if controller:
                controller.supervisor.check_observation(raw)
            emergency = self.emergencies[agent]
            for vehicle, priority in priorities.items():
                details = raw['vehicleDetails'].get(vehicle)
                if details and details['vehicleClass'] == 'emergency' and details['roadId'] in emergency.approach_edges.values():
                    emergency.register(raw, vehicle, priority)
            emergency.update(raw)
            greens = controller.supervisor.green_indices if controller else [0, 2]
            phase = raw['trafficLights'][agent]['phaseIndex']
            if phase in greens:
                self.last_service[agent][greens.index(phase)] = raw['simTime']
            result[agent] = raw
        return result

    def observations(self):
        return local_observations(self.raw, self.controllers, self.agents)

    def before_step(self, training_actions=None):
        now = next(iter(self.raw.values()))['simTime']
        if training_actions is not None:
            actions = self.coordinator.validate_actions(training_actions)
            self.coordinator.last_actions = actions.tolist()
        elif self.mode == 'hybrid':
            if now-self.last_coordination >= 5:
                actions = self.coordinator.recommend(self.observations())
                self.last_coordination = now
            else:
                actions = self.coordinator.last_actions
        else:
            actions = None
        for index, agent in enumerate(self.agents):
            if agent in self.controllers:
                controller = self.controllers[agent]
                controller.coordination_hint = int(actions[index]) if actions is not None else None
                controller.before_step(self.raw[agent])

    def after_step(self):
        self.raw = self.read()
        now = traci.simulation.getTime()
        dt = now-self.previous_time
        self.previous_time = now
        arrived = traci.simulation.getArrivedNumber()
        self.total_arrived += arrived
        rewards = np.zeros(len(self.agents), dtype=np.float32)
        for index, agent in enumerate(self.agents):
            raw = self.raw[agent]
            queue = sum(a['queued'] for a in raw['approaches'].values())
            delay = sum(a['avgWaitTimeSec']*a['vehicles'] for a in raw['approaches'].values())
            spillback = sum(d['spillbackIndicator'] for d in raw['downstream'].values())
            conflicts = len(raw['permissionAnalysis'][agent]['incompatiblePermissions'])
            fairness = max(now-t for t in self.last_service[agent].values())
            rewards[index] = -(0.1*queue+0.01*delay+2*spillback+fairness/120+100*conflicts)*dt+arrived/len(self.agents)
            self.queue_seconds += queue*dt
            if conflicts:
                raise ValueError('Unsafe network permission observation; simulation paused')
        if traci.simulation.getCollidingVehiclesNumber():
            raise ValueError('SUMO reported a collision; simulation paused')
        self.latest_rewards = rewards
        self.reward_totals += rewards
        return rewards, arrived

    def cancel(self):
        for emergency in self.emergencies.values():
            emergency.cancel_all(traci.simulation.getTime())

    def snapshot(self):
        now = next(iter(self.raw.values()))['simTime']
        junctions = {agent: dict(telemetry=self.raw[agent], controllerDiagnostics=c.diagnostics if (c := self.controllers.get(agent)) else None,
                               safetySupervisor=c.supervisor.report() if c else {'status': 'unavailable', 'reason': 'Fixed-time baseline'},
                               forecasts=self.raw[agent]['arrivalForecast'], emergencyPriority=self.emergencies[agent].snapshot()) for agent in self.agents}
        return dict(junctions=junctions, mappoStatus=self.coordinator.snapshot(),
                    metrics=dict(source='sumo_traci', arrivedVehicles=self.total_arrived, queueVehicleSeconds=self.queue_seconds,
                                 throughputVehiclesPerHour=self.total_arrived*3600/now if now else None,
                                 rewards=self.reward_totals.tolist(), simTime=now,
                                 limitations='Research reward and measured approach queue integral; no comparative benefit established'))
