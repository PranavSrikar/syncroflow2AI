
from pathlib import Path
import traci


class SumoAdapter:
    """Read real traffic measurements from a SUMO simulation."""

    APPROACHES = {
        "north": "N_in",
        "south": "S_in",
        "east": "E_in",
        "west": "W_in",
    }

    def __init__(self, approaches=None, departures=None, light_ids=None):
        self.APPROACHES = dict(approaches or self.APPROACHES)
        self.departures = departures or {d: edge.replace("_in", "_out") for d, edge in self.APPROACHES.items()}
        self.light_ids = light_ids
        self.config_path = (
            Path(__file__).resolve().parents[2]
            / "sumo_scenarios"
            / "four_way_basic"
            / "junction.sumocfg"
        )
        self.connected = False

    def start(self, seed=23423):
        if self.connected:
            raise RuntimeError("SUMO is already connected")

        if not self.config_path.is_file():
            raise FileNotFoundError(self.config_path)

        traci.start([
            "sumo",
            "-c",
            str(self.config_path),
            "--no-step-log",
            '--seed', str(seed),
        ])
        self.connected = True

    def step(self):
        if not self.connected:
            raise RuntimeError("SUMO is not connected")

        traci.simulationStep()
        return self.get_telemetry()

    def get_telemetry(self):
        if not self.connected:
            raise RuntimeError("SUMO is not connected")

        approaches = {}
        
        traffic_lights = {}
        
        
        vehicle_details = {}

        for vehicle_id in traci.vehicle.getIDList():
            vehicle_details[vehicle_id] = {
                "id": vehicle_id,
                "roadId": traci.vehicle.getRoadID(vehicle_id),
                "laneId": traci.vehicle.getLaneID(vehicle_id),
                "lanePosition": traci.vehicle.getLanePosition(vehicle_id),
                "laneLength": traci.lane.getLength(
                    traci.vehicle.getLaneID(vehicle_id)
                ),
                "vehicleLength": traci.vehicle.getLength(vehicle_id),
                "vehicleWidth": traci.vehicle.getWidth(vehicle_id),
                "speedMps": traci.vehicle.getSpeed(vehicle_id),
                "waitingTimeSec": traci.vehicle.getWaitingTime(vehicle_id),
                "typeId": traci.vehicle.getTypeID(vehicle_id),
                "routeId": traci.vehicle.getRouteID(vehicle_id),
                "routeEdges": list(traci.vehicle.getRoute(vehicle_id)),
                "routeIndex": traci.vehicle.getRouteIndex(vehicle_id),
                "vehicleClass": traci.vehicle.getVehicleClass(vehicle_id),
                "position": traci.vehicle.getPosition(vehicle_id),
                "angle": traci.vehicle.getAngle(vehicle_id),
            }




        
        for light_id in traci.trafficlight.getIDList():
            if self.light_ids is not None and light_id not in self.light_ids:
                continue
            
            current_program = traci.trafficlight.getProgram(light_id)
            programs = traci.trafficlight.getAllProgramLogics(light_id)

            active_program = next(
                (program for program in programs
                 if program.programID == current_program),
                None
            )

            phases = (
                [
                    {
                        "duration": float(phase.duration),
                        "state": phase.state,
                    }
                    for phase in active_program.phases
                ]
                if active_program is not None
                else []
            )

            traffic_lights[light_id] = {
                "phaseIndex": traci.trafficlight.getPhase(light_id),
                "signalState": traci.trafficlight.getRedYellowGreenState(light_id),
                "nextSwitch": traci.trafficlight.getNextSwitch(light_id),
                "controlledLinks": traci.trafficlight.getControlledLinks(light_id),
                "programId": current_program,
                "phases": phases,
            }



        for direction, edge in self.APPROACHES.items():
            
            vehicle_ids = traci.edge.getLastStepVehicleIDs(edge)

            waiting_times = [
                traci.vehicle.getWaitingTime(vehicle_id)
                for vehicle_id in vehicle_ids
            ]

            average_wait = (
                sum(waiting_times) / len(waiting_times)
                if waiting_times else 0.0
            )

            approaches[direction] = {
                "edgeId": edge,
                "vehicles": traci.edge.getLastStepVehicleNumber(edge),
                "queued": traci.edge.getLastStepHaltingNumber(edge),
                "meanSpeedMps": traci.edge.getLastStepMeanSpeed(edge),
                "vehicleIds": list(vehicle_ids),
                "avgWaitTimeSec": average_wait,
            }
        
        downstream = {}
        for direction in self.APPROACHES:
            edge = self.departures[direction]
            # SUMO 1.28 returns a net occupied-length ratio here despite the
            # Python API docstring calling it percent. Verified against actual
            # stopped vehicle length / lane length in the spillback fixture.
            fraction = traci.edge.getLastStepOccupancy(edge)
            percent = 100.0 * fraction
            downstream[direction] = {
                'edgeId': edge, 'occupancyFraction': fraction, 'occupancyPercent': percent,
                'queuedVehicles': traci.edge.getLastStepHaltingNumber(edge),
                'spillbackIndicator': percent >= 80.0,
                'spillbackDefinition': 'net occupied length >= 80%; heuristic, not a verified blocked exit',
            }
        return {
            "source": "sumo_traci",
            "simTime": traci.simulation.getTime(),
            "approaches": approaches,
            "trafficLights": traffic_lights,
            "vehicleDetails": vehicle_details,
            "downstream": downstream,
            "pedestrians": {
                person: {
                    "roadId": traci.person.getRoadID(person),
                    "nextEdge": traci.person.getNextEdge(person),
                    "laneId": traci.person.getLaneID(person),
                    "speedMps": traci.person.getSpeed(person),
                    "waitingTimeSec": traci.person.getWaitingTime(person),
                    "position": traci.person.getPosition(person),
                } for person in traci.person.getIDList()
            },
        }



    def stop(self):
        if self.connected:
            try:
                traci.close()
            finally:
                self.connected = False


sumo_adapter = SumoAdapter()
