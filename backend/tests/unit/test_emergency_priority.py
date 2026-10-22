import pytest
from app.services.emergency_priority import EmergencyPriority


def observation(time=0):
    return {"simTime": time, "vehicleDetails": {
        "ambulance": {"vehicleClass": "emergency", "roadId": "N_in", "laneLength": 250, "lanePosition": 200, "speedMps": 10, "routeEdges": ["N_in", "S_out"]},
        "fire": {"vehicleClass": "emergency", "roadId": "E_in", "laneLength": 250, "lanePosition": 240, "speedMps": 5, "routeEdges": ["E_in", "W_out"]},
        "car": {"vehicleClass": "passenger", "roadId": "N_in"}}}


def test_validation_and_conflicting_request_arbitration():
    service = EmergencyPriority()
    raw = observation()
    with pytest.raises(ValueError):
        service.register(raw, "car")
    with pytest.raises(ValueError):
        service.register(raw, "unknown")
    service.register(raw, "ambulance", 1)
    service.register(raw, "fire", 3)
    service.update(raw)
    assert service.selected == "fire"
    assert service.requests["fire"]["etaSec"] == 2
    raw["vehicleDetails"]["fire"]["roadId"] = ":center_5"
    service.update(raw)
    assert service.selected == "ambulance"
    raw["vehicleDetails"]["ambulance"]["roadId"] = "S_out"
    raw["vehicleDetails"]["fire"]["roadId"] = "W_out"
    raw["simTime"] = 20
    service.update(raw)
    assert service.selected is None
    assert service.requests["ambulance"]["approachResponseSec"] == 20
    assert service.events[-1]["event"] == "normal_control_recovery"


def test_removed_vehicle_does_not_get_false_completion():
    service = EmergencyPriority()
    service.update(observation())
    service.update({"simTime": 1, "vehicleDetails": {}})
    assert service.requests["ambulance"]["state"] == "unobserved_departure"
    assert "approachResponseSec" not in service.requests["ambulance"]


def test_stop_cancels_requests_without_claiming_completion():
    service = EmergencyPriority()
    service.update(observation())
    service.cancel_all(3)
    assert service.selected is None
    assert all(r["state"] == "cancelled" for r in service.requests.values())
    assert all("approachResponseSec" not in r for r in service.requests.values())
    assert all(r["cancellationReason"] == "simulation_stopped" for r in service.requests.values())
