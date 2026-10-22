"""Shared decentralized actor, centralized critic and clipped multi-agent PPO.

Reference: Yu et al., https://arxiv.org/abs/2103.01955.
CPU smoke training does not establish an operationally validated policy.
"""
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.distributions import Categorical


def generalized_advantages(rewards, values, bootstrap, terminals, gamma=0.99, gae_lambda=0.95):
    """True terminals cut bootstrapping; time-limit truncations retain it."""
    reward = torch.as_tensor(np.asarray(rewards), dtype=torch.float32)
    old_values = torch.as_tensor(np.asarray(values), dtype=torch.float32)
    following = torch.as_tensor(bootstrap, dtype=torch.float32)
    if reward.ndim != 2 or old_values.shape != reward.shape or following.shape != reward.shape[1:]:
        raise ValueError('Expected rewards/values [time, agents] and bootstrap [agents]')
    if len(terminals) != len(reward) or not len(reward):
        raise ValueError('One terminal flag per nonempty rollout step required')
    if not all(torch.isfinite(t).all() for t in (reward, old_values, following)):
        raise ValueError('Nonfinite rollout')
    advantage = torch.zeros_like(reward)
    tail = torch.zeros(reward.shape[1])
    for step in reversed(range(len(reward))):
        continuation = 1.0 - float(terminals[step])
        delta = reward[step] + gamma * following * continuation - old_values[step]
        tail = delta + gamma * gae_lambda * continuation * tail
        advantage[step] = tail
        following = old_values[step]
    return advantage, advantage + old_values


class MAPPO(nn.Module):
    def __init__(self, agents=2, observation_size=8, hidden=32, seed=42):
        super().__init__()
        torch.set_num_threads(1)
        torch.manual_seed(seed)
        torch.use_deterministic_algorithms(True)
        self.agents, self.observation_size, self.hidden, self.seed = agents, observation_size, hidden, seed
        self.actor = nn.Sequential(nn.Linear(observation_size, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, 2))
        self.critic = nn.Sequential(nn.Linear(agents * observation_size, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, agents))
        self.optimizer = torch.optim.Adam(self.parameters(), lr=3e-4)
        self.trained_steps = 0

    def distribution(self, observations):
        return Categorical(logits=self.actor(observations))

    @torch.no_grad()
    def act(self, observations, deterministic=False):
        obs = torch.as_tensor(observations, dtype=torch.float32)
        dist = self.distribution(obs)
        actions = torch.argmax(dist.logits, dim=-1) if deterministic else dist.sample()
        values = self.critic(obs.flatten())
        return actions.numpy(), dist.log_prob(actions).numpy(), values.numpy()

    def update(self, observations, actions, log_probs, rewards, values, bootstrap, terminals, epochs=4, gamma=0.99, gae_lambda=0.95):
        obs = torch.as_tensor(np.asarray(observations), dtype=torch.float32)
        acts = torch.as_tensor(np.asarray(actions), dtype=torch.long)
        old_log = torch.as_tensor(np.asarray(log_probs), dtype=torch.float32)
        old_values = torch.as_tensor(np.asarray(values), dtype=torch.float32)
        reward = torch.as_tensor(np.asarray(rewards), dtype=torch.float32)
        advantage, returns = generalized_advantages(reward, old_values, bootstrap, terminals, gamma, gae_lambda)
        normalized = (advantage - advantage.mean()) / (advantage.std(unbiased=False) + 1e-8)
        metrics = {}
        for _ in range(epochs):
            dist = self.distribution(obs)
            ratio = torch.exp(dist.log_prob(acts) - old_log)
            actor_loss = -torch.minimum(ratio * normalized, ratio.clamp(0.8, 1.2) * normalized).mean()
            predicted = self.critic(obs.flatten(start_dim=1))
            clipped = old_values + (predicted - old_values).clamp(-0.2, 0.2)
            value_loss = torch.maximum((predicted - returns).square(), (clipped - returns).square()).mean()
            entropy = dist.entropy().mean()
            loss = actor_loss + 0.5 * value_loss - 0.01 * entropy
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite MAPPO loss")
            self.optimizer.zero_grad()
            loss.backward()
            gradient_norm = nn.utils.clip_grad_norm_(self.parameters(), 0.5)
            self.optimizer.step()
            metrics = {"actorLoss": actor_loss.item(), "valueLoss": value_loss.item(), "entropy": entropy.item(), "gradientNorm": float(gradient_norm)}
        self.trained_steps += len(reward)
        return metrics

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"state": self.state_dict(), "optimizer": self.optimizer.state_dict(),
                    "agents": self.agents, "observation_size": self.observation_size, "hidden": self.hidden,
                    "seed": self.seed, "trained_steps": self.trained_steps, "torch_rng_state": torch.get_rng_state(),
                    "usage": "research_only_unvalidated", "action_semantics": "release_or_hold_preference_to_supervised_mpc"}, path)

    @classmethod
    def load(cls, path):
        data = torch.load(path, map_location="cpu", weights_only=True)
        if data.get("usage") != "research_only_unvalidated":
            raise ValueError("Unknown checkpoint provenance")
        model = cls(data["agents"], data["observation_size"], data["hidden"], data["seed"])
        model.load_state_dict(data["state"])
        model.optimizer.load_state_dict(data["optimizer"])
        model.trained_steps = data["trained_steps"]
        torch.set_rng_state(data["torch_rng_state"])
        return model
