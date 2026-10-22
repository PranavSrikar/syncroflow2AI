import traci

from app.services.sumo_adapter import sumo_adapter
from app.services.sumo_telemetry_mapper import (
    sumo_telemetry_mapper,
)   
from app.schemas.traffic import ApproachSignalState

try:
    sumo_adapter.start()

    for _ in range(35):
        raw = sumo_adapter.step()

    mapped = sumo_telemetry_mapper.map_telemetry(raw)
    signals = sumo_telemetry_mapper.map_signals(raw)
    approach_colors = sumo_telemetry_mapper.map_approach_signal_colors(raw)
    
    reusable_approaches = (
        sumo_telemetry_mapper.map_approach_signal_states(raw)
    )

    print("Reusable approach signal states:")
    for direction, signal in reusable_approaches.items():
        print(direction, signal.model_dump())

    phase_timing = sumo_telemetry_mapper.map_phase_timing(raw)
    validated_approaches = {}

    for direction, colors in approach_colors.items():
        validated_approaches[direction] = ApproachSignalState(
            through=colors["through"],
            left=colors["left"],
            right=colors["right"],
            remainingGreen=(
                phase_timing["remainingInPhase"]
                if phase_timing["transitionStage"] == "GREEN"
                and "green" in colors.values()
                else 0.0
            ),
            yellowDuration=3.0,
            allRedDuration=0.0,
        )

    print("Validated approach signals:")
    for direction, signal in validated_approaches.items():
        print(direction, signal.model_dump())

    
    phase_timing = sumo_telemetry_mapper.map_phase_timing(raw)

    print("SUMO phase timing:", phase_timing)


    print("Approach signal colors:", approach_colors)

    print("Mapped traffic signals:", len(signals))
    print("Example mapped signal:", signals[0] if signals else None)
    
    vehicles = sumo_telemetry_mapper.map_vehicles(raw)

    print("Mapped incoming vehicles:", len(vehicles))
    print("Example mapped vehicle:", vehicles[0] if vehicles else None)

    print("Detailed SUMO vehicles:", len(raw["vehicleDetails"]))
    print("Example vehicle:", next(iter(raw["vehicleDetails"].values()), None))


    print("Source:", mapped["source"])
    print("Simulation time:", mapped["simTime"])

    for direction, data in mapped["approaches"].items():
        print(
            direction,
            "vehicles:", data["vehicleCount"],
            "queued:", data["queuedVehicles"],
            "speed (km/h):", round(data["approachSpeed"], 2),
            "average wait (s):", round(data["avgWaitTime"], 2),
        )

    
    print("Traffic lights:", mapped["trafficLights"])

    # Check pedestrians currently present in SUMO
    print("SUMO pedestrian count:", traci.person.getIDCount())

    print("SUMO pedestrian IDs:", list(traci.person.getIDList()))

    print(
        "SUMO traffic light IDs:",
        list(traci.trafficlight.getIDList())
    )

    print("MAPPER TEST PASSED")

finally:
    sumo_adapter.stop()
