from pathlib import Path
import pytest
import traci
from app.services.sumo_network_safety import NetworkSafetyModel
from app.services.pedestrian_supervisor import PedestrianSupervisor


@pytest.fixture
def supervisor():
    path = Path(__file__).resolve().parents[2] / "sumo_scenarios/four_way_basic/junction.pedestrian-test.net.xml"
    model = NetworkSafetyModel(path)
    s = PedestrianSupervisor(model, "center")
    native = [{"state": p.attrib["state"]} for p in model.root.find("tlLogic").findall("phase")]
    s.phases = s.build_program(native)
    s.last_served = {2: 0, 7: 0}
    return s


def test_protected_program_independently_validated(supervisor):
    supervisor.validate_program(supervisor.phases)
    assert supervisor.required_clearance == 15
    assert supervisor.max_green_duration(2) == 45
    for phase in supervisor.phases:
        analysis = supervisor.model.analyze_state("center", phase.state)
        assert not analysis["incompatiblePermissions"]
        assert not any(pair["pedestrianInvolved"] for pair in analysis["yieldingInteractions"])


def test_reject_original_yielding_pedestrian_permissions(supervisor):
    phases = list(supervisor.phases)
    native = supervisor.model.root.find("tlLogic").findall("phase")[0].attrib["state"]
    phases[0] = traci.trafficlight.Phase(11, native)
    with pytest.raises(ValueError, match="protected"):
        supervisor.validate_program(phases)


@pytest.mark.parametrize("phase,spent,remaining", [(0, 1, 1), (2, 44, 2), (1, 2, 1), (3, 1, 1), (4, 0, 1)])
def test_reject_shortened_service_and_clearance(supervisor, phase, spent, remaining):
    with pytest.raises(ValueError):
        supervisor.validate_duration(phase, spent, remaining, 10)


def test_reject_skips_and_occupied_release(supervisor):
    empty = {"vehicleDetails": {}, "pedestrians": {}}
    with pytest.raises(ValueError, match="Illegal"):
        supervisor.validate_transition(0, 7, 30, empty)
    with pytest.raises(ValueError, match="interval"):
        supervisor.validate_transition(1, 2, 5, empty)
    occupied = {"vehicleDetails": {}, "pedestrians": {"walker": {"roadId": ":center_c0"}}}
    with pytest.raises(ValueError, match="occupied"):
        supervisor.validate_transition(1, 2, 15, occupied)
    supervisor.validate_transition(1, 2, 15, empty)
