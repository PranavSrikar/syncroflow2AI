"""SUMO-verified emergency requests; recommendations never write signal state."""
from collections import deque
import traci
import logging

logger = logging.getLogger("synchroflow.emergency")

APPROACH_EDGES = {"north": "N_in", "south": "S_in", "east": "E_in", "west": "W_in"}
ROUTES = {"north": "north_to_south", "south": "south_to_north", "east": "east_to_west", "west": "west_to_east"}


class EmergencyPriority:
    def __init__(self, approaches=None, routes=None, id_prefix='synchroflow_emergency'):
        self.approach_edges = approaches or APPROACH_EDGES
        self.routes = routes or ROUTES
        self.id_prefix = id_prefix
        self.requests = {}
        self.events = deque(maxlen=500)
        self.selected = None
        self.next_id = 0

    def event(self, time, vehicle, kind, **data):
        self.events.append({"simTime": time, "vehicleId": vehicle, "event": kind, **data})
        logger.info("Emergency event: %s", self.events[-1])

    def register(self, raw, vehicle_id, priority=1):
        if priority not in (1, 2, 3):
            raise ValueError("Priority must be 1, 2 or 3")
        vehicle = raw["vehicleDetails"].get(vehicle_id)
        if vehicle is None or vehicle["vehicleClass"] != "emergency":
            raise ValueError("Request requires an observed SUMO emergency-class vehicle")
        approach = next((d for d, edge in self.approach_edges.items() if edge == vehicle["roadId"]), None)
        if approach is None:
            raise ValueError("Emergency is not on a supported incoming approach")
        if vehicle_id not in self.requests:
            self.requests[vehicle_id] = {"vehicleId": vehicle_id, "approach": approach, "priority": priority,
                                         "state": "approaching", "requestedAt": raw["simTime"], "source": "sumo_traci"}
            self.event(raw["simTime"], vehicle_id, "request_validated", approach=approach, priority=priority)
        else:
            self.requests[vehicle_id]["priority"] = priority
        return self.requests[vehicle_id]

    def inject(self, approach, priority=1):
        if approach not in self.approach_edges or priority not in (1, 2, 3):
            raise ValueError("Invalid emergency injection request")
        if "synchroflow_emergency" not in traci.vehicletype.getIDList():
            traci.vehicletype.copy("car", "synchroflow_emergency")
            traci.vehicletype.setVehicleClass("synchroflow_emergency", "emergency")
            traci.vehicletype.setColor("synchroflow_emergency", (255, 30, 30, 255))
        if traci.vehicletype.getVehicleClass("synchroflow_emergency") != "emergency":
            raise ValueError("Emergency vehicle type is misconfigured")
        self.next_id += 1
        vehicle_id = f"{self.id_prefix}_{self.next_id}"
        if vehicle_id in traci.vehicle.getIDList() or vehicle_id in self.requests:
            raise ValueError("Emergency vehicle ID collision")
        traci.vehicle.add(vehicle_id, self.routes[approach], typeID="synchroflow_emergency", depart="now")
        now = traci.simulation.getTime()
        self.requests[vehicle_id] = {"vehicleId": vehicle_id, "approach": approach, "priority": priority,
                                    "state": "pending_departure", "requestedAt": now, "source": "sumo_injection"}
        self.event(now, vehicle_id, "injection_scheduled", approach=approach)
        return self.requests[vehicle_id]

    def update(self, raw):
        now = raw["simTime"]
        vehicles = raw["vehicleDetails"]
        for vehicle_id, vehicle in vehicles.items():
            if vehicle["vehicleClass"] == "emergency" and vehicle["roadId"] in self.approach_edges.values() and vehicle_id not in self.requests:
                self.register(raw, vehicle_id)
        for vehicle_id, request in self.requests.items():
            vehicle = vehicles.get(vehicle_id)
            old_state = request["state"]
            if old_state in {"completed", "unobserved_departure", "cancelled", "invalid_vehicle_class"}:
                continue
            if vehicle is not None:
                if vehicle["vehicleClass"] != "emergency":
                    request["state"] = "invalid_vehicle_class"
                elif vehicle["roadId"] == self.approach_edges[request["approach"]]:
                    request["state"] = "approaching"
                    distance = max(0.0, vehicle["laneLength"] - vehicle["lanePosition"])
                    request["etaSec"] = distance / max(1.0, vehicle["speedMps"])
                    request["etaMethod"] = "distance / current speed with 1 m/s floor; queue delay uncertain"
                elif vehicle["roadId"].startswith(":"):
                    request["state"] = "entered_junction"
                else:
                    request["state"] = "completed"
                    request["approachResponseSec"] = now - request["requestedAt"]
            elif old_state not in {"pending_departure"}:
                request["state"] = "unobserved_departure"
            if old_state != request["state"]:
                self.event(now, vehicle_id, request["state"])
        candidates = [r for r in self.requests.values() if r["state"] == "approaching"]
        selected = min(candidates, key=lambda r: (-r["priority"], r["requestedAt"], r.get("etaSec", float("inf")), r["vehicleId"])) if candidates else None
        selected_id = selected["vehicleId"] if selected else None
        if selected_id != self.selected:
            self.event(now, selected_id, "priority_selected" if selected_id else "normal_control_recovery")
        self.selected = selected_id

    def recommend(self, raw, supervisor, phase, spent):
        if self.selected is None:
            return None
        request = self.requests[self.selected]
        edge = self.approach_edges[request["approach"]]
        vehicle = raw["vehicleDetails"].get(self.selected)
        if vehicle is None:
            return None
        route_index = vehicle.get('routeIndex', vehicle['routeEdges'].index(edge) if edge in vehicle['routeEdges'] else -1)
        target = vehicle['routeEdges'][route_index+1] if 0 <= route_index < len(vehicle['routeEdges'])-1 else None
        served = any(not m["pedestrian"] and m["incomingLane"].rsplit("_", 1)[0] == edge and m["outgoingLane"].rsplit("_", 1)[0] == target and supervisor.phases[phase].state[m["signalIndex"]] in "Gg" for m in supervisor.model.movements[supervisor.tls])
        if spent < supervisor.MIN_GREEN:
            return None
        maximum = supervisor.max_green_duration(phase)
        if spent >= maximum:
            return None
        return min(2.0, maximum - spent) if served else 1.0

    def snapshot(self):
        return {"activeVehicleId": self.selected, "requests": list(self.requests.values()),
                "events": list(self.events), "selectionRule": "higher priority, then oldest validated request, ETA, vehicle ID",
                "safetyRule": "recommendations preserve minimum service, pedestrian closure, yellow, all-red and maximum-red bounds"}

    def cancel_all(self, now):
        for vehicle, request in self.requests.items():
            if request["state"] not in {"completed", "unobserved_departure", "invalid_vehicle_class", "cancelled"}:
                request["state"] = "cancelled"
                request["cancellationReason"] = "simulation_stopped"
                self.event(now, vehicle, "request_cancelled", reason="simulation_stopped")
        self.selected = None
