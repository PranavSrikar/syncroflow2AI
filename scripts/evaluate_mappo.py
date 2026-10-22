"""Deterministic research evaluation; never enables a policy on the dashboard."""
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.rl.mappo import MAPPO
from app.rl.sumo_env import MultiJunctionEnv
from app.services.mappo_coordination import MAPPOCoordinator


def evaluate(checkpoint, seeds, steps, mode, validation=None):
    if steps < 1 or not seeds:
        raise ValueError('Positive steps and at least one seed required')
    coordinator = MAPPOCoordinator(('A0', 'B0'), checkpoint, validation) if mode == 'mappo' else None
    if coordinator and coordinator.model is None:
        raise ValueError('Policy evaluation refused: '+coordinator.reason)
    model = coordinator.model if coordinator else None
    reports = []
    for seed in seeds:
        env = MultiJunctionEnv(episode_seconds=steps * 5, mode="mpc" if mode == "mappo" else mode)
        try:
            obs = env.reset(seed)
            reward_sum, arrived, start = np.zeros(2), 0, perf_counter()
            for _ in range(steps):
                action = coordinator.recommend(obs) if coordinator else None
                if coordinator and action is None:
                    raise ValueError('Policy inference failed qualification during evaluation: '+coordinator.reason)
                if model is None:
                    # No learned coordination bias for the baseline MPC.
                    for controller in env.controllers.values():
                        controller.coordination_hint = None
                    action = None
                obs, reward, terminal, truncated, info = env.step(action)
                reward_sum += reward
                arrived += info["arrivedVehicles"]
                if terminal or truncated:
                    break
            reports.append({"seed": seed, "controller": mode, "source": "sumo_traci", "simTime": info["simTime"],
                            "arrivedVehicles": arrived, "reward": reward_sum.tolist(), "wallTimeSec": perf_counter() - start})
        finally:
            env.close()
    return {"policyStatus": "qualified_research_only" if model else "non_rl_baseline", "experiments": reports,
            'limitations': 'Short research evaluation; no trained-policy usefulness or superiority established'}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default=".checkpoints/mappo-smoke.pt")
    parser.add_argument("--seeds", type=int, nargs="+", default=[43])
    parser.add_argument("--steps", type=int, default=32)
    parser.add_argument("--mode", choices=["mappo", "mpc", "max_pressure", "fixed_time"], default="mpc")
    parser.add_argument('--validation')
    parser.add_argument("--output")
    args = parser.parse_args()
    result = evaluate(args.checkpoint, args.seeds, args.steps, args.mode, args.validation)
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
