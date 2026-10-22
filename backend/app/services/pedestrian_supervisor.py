"""Protected pedestrian service and runtime clearance gate for the SUMO junction.

The design walking speed (0.5 m/s) and two-second margin are simulation
parameters, not a road standard. Actual occupancy holds cover slower walkers.
"""
from math import ceil, isfinite
import traci
from app.services.signal_supervisor import SignalSupervisor


class PedestrianSupervisor(SignalSupervisor):
    DESIGN_WALK_SPEED = 0.5
    CLEARANCE_MARGIN = 2.0
    MIN_WALK = 7.0

    def __init__(self, model, tls):
        super().__init__(model, tls)
        self.green_indices = [2, 7]
        self.walk_indices = {0, 5}
        self.closing_indices = {1, 6}
        self.yellow_indices = {3, 8}
        self.allred_indices = {4, 9}
        self.crossings = [m for m in model.movements[tls] if m["pedestrian"]]
        self.required_clearance = ceil(max(m["crossingLengthM"] for m in self.crossings) / self.DESIGN_WALK_SPEED + self.CLEARANCE_MARGIN)
        self.previous_phase = None
        self.entered_at = 0.0
        self.occupancy_holds = 0
        self.previous_raw = None

    def are_foes(self, a, b):
        if a["junction"] != b["junction"]:
            return False
        rows = self.model.requests[a["junction"]]
        return bool((rows[a["requestIndex"]][0] >> b["requestIndex"]) & 1 or (rows[b["requestIndex"]][0] >> a["requestIndex"]) & 1)

    def protected_state(self, state):
        result = list(state)
        active = [c for c in self.crossings if state[c["signalIndex"]] in "Gg"]
        for vehicle in self.model.movements[self.tls]:
            if not vehicle["pedestrian"] and any(self.are_foes(vehicle, c) for c in active):
                result[vehicle["signalIndex"]] = "r"
        return "".join(result)

    def build_program(self, native):
        if len(native) != 6:
            raise ValueError("Expected the inspected pedestrian network program")
        phases = []
        for source in (0, 3):
            native_state = native[source]["state"]
            pedestrian_links = {c["signalIndex"] for c in self.crossings}
            walk = "".join(s if i in pedestrian_links else "r" for i, s in enumerate(native_state))
            vehicles = "".join("r" if i in pedestrian_links else s for i, s in enumerate(native_state))
            red = "r" * len(walk)
            phases.extend([traci.trafficlight.Phase(10, walk),
                           traci.trafficlight.Phase(self.required_clearance, red),
                           traci.trafficlight.Phase(11, vehicles),
                           traci.trafficlight.Phase(3, "".join("y" if s in "Gg" else "r" for s in vehicles)),
                           traci.trafficlight.Phase(2, red)])
        return phases

    def validate_program(self, phases):
        if len(phases) != 10:
            raise ValueError("Pedestrian program requires walk/clearance/vehicle/yellow/all-red groups")
        served = set()
        for i, phase in enumerate(phases):
            state, duration = phase.state, phase.duration
            if not isfinite(duration) or duration <= 0:
                raise ValueError("Invalid phase duration")
            analysis = self.model.analyze_state(self.tls, state)
            if analysis["incompatiblePermissions"] or any(p["pedestrianInvolved"] for p in analysis["yieldingInteractions"]):
                raise ValueError("Pedestrian service must be protected from all conflicting vehicle permissions")
            if i in self.walk_indices:
                if duration < self.MIN_WALK or any(state[m["signalIndex"]] != "r" for m in self.model.movements[self.tls] if not m["pedestrian"]):
                    raise ValueError("Walk service must be exclusive and long enough")
                served.update(c["signalIndex"] for c in self.crossings if state[c["signalIndex"]] in "Gg")
            elif i in self.green_indices:
                if not self.MIN_GREEN <= duration <= self.MAX_GREEN or any(state[c["signalIndex"]] != "r" for c in self.crossings):
                    raise ValueError("Vehicle green bound or pedestrian exclusion violated")
            elif i in self.closing_indices:
                if state != "r" * len(state) or duration < self.required_clearance:
                    raise ValueError("Pedestrian clearance shortened or conflicting permissions introduced")
            elif i in self.yellow_indices:
                expected = "".join("y" if s in "Gg" else "r" for s in phases[i-1].state)
                if state != expected or duration < self.MIN_YELLOW:
                    raise ValueError("Missing yellow clearance")
            elif state != "r" * len(state) or duration < self.MIN_ALL_RED:
                raise ValueError("Missing all-red clearance")
        if served != {c["signalIndex"] for c in self.crossings}:
            raise ValueError("Program omits pedestrian service")
        if any(not any(p.state[m["signalIndex"]] in "Gg" for p in phases) for m in self.model.movements[self.tls] if not m["pedestrian"]):
            raise ValueError("Program omits a vehicle movement")

    def install(self, phases):
        self.validate_program(phases)
        if traci.simulation.getTime() != 0:
            raise ValueError("Install only at simulation start")
        logic = traci.trafficlight.Logic("synchroflow_max_pressure", 0, 0, phases)
        traci.trafficlight.setProgramLogic(self.tls, logic)
        traci.trafficlight.setProgram(self.tls, logic.programID)
        self.phases = phases
        self.last_served = {g: 0.0 for g in self.green_indices}

    def max_green_duration(self, phase):
        return self.MAX_GREEN

    def clearance_duration(self):
        return 10 + self.required_clearance + self.MIN_YELLOW + self.MIN_ALL_RED

    def validate_duration(self, phase_index, spent, remaining, now):
        if not self.phases or not 0 <= phase_index < len(self.phases):
            raise ValueError("Unknown phase")
        if not all(isfinite(x) for x in (spent, remaining, now)) or spent < 0 or remaining <= 0:
            raise ValueError("Invalid timing")
        total = spent + remaining
        if phase_index in self.green_indices:
            if not self.MIN_GREEN <= total <= self.max_green_duration(phase_index):
                raise ValueError("Green/walk timing bound violated")
            if any(now + remaining + self.clearance_duration() - self.last_served[g] > self.MAX_RED for g in self.green_indices if g != phase_index):
                raise ValueError("Maximum-red fairness requires release")
        elif phase_index in self.walk_indices and not self.MIN_WALK <= total <= 10:
            raise ValueError("Pedestrian walk shortened or overextended")
        elif phase_index in self.closing_indices and (total < self.required_clearance or remaining < 2):
            raise ValueError("Pedestrian clearance shortened")
        elif phase_index in self.yellow_indices and total < self.MIN_YELLOW:
            raise ValueError("Yellow clearance shortened")
        elif phase_index in self.allred_indices and (total < self.MIN_ALL_RED or remaining < 2):
            raise ValueError("All-red clearance shortened")

    def clearance_occupied(self, raw):
        crossing_edges = {c["outgoingLane"].rsplit("_", 1)[0] for c in self.crossings}
        return super().clearance_occupied(raw) or any(p["roadId"] in crossing_edges for p in raw["pedestrians"].values())

    def guard_clearance(self, raw):
        phase = raw["trafficLights"][self.tls]["phaseIndex"]
        remaining = raw["trafficLights"][self.tls]["nextSwitch"] - raw["simTime"]
        if phase in self.allred_indices | self.closing_indices and remaining <= 2 and self.clearance_occupied(raw):
            self.occupancy_holds += 1
            self.apply_duration(phase, 2.0, "pedestrian_or_vehicle_occupancy_clearance_hold")

    def validate_transition(self, origin, target, elapsed, raw):
        if target != (origin + 1) % len(self.phases):
            raise ValueError("Illegal phase transition")
        minimum = self.MIN_GREEN if origin in self.green_indices else self.phases[origin].duration
        if elapsed < minimum:
            raise ValueError("Required service/clearance interval not completed")
        if target in set(self.green_indices) | self.walk_indices and self.clearance_occupied(raw):
            raise ValueError("Crossing or internal junction remains occupied")

    def check_observation(self, raw):
        light = raw["trafficLights"][self.tls]
        phase = light["phaseIndex"]
        if not 0 <= phase < len(self.phases) or light["signalState"] != self.phases[phase].state or light["programId"] != "synchroflow_max_pressure":
            raise ValueError("Signal feedback differs from approved pedestrian program")
        spent = traci.trafficlight.getSpentDuration(self.tls)
        if self.previous_phase is not None and phase != self.previous_phase:
            self.validate_transition(self.previous_phase, phase, raw["simTime"] - self.entered_at, self.previous_raw)
        self.previous_phase = phase
        self.entered_at = raw["simTime"] - spent
        self.previous_raw = raw
        if phase in self.green_indices:
            if spent > self.max_green_duration(phase):
                raise ValueError("Observed walk/green exceeds maximum")
            self.last_served[phase] = raw["simTime"]
        if any(raw["simTime"] - t > self.MAX_RED for t in self.last_served.values()):
            raise ValueError("Maximum red exceeded while waiting for protected clearance; simulation paused")
        state = light["signalState"]
        for crossing in self.crossings:
            edge = crossing["outgoingLane"].rsplit("_", 1)[0]
            if any(p["roadId"] == edge for p in raw["pedestrians"].values()):
                if any(not m["pedestrian"] and self.are_foes(m, crossing) and state[m["signalIndex"]] in "GgyY" for m in self.model.movements[self.tls]):
                    raise ValueError("Occupied crossing has conflicting vehicle permission")

    def report(self):
        return {**super().report(), "status": "enforcing_pedestrian_and_vehicle_timing",
                "pedestrianAdaptiveControl": "protected", "pedestrianClearanceSec": self.required_clearance,
                "designWalkingSpeedMps": self.DESIGN_WALK_SPEED, "occupancyHolds": self.occupancy_holds,
                "reason": "Protected crossings, timed pedestrian closure and occupancy-gated all-red; simulation validation only"}
