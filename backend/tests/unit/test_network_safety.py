from pathlib import Path
import pytest
from app.services.sumo_network_safety import NetworkSafetyModel

SCENARIO = Path(__file__).resolve().parents[2] / "sumo_scenarios" / "four_way_basic"


@pytest.fixture
def model():
    return NetworkSafetyModel(SCENARIO / "junction.pedestrian-test.net.xml")


def test_crossings_derived_from_actual_connections(model):
    crossings = [m for m in model.movements["center"] if m["pedestrian"]]
    assert len(crossings) == 4
    assert {m["outgoingLane"] for m in crossings} == {f":center_c{i}_0" for i in range(4)}
    assert all(m["crossingLengthM"] == 6.4 for m in crossings)
    assert {m["requestIndex"] for m in crossings} == {16, 17, 18, 19}


def test_bit_orientation_and_yielding_are_distinguished(model):
    # Request zero has crossing 19 as its foe and yields to it.
    state = list("r" * 20)
    state[0], state[19] = "g", "G"
    report = model.analyze_state("center", "".join(state))
    assert report["compatibleUnderSumoRules"]
    assert report["yieldingInteractions"] == [{"signals": [19, 0], "pedestrianInvolved": True}]
    state[0] = "G"
    assert not model.analyze_state("center", "".join(state))["compatibleUnderSumoRules"]


def test_program_audit_measures_clearance(model):
    report = model.audit()
    phases = report["programs"][0]["phases"]
    assert len(phases) == 6
    clearances = [c for phase in phases for c in phase["clearance"]]
    assert len(clearances) == 4
    assert all(c["requiredSec"] == 6.4 for c in clearances)
    assert all(c["availableSec"] == 8 for c in clearances)
    assert all(c["sufficient"] for c in clearances)
    # Slower walkers expose insufficient clearance instead of hardcoded success.
    assert any(not c["sufficient"] for phase in model.audit(0.5)["programs"][0]["phases"] for c in phase["clearance"])


@pytest.mark.parametrize("speed", [0, -1, float("nan"), float("inf")])
def test_reject_invalid_walking_speed(model, speed):
    with pytest.raises(ValueError):
        model.audit(speed)


def test_bad_signal_length_rejected(model):
    with pytest.raises(ValueError):
        model.analyze_state("center", "GG")
