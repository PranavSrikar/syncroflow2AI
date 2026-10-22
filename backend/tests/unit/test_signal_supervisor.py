from pathlib import Path
import pytest
import traci
from app.services.sumo_network_safety import NetworkSafetyModel
from app.services.signal_supervisor import SignalSupervisor


@pytest.fixture
def supervisor():
    path = Path(__file__).resolve().parents[2] / "sumo_scenarios/four_way_basic/junction.net.xml"
    model = NetworkSafetyModel(path)
    native = model.root.find("tlLogic").findall("phase")
    s = SignalSupervisor(model, "center")
    phases = []
    for i in (0, 2):
        state = native[i].attrib["state"]
        phases.extend([traci.trafficlight.Phase(11, state), traci.trafficlight.Phase(3, native[i+1].attrib["state"]), traci.trafficlight.Phase(2, "r" * len(state))])
    s.phases = phases
    s.green_indices = [0, 3]
    s.last_served = {0: 0.0, 3: 0.0}
    return s


def test_legal_program_and_timing(supervisor):
    supervisor.validate_program(supervisor.phases)
    supervisor.validate_duration(0, 10, 2, 10)


@pytest.mark.parametrize("phase,spent,remaining,now", [(0, 1, 1, 1), (0, 44, 2, 44), (1, 0, 1, 12), (2, 0, 1, 15), (0, 10, 2, 120), (0, 10, float('nan'), 10)])
def test_unsafe_durations_rejected(supervisor, phase, spent, remaining, now):
    with pytest.raises(ValueError):
        supervisor.validate_duration(phase, spent, remaining, now)


def test_conflicting_green_program_rejected(supervisor):
    phases = list(supervisor.phases)
    phases[0] = traci.trafficlight.Phase(11, "G" * len(phases[0].state))
    with pytest.raises(ValueError, match="Incompatible"):
        supervisor.validate_program(phases)


def test_missing_clearance_rejected(supervisor):
    phases = list(supervisor.phases)
    phases[2] = traci.trafficlight.Phase(1, phases[2].state)
    with pytest.raises(ValueError, match="all-red"):
        supervisor.validate_program(phases)
