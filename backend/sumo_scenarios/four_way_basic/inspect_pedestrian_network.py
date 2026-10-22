
from pathlib import Path
import xml.etree.ElementTree as ET

# Locate the SUMO network file
scenario_folder = Path(__file__).resolve().parent
network_file = scenario_folder / "junction.pedestrian-test.net.xml"
print("Inspecting network:", network_file)
print("Network exists:", network_file.is_file())
# Read the XML network
tree = ET.parse(network_file)
root = tree.getroot()

print("NETWORK PEDESTRIAN INSPECTION")
print("-----------------------------")

# Find all pedestrian crossing definitions
crossing_edges = [
    edge
    for edge in root.findall(".//edge")
    if edge.get("function") == "crossing"
]

crossings = crossing_edges

print("Pedestrian crossings found:", len(crossings))

for crossing in crossings:
    print({
        "id": crossing.get("id"),
        "function": crossing.get("function"),
        "crossedEdges": crossing.get("crossingEdges"),
    })


# Check for pedestrian walking lanes
walking_lanes = []

for lane in root.findall(".//lane"):
    if lane.get("allow") == "pedestrian":
        walking_lanes.append(lane.get("id"))

print("Pedestrian-only lanes found:", len(walking_lanes))

for lane_id in walking_lanes:
    print("Walking lane:", lane_id)

print("\nLANE PERMISSION DETAILS")
print("-----------------------")

for edge in root.findall(".//edge"):
    edge_id = edge.get("id", "")

    if edge_id.startswith(":"):
        continue

    for lane in edge.findall("lane"):
        print(
            "Edge:", edge_id,
            "| Lane:", lane.get("id"),
            "| Allow:", lane.get("allow"),
            "| Disallow:", lane.get("disallow")
        )

print("INSPECTION COMPLETE")
