
import traci

# Start SUMO without its graphical interface
traci.start([
    "sumo",
    "-c",
    "junction.sumocfg",
    "--no-step-log"
])

approaches = ["N_in", "S_in", "E_in", "W_in"]

try:
    for step in range(120):
        traci.simulationStep()

        if step % 10 == 0:
            print(f"\nSimulation time: {traci.simulation.getTime()} s")

            for edge in approaches:
                vehicles = traci.edge.getLastStepVehicleNumber(edge)
                halting = traci.edge.getLastStepHaltingNumber(edge)
                speed = traci.edge.getLastStepMeanSpeed(edge)

                print(
                    f"{edge}: "
                    f"vehicles={vehicles}, "
                    f"queued={halting}, "
                    f"mean_speed={speed:.2f} m/s"
                )
finally:
    traci.close()
