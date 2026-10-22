
from pathlib import Path
import xml.etree.ElementTree as ET

scenario_folder = Path(__file__).resolve().parent
network_file = scenario_folder / "junction.pedestrian-test.net.xml"

tree = ET.parse(network_file)
root = tree.getroot()

print("PEDESTRIAN SIGNAL INSPECTION")
print("----------------------------")

# Inspect pedestrian crossings and signal link indices
crossings = [
    edge for edge in root.findall(".//edge")
    if edge.get("function") == "crossing"
]

for crossing in crossings:
    print(
        "Crossing:", crossing.get("id"),
        "| Crossed roads:", crossing.get("crossingEdges"),
        "| Signal link index:", crossing.get("tlLinkIndex")
    )


# Inspect traffic-light programs and pedestrian signals
for logic in root.findall(".//tlLogic"):
    print("\nTraffic light:", logic.get("id"))
    print("Program:", logic.get("programID"))

    phases = logic.findall("phase")

    for index, phase in enumerate(phases):
        print(
            "Phase:", index,
            "| Duration:", phase.get("duration"),
            "| State:", phase.get("state"),
            "| State length:", len(phase.get("state", ""))
        )

    print("\nPEDESTRIAN SIGNAL STATES BY PHASE")

    crossing_indices = {
        "north": 16,
        "east": 17,
        "south": 18,
        "west": 19,
    }

    for phase_index, phase in enumerate(phases):
        state = phase.get("state", "")

        print(
            f"Phase {phase_index} "
            f"(duration {phase.get('duration')} s)"
        )

        for direction, signal_index in crossing_indices.items():
            print(
                f"  {direction}: {state[signal_index]}"
            )



# Inspect controlled connections
print("\nCROSSING SIGNAL CONNECTIONS")

for connection in root.findall(".//connection"):
    from_edge = connection.get("from", "")
    to_edge = connection.get("to", "")

    if from_edge.startswith(":center_c") or to_edge.startswith(":center_c"):
        print(connection.attrib)

print("\nPEDESTRIAN AND VEHICLE GREEN OVERLAP")
print("------------------------------------")

for logic in root.findall(".//tlLogic"):
    for phase_index, phase in enumerate(logic.findall("phase")):
        state = phase.get("state", "")

        pedestrian_green = [
            index
            for index in range(16, len(state))
            if state[index] in ("G", "g")
        ]

        vehicle_green = [
            index
            for index in range(min(16, len(state)))
            if state[index] in ("G", "g")
        ]

        print(
            f"Phase {phase_index}:",
            "pedestrian green indices =", pedestrian_green,
            "| vehicle green indices =", vehicle_green
        )

print("\nVEHICLE SIGNAL CONNECTION MAPPING")
print("---------------------------------")

for connection in root.findall(".//connection"):
    if connection.get("tl") != "center":
        continue

    link_index_text = connection.get("linkIndex")

    if link_index_text is None:
        continue

    link_index = int(link_index_text)

    if link_index >= 16:
        continue

    print(
        f"Signal index: {link_index}",
        f"| From: {connection.get('from')}",
        f"| To: {connection.get('to')}",
        f"| Direction: {connection.get('dir')}",
        f"| From lane: {connection.get('fromLane')}",
        f"| To lane: {connection.get('toLane')}"
    )


print("\nJUNCTION CONFLICT INFORMATION")
print("-----------------------------")

for junction in root.findall(".//junction"):
    if junction.get("id") != "center":
        continue

    print("Junction:", junction.get("id"))
    print("Type:", junction.get("type"))

    requests = junction.findall("request")

    print("Conflict request entries:", len(requests))

    for request in requests:
        print(
            "Index:", request.get("index"),
            "| Response:", request.get("response"),
            "| Foes:", request.get("foes"),
            "| Continue:", request.get("cont")
        )

print("INSPECTION COMPLETE")
