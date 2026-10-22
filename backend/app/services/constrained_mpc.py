"""Finite-control-set MPC with explicit legal cyclic signal trajectories.

Enumerates feasible remaining-green/next-green plans, propagates fluid queues
at one-second resolution and executes only the first duration recommendation.
No optimizer results are fabricated. Demand is a finite-window estimate and
the default saturation flow is an explicit uncalibrated model parameter.
"""
from math import isfinite
from time import perf_counter
from app.services.max_pressure_controller import MaxPressureController, PCU


class ConstrainedMPC(MaxPressureController):
    HORIZON_SEC = 60
    SOLVE_BUDGET_SEC = 0.05
    SATURATION_PCU_PER_SEC = 0.5  # per approach, configurable only after calibration
    SWITCH_PENALTY = 2.0

    def rollout(self, queues, arrivals, available, groups, phase, remaining, next_green):
        other = self.supervisor.other_green(phase) if hasattr(self, "supervisor") else (3 if phase == 0 else 0)
        # Every service change includes three-second yellow plus two-second all-red.
        clearance = int(self.supervisor.clearance_duration()) if hasattr(self, "supervisor") else 5
        schedule = [(phase, remaining), (None, clearance), (other, next_green), (None, clearance)]
        schedule += [(phase, 10), (None, clearance), (other, 10), (None, clearance)] * 3
        q = dict(queues)
        trajectory, objective, switches, last = [], 0.0, 0, phase
        for service_phase, duration in schedule:
            if service_phase is not None and service_phase != last:
                switches += 1
                last = service_phase
            for _ in range(int(duration)):
                if len(trajectory) >= self.HORIZON_SEC:
                    return objective + sum(q.values()) * 5 + switches * self.SWITCH_PENALTY, trajectory
                for direction in q:
                    rate = arrivals[direction]
                    incoming = rate[min(len(trajectory), len(rate)-1)] if isinstance(rate, list) else rate
                    capacity = self.SATURATION_PCU_PER_SEC * available[direction] if direction in groups.get(service_phase, set()) else 0.0
                    q[direction] = max(0.0, q[direction] + incoming - capacity)
                    objective += q[direction]
                trajectory.append(dict(q))
        # The schedule always covers the horizon with the candidate domains below.
        if len(trajectory) < self.HORIZON_SEC:
            raise ValueError("MPC schedule does not cover horizon")
        return objective + sum(q.values()) * 5 + switches * self.SWITCH_PENALTY, trajectory

    def recommend_remaining(self, raw, phase, spent, scores):
        if spent < self.supervisor.MIN_GREEN or spent >= self.supervisor.max_green_duration(phase):
            return None
        started = perf_counter()
        try:
            defaults = {"north": "N_in", "south": "S_in", "east": "E_in", "west": "W_in"}
            directions = {row.get("edgeId", defaults[d]): d for d, row in raw["approaches"].items()}
            groups = {}
            for green in self.supervisor.green_indices:
                state = self.supervisor.phases[green].state
                groups[green] = {directions[m["incomingLane"].rsplit("_", 1)[0]] for m in self.model.movements[self.tls] if not m["pedestrian"] and state[m["signalIndex"]] in "Gg"}
            queues, arrivals, available = {}, {}, {}
            for direction, row in raw["approaches"].items():
                queues[direction] = sum(PCU.get(raw["vehicleDetails"][v]["vehicleClass"], 1.0) for v in row["vehicleIds"] if raw["vehicleDetails"][v]["speedMps"] <= 0.1)
                rate = raw["stateEstimates"][direction].get('arrivalRatePcuPerSec', raw['stateEstimates'][direction]['arrivalRatePerSec'])
                arrivals[direction] = rate if rate is not None else 0.0
                forecast = raw.get('arrivalForecast') or {}
                prediction = forecast.get('approaches', {}).get(direction) if forecast.get('available') else None
                if prediction:
                    rates = []
                    for slot in prediction['steps']:
                        # PCU/s input matches the existing PCU queue/saturation model.
                        rates.extend([slot['arrivalRatePcuPerSec']] * slot['durationSec'])
                    if len(rates) < self.HORIZON_SEC or any(not isfinite(x) or x < 0 for x in rates):
                        raise ValueError('Invalid arrival forecast')
                    arrivals[direction] = rates[:self.HORIZON_SEC]
                # Conservative static receiver bound for the current straight-route scenario.
                available[direction] = self.receiving_supply(raw, direction)
            arrival_values = [x for rate in arrivals.values() for x in (rate if isinstance(rate, list) else [rate])]
            if any(not isfinite(x) or x < 0 for x in [*queues.values(), *arrival_values, *available.values()]):
                raise ValueError("Invalid MPC observations")
            other = self.supervisor.other_green(phase)
            candidates = []
            maximum = int(self.supervisor.max_green_duration(phase) - spent)
            for remaining in sorted({1, min(2, maximum), min(5, maximum), min(10, maximum)}):
                if remaining < 1:
                    continue
                try:
                    self.supervisor.validate_duration(phase, spent, remaining, raw["simTime"])
                except ValueError:
                    continue
                if raw["simTime"] + remaining + self.supervisor.clearance_duration() - self.supervisor.last_served[other] > self.supervisor.MAX_RED:
                    continue
                for next_green in (10, 20, 30, 45):
                    if next_green > self.supervisor.max_green_duration(other):
                        continue
                    if perf_counter() - started > self.SOLVE_BUDGET_SEC:
                        raise TimeoutError("MPC computation budget exceeded")
                    objective, trajectory = self.rollout(queues, arrivals, available, groups, phase, remaining, next_green)
                    hint = getattr(self, "coordination_hint", None)
                    if hint in (0, 1):
                        objective += 2.0 * abs(remaining - (1 if hint == 0 else min(10, maximum)))
                    candidates.append((objective, remaining, next_green, trajectory))
            if not candidates:
                raise ValueError("No feasible MPC timing candidate")
            best = min(candidates, key=lambda c: (c[0], c[1]))
            self.diagnostics.update({"policy": "constrained_mpc", "objective": best[0],
                "recommendedRemainingSec": best[1], "plannedNextGreenSec": best[2],
                "predictedQueuesPcu": best[3], "feasibleCandidates": len(candidates),
                "solveTimeMs": (perf_counter() - started) * 1000,
                "receivingSupply": available,
                "modelLimitations": "Uncalibrated 0.5 PCU/s; route-weighted static receiver heuristic (straight fallback with no observed routes); optional seasonal arrivals; forecast bounds diagnostic, not robust optimization; no movement-level flow optimization",
                "fallback": None})
            self.diagnostics["coordinationHint"] = getattr(self, "coordination_hint", None)
            self.diagnostics['arrivalForecastSource'] = 'seasonal_shrinkage_baseline' if any(isinstance(x, list) for x in arrivals.values()) else 'recent_observations'
            self.diagnostics['forecastUncertainty'] = (raw.get('arrivalForecast') or {}).get('uncertainty')
            return float(best[1])
        except (ValueError, TimeoutError) as exc:
            self.diagnostics.update({"policy": "max_pressure_fallback", "fallback": str(exc)})
            return super().recommend_remaining(raw, phase, spent, scores)
