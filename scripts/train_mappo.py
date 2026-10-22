"""Reproducible CPU MAPPO smoke training on two real SUMO intersections."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.rl.mappo import MAPPO
from app.rl.sumo_env import MultiJunctionEnv


def train(updates=2, rollout_steps=32, seed=42, checkpoint=".checkpoints/mappo-smoke.pt"):
    model = MAPPO(seed=seed)
    results = []
    env = MultiJunctionEnv(episode_seconds=rollout_steps * 5)
    try:
        for update in range(updates):
            obs = env.reset(seed + update)
            observations, actions, logs, rewards, values, terminals = [], [], [], [], [], []
            for _ in range(rollout_steps):
                action, log, value = model.act(obs)
                following, reward, terminal, truncated, info = env.step(action)
                observations.append(obs.copy())
                actions.append(action)
                logs.append(log)
                rewards.append(reward)
                values.append(value)
                terminals.append(terminal)
                obs = following
                if terminal or truncated:
                    break
            _, _, bootstrap = model.act(obs, deterministic=True)
            metrics = model.update(observations, actions, logs, rewards, values, bootstrap, terminals)
            results.append({"update": update, "seed": seed + update, "sumReward": np.sum(rewards, axis=0).tolist(), "simTime": info["simTime"], **metrics})
            model.save(checkpoint)
    finally:
        env.close()
    report = {"source": "actual_two_junction_sumo", "checkpoint": str(checkpoint),
              "trainedDecisionSteps": model.trained_steps, "status": "smoke_only_unvalidated", "updates": results}
    Path(checkpoint).with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--updates", type=int, default=2)
    parser.add_argument("--rollout-steps", type=int, default=32)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--checkpoint", default=".checkpoints/mappo-smoke.pt")
    args = parser.parse_args()
    if args.updates < 1 or args.rollout_steps < 1:
        parser.error("Positive updates and rollout steps required")
    print(json.dumps(train(args.updates, args.rollout_steps, args.seed, args.checkpoint), indent=2))
