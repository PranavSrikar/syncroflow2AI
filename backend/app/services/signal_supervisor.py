"""Authoritative gate for adaptive vehicle-only SUMO program and duration writes.

Pedestrian adaptive control is deliberately rejected until runtime clearance
supervision is implemented. The independent network model permits documented
SUMO yielding interactions; this does not certify public-road safety.
"""
from math import isfinite
from collections import deque
import traci


class SignalFeedbackFault(RuntimeError):
    """Live feedback is inconsistent; do not advance SUMO on a cached snapshot."""


class SignalSupervisor:
    MIN_GREEN = 10.0
    MAX_GREEN = 45.0
    MIN_YELLOW = 3.0
    MIN_ALL_RED = 2.0
    MAX_RED = 120.0

    def __init__(self, model, tls):
        self.model, self.tls = model, tls
        self.phases = []
        self.green_indices = []
        self.last_served = {}
        self.last_decision = None
        self.accepted = 0
        self.rejected = 0
        self.closing_indices = set()
        self.yellow_indices = {1, 4}
        self.allred_indices = {2, 5}
        self.previous_phase = None
        self.previous_raw = None
        self.entered_at = 0.0
        self.decisions = deque(maxlen=100)

    def other_green(self, phase):
        return next(g for g in self.green_indices if g != phase)

    def max_green_duration(self, phase):
        return self.MAX_GREEN

    def clearance_duration(self):
        return self.MIN_YELLOW + self.MIN_ALL_RED

    def clearance_occupied(self, raw):
        junctions = {m['junction'] for m in self.model.movements[self.tls]}
        return any(any(v['roadId'].startswith(':'+j+'_') for j in junctions) for v in raw['vehicleDetails'].values())

    def guard_clearance(self, raw):
        phase = raw["trafficLights"][self.tls]["phaseIndex"]
        if phase in self.allred_indices and self.clearance_occupied(raw):
            self.apply_duration(phase, 2.0, "occupancy_clearance_hold")

    def validate_program(self, phases):
        if any(m["pedestrian"] for m in self.model.movements[self.tls]):
            raise ValueError("Adaptive pedestrian control is not yet validated")
        if len(phases) != 6:
            raise ValueError("Vehicle supervisor requires two green/yellow/all-red groups")
        for i, phase in enumerate(phases):
            state, duration = phase.state, phase.duration
            if not isfinite(duration) or duration <= 0:
                raise ValueError("Invalid duration")
            if not self.model.analyze_state(self.tls, state)["compatibleUnderSumoRules"]:
                raise ValueError("Incompatible signal permissions")
            stage = i % 3
            if stage == 0:
                if not self.MIN_GREEN <= duration <= self.MAX_GREEN or not any(s in "Gg" for s in state):
                    raise ValueError("Invalid green duration/state")
            elif stage == 1:
                expected = "".join("y" if s in "Gg" else "r" for s in phases[i-1].state)
                if state != expected or duration < self.MIN_YELLOW:
                    raise ValueError("Missing yellow clearance")
            elif state != "r" * len(state) or duration < self.MIN_ALL_RED:
                raise ValueError("Missing all-red clearance")

    def install(self, phases):
        self.validate_program(phases)
        if traci.simulation.getTime() != 0:
            raise ValueError("Install adaptive programs only at simulation start")
        logic = traci.trafficlight.Logic("synchroflow_max_pressure", 0, 0, phases)
        traci.trafficlight.setProgramLogic(self.tls, logic)
        traci.trafficlight.setProgram(self.tls, logic.programID)
        self.phases = phases
        self.green_indices = [0, 3]
        self.last_served = {0: 0.0, 3: 0.0}

    def validate_duration(self, phase_index, spent, remaining, now):
        if not self.phases or not 0 <= phase_index < len(self.phases):
            raise ValueError("Unknown phase")
        if not all(isfinite(x) for x in (spent, remaining, now)) or spent < 0 or remaining <= 0:
            raise ValueError("Invalid phase timing")
        total = spent + remaining
        if phase_index % 3 == 0:
            if not self.MIN_GREEN <= total <= self.MAX_GREEN:
                raise ValueError("Green timing bound violated")
            if any(now + remaining + self.clearance_duration() - self.last_served[g] > self.MAX_RED for g in self.green_indices if g != phase_index):
                raise ValueError("Maximum-red fairness requires release")
        elif phase_index % 3 == 1 and total < self.MIN_YELLOW:
            raise ValueError("Yellow clearance shortened")
        elif phase_index % 3 == 2 and total < self.MIN_ALL_RED:
            raise ValueError("All-red clearance shortened")

    def apply_duration(self, phase_index, remaining, reason):
        try:
            actual = traci.trafficlight.getPhase(self.tls)
            state = traci.trafficlight.getRedYellowGreenState(self.tls)
            if traci.trafficlight.getProgram(self.tls) != 'synchroflow_max_pressure':
                raise SignalFeedbackFault('Unapproved live signal program; simulation must pause')
            if actual != phase_index or state != self.phases[phase_index].state:
                raise SignalFeedbackFault("Candidate does not match active approved phase")
            spent = traci.trafficlight.getSpentDuration(self.tls)
            self.validate_duration(phase_index, spent, remaining, traci.simulation.getTime())
            traci.trafficlight.setPhaseDuration(self.tls, remaining)
            self.accepted += 1
            self.last_decision = {"accepted": True, "phaseIndex": phase_index, "remainingSec": remaining, "reason": reason}
            self.decisions.append({'simTime': traci.simulation.getTime(), **self.last_decision})
        except Exception as exc:
            self.rejected += 1
            self.last_decision = {"accepted": False, "reason": str(exc)}
            self.decisions.append({'simTime': traci.simulation.getTime(), **self.last_decision})
            raise

    def verify_live_feedback(self, raw):
        light = raw['trafficLights'][self.tls]
        if (traci.trafficlight.getPhase(self.tls) != light['phaseIndex']
            or traci.trafficlight.getProgram(self.tls) != light['programId']
            or traci.trafficlight.getRedYellowGreenState(self.tls) != light['signalState']):
            raise SignalFeedbackFault('Live signal feedback differs from last observation; simulation paused before stepping')

    def check_observation(self, raw):
        light = raw["trafficLights"][self.tls]
        phase = light["phaseIndex"]
        if not 0 <= phase < len(self.phases) or light["signalState"] != self.phases[phase].state:
            raise ValueError("Signal feedback differs from approved program")
        if light["programId"] != "synchroflow_max_pressure":
            raise ValueError("Unapproved active signal program")
        spent = traci.trafficlight.getSpentDuration(self.tls)
        if self.previous_phase is not None and phase != self.previous_phase:
            if phase != (self.previous_phase + 1) % len(self.phases):
                raise ValueError('Illegal phase transition')
            minimum = self.MIN_GREEN if self.previous_phase in self.green_indices else self.phases[self.previous_phase].duration
            if raw['simTime']-self.entered_at < minimum:
                raise ValueError('Required service/clearance interval not completed')
            if phase in self.green_indices and self.clearance_occupied(self.previous_raw):
                raise ValueError('Internal junction remains occupied before green')
        self.previous_phase, self.previous_raw = phase, raw
        self.entered_at = raw['simTime']-spent
        if phase in self.green_indices:
            if traci.trafficlight.getSpentDuration(self.tls) > self.MAX_GREEN:
                raise ValueError("Observed green exceeds supervisor maximum")
            self.last_served[phase] = raw["simTime"]
        if any(raw["simTime"] - t > self.MAX_RED for t in self.last_served.values()):
            raise ValueError("Maximum-red bound exceeded; pause for blocked-clearance recovery")

    def report(self):
        return {"status": "enforcing_vehicle_timing", "reason": "Validated cyclic program; green/yellow/all-red bounds and red fairness gate; clearance occupancy hold",
                "acceptedActions": self.accepted, "rejectedActions": self.rejected,
                "decisions": list(self.decisions),
                "lastDecision": self.last_decision, "pedestrianAdaptiveControl": "disabled"}
