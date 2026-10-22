
from app.services.sumo_adapter import sumo_adapter

try:
    sumo_adapter.start()

    for i in range(60):
        telemetry = sumo_adapter.step()

        if i % 10 == 0:
            print(telemetry)

finally:
    sumo_adapter.stop()
