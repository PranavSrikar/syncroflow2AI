from app.services.constrained_mpc import ConstrainedMPC


def test_queue_model_conservation_and_receiver_blockage():
    # Exercise the prediction model independently of a running simulator.
    mpc = object.__new__(ConstrainedMPC)
    groups = {0: {"north"}, 3: {"east"}}
    queues = {"north": 10.0, "east": 0.0}
    arrivals = {"north": 0.1, "east": 0.0}
    score, trajectory = mpc.rollout(queues, arrivals, {"north": 1.0, "east": 1.0}, groups, 0, 10, 10)
    assert len(trajectory) == 60
    assert abs(trajectory[0]["north"] - 9.6) < 1e-9
    assert abs(trajectory[9]["north"] - 6.0) < 1e-9
    assert abs(trajectory[10]["north"] - 6.1) < 1e-9  # clearance accumulates arrivals
    blocked_score, blocked = mpc.rollout(queues, arrivals, {"north": 0.0, "east": 1.0}, groups, 0, 10, 10)
    assert abs(blocked[-1]["north"] - 16.0) < 1e-9
    assert blocked_score > score


def test_serving_heavy_queue_reduces_prediction_cost():
    mpc = object.__new__(ConstrainedMPC)
    args = ({"north": 20.0, "east": 0.0}, {"north": 0.2, "east": 0.0}, {"north": 1.0, "east": 1.0}, {0: {"north"}, 3: {"east"}}, 0)
    short, _ = mpc.rollout(*args, 1, 10)
    long, _ = mpc.rollout(*args, 10, 10)
    assert long < short
