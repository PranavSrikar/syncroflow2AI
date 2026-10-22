"""Numerical and multi-seed safety qualification, not proof of policy usefulness."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'backend'))
from app.rl.mappo import MAPPO
from app.rl.sumo_env import MultiJunctionEnv
from app.services.mappo_coordination import qualification_fingerprint


def qualify(checkpoint, seeds=(101, 102, 103), seconds=240):
    model = MAPPO.load(checkpoint)
    provenance_path = Path(checkpoint).parent / 'training.json'
    training = json.loads(provenance_path.read_text()) if provenance_path.exists() else None
    rng = np.random.default_rng(2026)
    checks = model.agents == 2 and model.observation_size == 8
    checks = checks and all(torch.isfinite(p).all().item() for p in model.parameters())
    for _ in range(128):
        obs = rng.uniform(0, 3, (2, 8)).astype(np.float32)
        action, log, value = model.act(obs, deterministic=True)
        checks = checks and np.isfinite(log).all() and np.isfinite(value).all() and np.isin(action, [0, 1]).all()
        checks = checks and np.array_equal(action, model.act(obs, deterministic=True)[0])
    report = dict(checkpointSha256=hashlib.sha256(Path(checkpoint).read_bytes()).hexdigest(),
                  architectureFingerprint=qualification_fingerprint(),
                  trainedDecisionSteps=model.trained_steps, numericalChecksPassed=bool(checks),
                  eligibleForEvaluation=False, minimumDecisionSteps=1024,
                  status='insufficient_training', usefulnessEstablished=False,
                  validationScope='Finite deterministic inference plus held-out closed-loop supervisor/clearance/conflict/fairness checks; no performance certification')
    if model.trained_steps < 1024 or not checks:
        return report
    if training is None or training.get('provenance', {}).get('architectureFingerprint') != qualification_fingerprint():
        report['status'] = 'missing_current_training_provenance'
        return report
    training_seeds = {u['episodeSeed'] for u in training['updates']}
    if training_seeds.intersection(seeds):
        raise ValueError('Qualification seeds overlap training')
    if len(set(seeds)) < 3 or seconds < 240:
        raise ValueError('At least three distinct held-out seeds and 240 simulated seconds each required')
    faults, trials = 0, []
    for seed in seeds:
        env = MultiJunctionEnv(episode_seconds=seconds)
        try:
            obs = env.reset(seed)
            while True:
                obs, reward, terminal, truncated, info = env.step(model.act(obs, deterministic=True)[0])
                if not np.isfinite(reward).all():
                    raise ValueError('Nonfinite qualification reward')
                if terminal or truncated:
                    break
            trials.append(dict(seed=seed, simTime=info['simTime'], supervisors=info['supervisors']))
        except Exception as exc:
            faults += 1
            trials.append(dict(seed=seed, fault=str(exc)))
        finally:
            env.close()
    report.update(eligibleForEvaluation=False, safetyValidationPassed=faults == 0,
                  status='safety_passed_performance_validation_required' if faults == 0 else 'safety_validation_failed',
                  performanceValidation=dict(passed=False, reason='Safety-only qualification cannot establish comparative usefulness'),
                  closedLoopValidation=dict(seeds=list(seeds), secondsPerSeed=seconds, safetyFaults=faults, trials=trials))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--seeds', type=int, nargs='+', default=[101, 102, 103])
    parser.add_argument('--seconds', type=int, default=240)
    args = parser.parse_args()
    report = qualify(args.checkpoint, args.seeds, args.seconds)
    Path(args.output).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'closedLoopValidation'}, indent=2))
