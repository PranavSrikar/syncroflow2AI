"""Network-derived permission analysis, not a real-road safety certification.

SUMO request indices and TLS indices are separate index spaces. sumolib
derives the former from junction incoming-lane/connection ordering.
https://sumo.dlr.de/docs/Networks/SUMO_Road_Networks.html#requests
"""
from itertools import combinations
from math import isfinite
from pathlib import Path
import xml.etree.ElementTree as ET
import sumolib


class NetworkSafetyModel:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.net = sumolib.net.readNet(str(path), withInternal=True, withPrograms=True)
        self.root = ET.parse(path).getroot()
        self.movements = {}
        self.requests = {}
        for junction in self.root.findall("junction"):
            rows = junction.findall("request")
            if not rows:
                continue
            count = len(rows)
            mapped = {}
            for row in rows:
                index = int(row.attrib["index"])
                foes, response = row.attrib["foes"], row.attrib["response"]
                if index in mapped or len(foes) != count or len(response) != count or set(foes + response) - {"0", "1"}:
                    raise ValueError("Malformed junction conflict matrix")
                mapped[index] = (int(foes, 2), int(response, 2))
            if set(mapped) != set(range(count)):
                raise ValueError("Incomplete junction request indices")
            self.requests[junction.attrib["id"]] = mapped
        for edge in self.net.getEdges(withInternal=True):
            for lane in edge.getLanes():
                for connection in lane.getOutgoing():
                    tls = connection.getTLSID()
                    if not tls:
                        continue
                    junction = connection.getJunction().getID()
                    request = connection.getJunctionIndex()
                    if request not in self.requests.get(junction, {}):
                        raise ValueError("Unmapped controlled movement")
                    target = connection.getToLane()
                    self.movements.setdefault(tls, []).append({
                        "signalIndex": connection.getTLLinkIndex(), "requestIndex": request,
                        "junction": junction, "incomingLane": lane.getID(),
                        "outgoingLane": target.getID(),
                        "pedestrian": target.getEdge().getFunction() == "crossing",
                        "crossingLengthM": target.getLength() if target.getEdge().getFunction() == "crossing" else None,
                    })

    def analyze_state(self, tls, state):
        movements = self.movements[tls]
        if len(state) != max(m["signalIndex"] for m in movements) + 1 or set(state) - set("rRyYgGoOu"):
            raise ValueError("Invalid signal state or link count")
        violations, yielding = [], []
        active = [m for m in movements if state[m["signalIndex"]] in "Gg"]
        for a, b in combinations(active, 2):
            if a["junction"] != b["junction"]:
                continue
            rows = self.requests[a["junction"]]
            ia, ib = a["requestIndex"], b["requestIndex"]
            if not ((rows[ia][0] >> ib) & 1 or (rows[ib][0] >> ia) & 1):
                continue
            sa, sb = state[a["signalIndex"]], state[b["signalIndex"]]
            a_yields = sa == "g" and (rows[ia][1] >> ib) & 1
            b_yields = sb == "g" and (rows[ib][1] >> ia) & 1
            pair = {"signals": [a["signalIndex"], b["signalIndex"]],
                    "pedestrianInvolved": a["pedestrian"] or b["pedestrian"]}
            if (a_yields or b_yields) and not (sa == sb == "G"):
                yielding.append(pair)
            else:
                violations.append(pair)
        return {"compatibleUnderSumoRules": not violations,
                "incompatiblePermissions": violations, "yieldingInteractions": yielding}

    def audit(self, walking_speed_mps=1.0):
        if not isfinite(walking_speed_mps) or walking_speed_mps <= 0:
            raise ValueError("Walking speed must be finite and positive")
        programs = []
        for logic in self.root.findall("tlLogic"):
            tls = logic.attrib["id"]
            phases = logic.findall("phase")
            durations = [float(p.attrib["duration"]) for p in phases]
            if any(not isfinite(d) or d <= 0 for d in durations):
                raise ValueError("Invalid phase duration")
            phase_reports = []
            for i, phase in enumerate(phases):
                state = phase.attrib["state"]
                report = self.analyze_state(tls, state)
                clearance = []
                for crossing in self.movements[tls]:
                    s = crossing["signalIndex"]
                    if not crossing["pedestrian"] or state[s] not in "Gg":
                        continue
                    nxt = (i + 1) % len(phases)
                    if phases[nxt].attrib["state"][s] in "Gg":
                        continue
                    # Time from closing this crossing to a conflicting protected vehicle green.
                    available = 0.0
                    found = False
                    for offset in range(1, len(phases) + 1):
                        k = (i + offset) % len(phases)
                        st = phases[k].attrib["state"]
                        foes = self.requests[crossing["junction"]][crossing["requestIndex"]][0]
                        if any(not m["pedestrian"] and (foes >> m["requestIndex"]) & 1 and st[m["signalIndex"]] == "G" for m in self.movements[tls]):
                            found = True
                            break
                        available += durations[k]
                    required = crossing["crossingLengthM"] / walking_speed_mps
                    clearance.append({"signalIndex": s, "requiredSec": required,
                                      "availableSec": available if found else None,
                                      "sufficient": available >= required if found else None})
                phase_reports.append({"phaseIndex": i, "state": state, **report, "clearance": clearance})
            programs.append({"trafficLightId": tls, "programId": logic.attrib["programID"], "phases": phase_reports})
        return {"source": "sumo_network_xml", "walkingSpeedMps": walking_speed_mps,
                "scope": "Static SUMO permission and clearance analysis; occupancy and transitions require runtime supervision",
                "movements": self.movements, "programs": programs}
