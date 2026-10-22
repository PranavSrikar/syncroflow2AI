from app.services.traffic_estimation import TrafficEstimator


def sample(time, ids, roads=None):
    return {
        "simTime": time,
        "approaches": {d: {"vehicleIds": ids if d == "north" else []} for d in ("north", "south", "east", "west")},
        "vehicleDetails": {v: {"vehicleClass": "bus" if v == "b" else "passenger", "roadId": road} for v, road in (roads or {v: "N_in" for v in ids}).items()},
    }


def test_rates_count_new_ids_and_only_proven_discharge():
    estimator = TrafficEstimator()
    assert estimator.update(sample(0, ["a"]))["north"]["arrivalRatePerSec"] is None
    result = estimator.update(sample(2, ["b"], {"a": ":center_1", "b": "N_in"}))["north"]
    assert result["arrivalRatePerSec"] == 0.5
    assert result["observedDischargePerSec"] == 0.5
    assert result["vehicleClasses"] == {"bus": 1}
    result = estimator.update(sample(4, []))["north"]
    assert result["observedDischargePerSec"] == 0.25  # removed b is not proven discharge


def test_window_expiry_and_restart():
    estimator = TrafficEstimator(window_sec=10)
    estimator.update(sample(0, []))
    estimator.update(sample(1, ["a"]))
    assert estimator.update(sample(12, ["a"]))["north"]["arrivalRatePerSec"] == 0
    assert estimator.update(sample(0, []))["north"]["arrivalRatePerSec"] is None
