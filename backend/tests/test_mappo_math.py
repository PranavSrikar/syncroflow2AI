import numpy as np
import pytest
torch = pytest.importorskip('torch')
from app.rl.mappo import generalized_advantages


def test_gae_matches_hand_calculation_and_time_limit_bootstrap():
    # gamma=1, lambda=.5: last delta=3+4-2=5; first=1+2-1+.5*5=4.5.
    advantage, returns = generalized_advantages([[1,1],[3,3]], [[1,1],[2,2]], [4,4], [False,False], 1, .5)
    np.testing.assert_allclose(advantage, [[4.5,4.5],[5,5]])
    np.testing.assert_allclose(returns, [[5.5,5.5],[7,7]])


def test_gae_terminal_cuts_future_episode_and_bootstrap():
    advantage, _ = generalized_advantages([[1],[100]], [[0],[0]], [999], [True,True], 1, 1)
    np.testing.assert_allclose(advantage, [[1],[100]])


def test_gae_rejects_nonfinite_and_inconsistent_shapes():
    with pytest.raises(ValueError):
        generalized_advantages([[float('nan')]], [[0]], [0], [False])
    with pytest.raises(ValueError):
        generalized_advantages([[1,2]], [[0]], [0], [False])


def test_checkpoint_restores_sampling_rng(tmp_path):
    from app.rl.mappo import MAPPO
    model = MAPPO(seed=123)
    path = tmp_path/'candidate.pt'
    model.save(path)
    observations = np.zeros((2,8), dtype=np.float32)
    expected = [model.act(observations)[0] for _ in range(20)]
    restored = MAPPO.load(path)
    actual = [restored.act(observations)[0] for _ in range(20)]
    np.testing.assert_array_equal(actual, expected)
