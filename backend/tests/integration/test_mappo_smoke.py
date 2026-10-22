from pathlib import Path
import shutil
import numpy as np
import pytest

torch = pytest.importorskip("torch")
from app.rl.mappo import MAPPO
from app.rl.sumo_env import MultiJunctionEnv


@pytest.mark.skipif(shutil.which("sumo") is None, reason="SUMO required")
def test_two_agent_training_checkpoint_and_decentralized_inference(tmp_path):
    env = MultiJunctionEnv(episode_seconds=80)
    model = MAPPO(seed=17)
    before = {k: v.clone() for k, v in model.actor.state_dict().items()}
    critic_before = {k: v.clone() for k, v in model.critic.state_dict().items()}
    observations, actions, logs, rewards, values, terminals = [], [], [], [], [], []
    try:
        obs = env.reset(17)
        assert obs.shape == (2, 8)
        for _ in range(16):
            action, log, value = model.act(obs)
            following, reward, terminal, truncated, info = env.step(action)
            observations.append(obs.copy())
            actions.append(action)
            logs.append(log)
            rewards.append(reward)
            values.append(value)
            terminals.append(terminal)
            obs = following
            assert info['coordinationRecommendations'] == action.tolist()
            assert all(c.coordination_hint == int(action[i]) for i, c in enumerate(env.controllers.values()))
        assert info["source"] == "sumo_traci"
        assert set(info["supervisors"]) == {"A0", "B0"}
        _, _, bootstrap = model.act(obs, deterministic=True)
        metrics = model.update(observations, actions, logs, rewards, values, bootstrap, terminals)
        assert all(np.isfinite(v) for v in metrics.values())
        assert any(not torch.equal(before[k], v) for k, v in model.actor.state_dict().items())
        assert any(not torch.equal(critic_before[k], v) for k, v in model.critic.state_dict().items())
        checkpoint = tmp_path / "smoke.pt"
        model.save(checkpoint)
        restored = MAPPO.load(checkpoint)
        np.testing.assert_array_equal(model.act(obs, deterministic=True)[0], restored.act(obs, deterministic=True)[0])
        # Each decentralized actor output depends only on that agent's local observation.
        changed = obs.copy()
        changed[1] += 1
        with torch.no_grad():
            np.testing.assert_array_equal(model.actor(torch.tensor(obs))[0].numpy(), model.actor(torch.tensor(changed))[0].numpy())
        assert restored.trained_steps == 16
    finally:
        env.close()
