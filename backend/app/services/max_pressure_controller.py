"""Feedback Max-Pressure-inspired green extensions over a legal two-stage ring."""
import traci
from app.services.signal_supervisor import SignalSupervisor
from app.services.pedestrian_supervisor import PedestrianSupervisor

PCU = {"motorcycle": 0.5, "bicycle": 0.3, "bus": 3.0, "truck": 2.5, "trailer": 3.0}


class MaxPressureController:
    def __init__(self, model, initial):
        if len(initial["trafficLights"]) != 1:
            raise ValueError("Current adaptive runtime supports one junction")
        self.tls, light = next(iter(initial["trafficLights"].items()))
        self.model = model
        self.emergencies = None
        pedestrian = any(m["pedestrian"] for m in model.movements[self.tls])
        self.supervisor = PedestrianSupervisor(model, self.tls) if pedestrian else SignalSupervisor(model, self.tls)
        native = light["phases"]
        if pedestrian:
            self.supervisor.install(self.supervisor.build_program(native))
            self.diagnostics = {}
            return
        if len(native) != 4:
            raise ValueError("Adaptive mode requires the original vehicle-only network")
        phases = []
        for i in (0, 2):
            phases.extend([
                traci.trafficlight.Phase(self.supervisor.MIN_GREEN + 1, native[i]["state"]),
                traci.trafficlight.Phase(max(3, native[i+1]["duration"]), native[i+1]["state"]),
                traci.trafficlight.Phase(2, "r" * len(native[i]["state"])),
            ])
        self.supervisor.install(phases)
        self.diagnostics = {}

    def pressures(self, raw):
        scores = {}
        movements = []
        for phase_index in self.supervisor.green_indices:
            state = self.supervisor.phases[phase_index].state
            score = 0.0
            used = set()
            for m in self.model.movements[self.tls]:
                if m["pedestrian"]:
                    continue
                if state[m["signalIndex"]] not in "Gg":
                    continue
                pair = (m["incomingLane"], m["outgoingLane"])
                if pair in used:
                    continue
                used.add(pair)
                incoming = m["incomingLane"].rsplit("_", 1)[0]
                outgoing = m["outgoingLane"].rsplit("_", 1)[0]
                upstream = downstream = 0.0
                for vehicle in raw["vehicleDetails"].values():
                    if vehicle["speedMps"] > 0.1:
                        continue
                    weight = PCU.get(vehicle["vehicleClass"], 1.0)
                    route = vehicle["routeEdges"]
                    route_index = vehicle.get("routeIndex", route.index(incoming) if incoming in route else -1)
                    next_edge = route[route_index + 1] if 0 <= route_index < len(route) - 1 else None
                    if vehicle["roadId"] == incoming and next_edge == outgoing:
                        upstream += weight
                    elif vehicle["roadId"] == outgoing:
                        downstream += weight
                receiving = next((r for r in raw["downstream"].values() if r["edgeId"] == outgoing), None)
                # Do not reward serving a saturated receiver. This is a heuristic
                # phase-level extension rule, not per-movement spillback proof.
                pressure = -upstream - downstream if receiving and receiving["spillbackIndicator"] else upstream - downstream
                score += pressure * (1.0 if state[m["signalIndex"]] == "G" else 0.5)
                movements.append(dict(phaseIndex=phase_index, incomingEdge=incoming, outgoingEdge=outgoing,
                                      upstreamQueuedPcu=upstream, downstreamQueuedPcu=downstream,
                                      pressurePcu=pressure, spillback=bool(receiving and receiving['spillbackIndicator'])))
            scores[phase_index] = score
        self.movement_diagnostics = movements
        return scores

    def receiving_supply(self, raw, direction):
        """Route-weighted receiving heuristic; SUMO still enforces junction blocking."""
        row = raw['approaches'][direction]
        weights = {}
        for vehicle_id in row['vehicleIds']:
            vehicle = raw['vehicleDetails'][vehicle_id]
            index = vehicle.get('routeIndex', -1)
            route = vehicle['routeEdges']
            if 0 <= index < len(route)-1:
                edge = route[index+1]
                weights[edge] = weights.get(edge, 0)+PCU.get(vehicle['vehicleClass'], 1.0)
        receivers = {v['edgeId']: v for v in raw['downstream'].values()}
        if not weights:
            opposite = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[direction]
            weights = {raw['downstream'][opposite]['edgeId']: 1.0}
        def supply(edge):
            receiver = receivers.get(edge)
            if receiver is None or receiver['spillbackIndicator']:
                return 0.0
            return max(0.0, 1-receiver['occupancyPercent']/100)
        return sum(weight*supply(edge) for edge, weight in weights.items())/sum(weights.values())

    def before_step(self, raw):
        self.supervisor.verify_live_feedback(raw)
        self.supervisor.check_observation(raw)
        self.supervisor.guard_clearance(raw)
        light = raw["trafficLights"][self.tls]
        phase = light["phaseIndex"]
        now = raw["simTime"]
        spent = traci.trafficlight.getSpentDuration(self.tls)
        if phase in self.supervisor.green_indices:
            self.supervisor.last_served[phase] = now
            scores = self.pressures(raw)
            self.diagnostics = {"phasePressurePcu": scores, "elapsedGreenSec": spent,
                                "movementPressure": self.movement_diagnostics,
                                "policy": "Extend incumbent when its pressure dominates; retain legal cyclic service"}
            if self.emergencies is not None and self.emergencies.selected is not None:
                remaining = self.emergencies.recommend(raw, self.supervisor, phase, spent)
                self.diagnostics.update({"policy": "emergency_priority", "vehicleId": self.emergencies.selected,
                                         "recommendedRemainingSec": remaining})
            else:
                remaining = self.recommend_remaining(raw, phase, spent, scores)
            if remaining is not None:
                try:
                    self.supervisor.apply_duration(phase, remaining, self.diagnostics.get("policy", "pressure_extension"))
                except ValueError:
                    # The approved program expires naturally when extension is
                    # rejected by fairness; never write a substitute raw action.
                    pass

    def recommend_remaining(self, raw, phase, spent, scores):
        other = self.supervisor.other_green(phase)
        if spent >= self.supervisor.MIN_GREEN and spent < self.supervisor.max_green_duration(phase) and scores[phase] > 0 and scores[phase] >= scores[other]:
            return min(2.0, self.supervisor.max_green_duration(phase) - spent)
        return None
