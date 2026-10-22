"""Finite-window rates from unique SUMO identities, never synthetic camera data."""
from collections import deque
from app.services.max_pressure_controller import PCU


class TrafficEstimator:
    def __init__(self, window_sec=60.0):
        self.window = window_sec
        self.previous = None
        self.events = {d: deque() for d in ("north", "south", "east", "west")}

    def update(self, raw):
        now = raw["simTime"]
        if self.previous is not None and now < self.previous["simTime"]:
            self.__init__(self.window)
        result = {}
        for direction, row in raw["approaches"].items():
            ids = set(row["vehicleIds"])
            events = self.events[direction]
            if self.previous is not None and now > self.previous["simTime"]:
                old = set(self.previous["approaches"][direction]["vehicleIds"])
                # Only count departures observed on a different road; disappeared
                # identities may be teleported/removed and are not proven discharge.
                departed = sum(v in raw["vehicleDetails"] and raw["vehicleDetails"][v]["roadId"] != self.previous["vehicleDetails"][v]["roadId"] for v in old - ids)
                arriving_pcu = sum(PCU.get(raw['vehicleDetails'][v]['vehicleClass'], 1.0) for v in ids-old)
                events.append((now, len(ids - old), departed, arriving_pcu))
            while events and events[0][0] <= now - self.window:
                events.popleft()
            first_time = self.previous.get("observationStart", now) if self.previous else now
            exposure = min(self.window, now - first_time)
            counts = {}
            for v in ids:
                cls = raw["vehicleDetails"][v]["vehicleClass"]
                counts[cls] = counts.get(cls, 0) + 1
            result[direction] = {
                "vehicleClasses": counts,
                "arrivalRatePerSec": sum(e[1] for e in events) / exposure if exposure > 0 else None,
                "arrivalRatePcuPerSec": sum(e[3] for e in events) / exposure if exposure > 0 else None,
                "observedDischargePerSec": sum(e[2] for e in events) / exposure if exposure > 0 else None,
                "rateWindowSec": exposure,
                "measurementSource": "sumo_traci", "uncertainty": "Exact simulator counts; finite-window rates are estimates, not forecasts",
            }
        raw["observationStart"] = self.previous.get("observationStart", now) if self.previous else now
        self.previous = raw
        return result
