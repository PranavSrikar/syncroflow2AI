
"""
SYNCHROFLOW AI — SUMO Telemetry Mapper

Converts raw SUMO measurements into normalized traffic data.
This is the first stage of dashboard integration.
"""

from typing import Any, Dict
from app.schemas.traffic import ApproachSignalState


class SumoTelemetryMapper:

    DIRECTIONS = ("north", "south", "east", "west")

    def map_telemetry(
        self, raw: Dict[str, Any]
    ) -> Dict[str, Any]:

        if raw.get("source") != "sumo_traci":
            raise ValueError("Expected SUMO TraCI telemetry")

        approaches = {}

        for direction in self.DIRECTIONS:
            data = raw["approaches"][direction]

            approaches[direction] = {
                "direction": direction,
                "name": f"{direction.capitalize()} Approach",
                "vehicleCount": int(data["vehicles"]),
                "queuedVehicles": int(data["queued"]),
                "approachSpeed": float(
                    data["meanSpeedMps"]
                ) * 3.6,
                "avgWaitTime": float(data["avgWaitTimeSec"]),
                "vehicleIds": list(data["vehicleIds"]),
            }

        return {
            "source": "sumo_traci",
            "simTime": float(raw["simTime"]),
            "approaches": approaches,
            "trafficLights": raw["trafficLights"],
        }


    def map_vehicles(self, raw):
        vehicles = []

        edge_to_direction = {
            "N_in": "north",
            "S_in": "south",
            "E_in": "east",
            "W_in": "west",
        }

        for vehicle_id, data in raw["vehicleDetails"].items():
            road_id = data["roadId"]

            if road_id not in edge_to_direction:
                continue

            direction = edge_to_direction[road_id]
            

            lane_length = float(data["laneLength"])
            lane_position = float(data["lanePosition"])

            distance_to_stop_line = max(
                0.0,
                lane_length - lane_position
            )

            progress = (
                min(1.0, max(0.0, lane_position / lane_length))
                if lane_length > 0
                else 0.0
            )
            
            route_edges = data.get("routeEdges", [])

            movement = "through"

            if len(route_edges) >= 2:
                destination_edge = route_edges[-1]

                movement_lookup = {
                    "N_in": {
                        "S_out": "through",
                        "E_out": "left",
                        "W_out": "right",
                    },
                    "S_in": {
                        "N_out": "through",
                        "W_out": "left",
                        "E_out": "right",
                    },
                    "E_in": {
                        "W_out": "through",
                        "S_out": "left",
                        "N_out": "right",
                    },
                    "W_in": {
                        "E_out": "through",
                        "N_out": "left",
                        "S_out": "right",
                    },
                }

                movement = movement_lookup.get(
                    road_id, {}
                ).get(destination_edge, "through")


          
            vehicles.append({
                "id": vehicle_id,
                "approach": direction,
                "type": "sedan",
                "movement": movement,
                "laneIndex": 0,
                "speed": float(data["speedMps"]),
                "waitingTime": float(data["waitingTimeSec"]),
                "isStopped": float(data["speedMps"]) < 0.1,
                "isEmergency": False,
                "position": data["position"],
                "angle": float(data["angle"]),
                "lanePosition": float(data["lanePosition"]),

                "distanceToStopLine": distance_to_stop_line,
                "progress": progress,
                "length": float(data["vehicleLength"]),
                "width": float(data["vehicleWidth"]),
            })


        return vehicles

    def map_signals(self, raw):
        signals = []

        for light_id, light_data in raw["trafficLights"].items():
            signal_state = light_data["signalState"]
            controlled_links = light_data["controlledLinks"]

            if len(signal_state) != len(controlled_links):
                raise ValueError(
                    f"Signal/link count mismatch for {light_id}"
                )

            for index, link_group in enumerate(controlled_links):
                for incoming_lane, outgoing_lane, via_lane in link_group:
                    signals.append({
                        "trafficLightId": light_id,
                        "signalIndex": index,
                        "incomingLane": incoming_lane,
                        "outgoingLane": outgoing_lane,
                        "viaLane": via_lane,
                        "state": signal_state[index],
                    })

        return signals
        
    def map_approach_signal_colors(self, raw):
        signals = self.map_signals(raw)

        lane_to_direction = {
            "N_in": "north",
            "S_in": "south",
            "E_in": "east",
            "W_in": "west",
        }

        movement_lookup = {
            "N_in": {
                "S_out": "through",
                "E_out": "left",
                "W_out": "right",
            },
            "S_in": {
                "N_out": "through",
                "W_out": "left",
                "E_out": "right",
            },
            "E_in": {
                "W_out": "through",
                "S_out": "left",
                "N_out": "right",
            },
            "W_in": {
                "E_out": "through",
                "N_out": "left",
                "S_out": "right",
            },
        }

        result = {
            direction: {}
            for direction in self.DIRECTIONS
        }

        color_lookup = {
            "G": "green",
            "g": "green",
            "y": "yellow",
            "Y": "yellow",
            "r": "red",
        }

        for signal in signals:
            incoming_edge = signal["incomingLane"].rsplit("_", 1)[0]
            outgoing_edge = signal["outgoingLane"].rsplit("_", 1)[0]

            direction = lane_to_direction.get(incoming_edge)
            if direction is None:
                continue

            movement = movement_lookup.get(
                incoming_edge, {}
            ).get(outgoing_edge)

            if movement is None:
                continue

            raw_state = signal["state"]

            if raw_state not in color_lookup:
                raise ValueError(
                    f"Unsupported SUMO signal state: {raw_state}"
                )

            color = color_lookup[raw_state]

            if movement in result[direction]:
                if result[direction][movement] != color:
                    raise ValueError(
                        f"Conflicting signal colors for "
                        f"{direction} {movement}"
                    )

            result[direction][movement] = color

        return result
        
    def map_phase_timing(self, raw):
        traffic_lights = raw["trafficLights"]

        if len(traffic_lights) != 1:
            raise ValueError(
                "Phase timing mapper currently expects one junction"
            )

        light_id, light_data = next(iter(traffic_lights.items()))

        phases = light_data["phases"]
        current_index = int(light_data["phaseIndex"])

        if not phases or not (0 <= current_index < len(phases)):
            raise ValueError("Invalid SUMO phase information")

        current_phase = phases[current_index]
        phase_duration = float(current_phase["duration"])
        sim_time = float(raw["simTime"])
        next_switch = float(light_data["nextSwitch"])

        remaining = max(0.0, next_switch - sim_time)

        elapsed = max(0.0, phase_duration - remaining)

        cycle_time = sum(
            float(phase["duration"]) for phase in phases
        )

        signal_state = light_data["signalState"]

        if "y" in signal_state or "Y" in signal_state:
            transition_stage = "YELLOW_CLEARANCE"
        elif all(character in "rR" for character in signal_state):
            transition_stage = "ALL_RED_CLEARANCE"
        else:
            transition_stage = "GREEN"

        return {
            "trafficLightId": light_id,
            "currentPhaseIndex": current_index,
            "phaseDuration": phase_duration,
            "elapsedInPhase": elapsed,
            "remainingInPhase": remaining,
            "cycleTime": cycle_time,
            "nextPhaseIndex": (current_index + 1) % len(phases),
            "transitionStage": transition_stage,
        }
    
    def map_approach_signal_states(self, raw):
        colors_by_direction = self.map_approach_signal_colors(raw)
        timing = self.map_phase_timing(raw)

        phases = raw["trafficLights"][timing["trafficLightId"]]["phases"]

        yellow_durations = [
            float(phase["duration"])
            for phase in phases
            if "y" in phase["state"] or "Y" in phase["state"]
        ]

        all_red_durations = [
            float(phase["duration"])
            for phase in phases
            if all(character in "rR" for character in phase["state"])
        ]

        yellow_duration = (
            max(yellow_durations) if yellow_durations else 0.0
        )
        all_red_duration = (
            max(all_red_durations) if all_red_durations else 0.0
        )

        result = {}

        for direction, colors in colors_by_direction.items():
            result[direction] = ApproachSignalState(
                through=colors["through"],
                left=colors["left"],
                right=colors["right"],
                remainingGreen=(
                    timing["remainingInPhase"]
                    if timing["transitionStage"] == "GREEN"
                    and "green" in colors.values()
                    else 0.0
                ),
                yellowDuration=yellow_duration,
                allRedDuration=all_red_duration,
            )

        return result



sumo_telemetry_mapper = SumoTelemetryMapper()
