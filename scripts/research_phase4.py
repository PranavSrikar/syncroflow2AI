"""Reproducible offline research. Candidate hints never enable an operational policy.

Every candidate recommendation uses the existing MPC and independent supervisors.
Training, selection and final-test seeds are deliberately separate.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time
import xml.etree.ElementTree as ET

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
os.environ['DEBUG'] = 'false'
for name in ('SYNCHROFLOW_MAPPO_CHECKPOINT','SYNCHROFLOW_MAPPO_VALIDATION'):
    os.environ.pop(name,None)  # isolated research never inherits operational policy activation
from app.rl.mappo import MAPPO
from app.rl.sumo_env import MultiJunctionEnv
from app.services.mappo_coordination import qualification_fingerprint
import torch
import traci

OUT = ROOT / '.checkpoints/phase4-demand-corrected'


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')
    temporary.replace(path)


def provenance():
    return dict(python=platform.python_version(), torch=torch.__version__, numpy=np.__version__,
                cuda=torch.cuda.is_available(), logicalCPUs=os.cpu_count(),
                architectureFingerprint=qualification_fingerprint(),
                sourceHashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in [Path(__file__), ROOT/'backend/app/rl/sumo_env.py',
                                        ROOT/'backend/sumo_scenarios/two_junction/corridor.rou.xml']})


def train(seed, updates, rollout, resume=False):
    folder = OUT / f'train-{seed}'
    report_path = folder/'training.json'
    if report_path.exists() and not resume:
        raise ValueError('Training exists; use --resume or a new seed; never overwrite a run')
    report = json.loads(report_path.read_text()) if resume else dict(
        modelSeed=seed, rolloutSteps=rollout, decisionSeconds=5, gamma=.99, gaeLambda=.95,
        learningRate=.0003, epochs=4, clip=.2, entropyCoefficient=.01,
        observationRepresentation='occupancy_fraction_corrected_stage3', provenance=provenance(),
        startedUtc=datetime.now(timezone.utc).isoformat(), updates=[],
        status='unvalidated_research_candidate', operationallyEnabled=False)
    if resume and (report['rolloutSteps'] != rollout or report['provenance'] != provenance()):
        raise ValueError('Resume configuration/source mismatch')
    model = MAPPO.load(report['latestCheckpoint']) if resume else MAPPO(seed=seed)
    env = MultiJunctionEnv(episode_seconds=rollout*5)
    try:
        for update in range(len(report['updates']), updates):
            started = time.perf_counter()
            episode_seed = seed*1000+update
            obs = env.reset(episode_seed)
            observations, actions, logs, rewards, values, terminals = [], [], [], [], [], []
            for _ in range(rollout):
                action, log, value = model.act(obs)
                following, reward, terminal, truncated, info = env.step(action)
                observations.append(obs.copy()); actions.append(action); logs.append(log)
                rewards.append(reward); values.append(value); terminals.append(terminal)
                obs = following
                if terminal or truncated:
                    break
            bootstrap = model.act(obs, deterministic=True)[2]
            metrics = model.update(observations, actions, logs, rewards, values, bootstrap, terminals)
            checkpoint = folder/f'update-{update+1:04d}.pt'
            if checkpoint.exists():
                raise ValueError('Refusing to overwrite checkpoint')
            model.save(checkpoint)
            row = dict(update=update+1, episodeSeed=episode_seed,
                       trainedDecisionSteps=model.trained_steps, reward=np.sum(rewards, axis=0).tolist(),
                       simTime=info['simTime'], wallSeconds=time.perf_counter()-started,
                       arrivedVehicles=env.network.total_arrived, **metrics)
            report['updates'].append(row)
            report.update(latestCheckpoint=str(checkpoint), trainedDecisionSteps=model.trained_steps,
                          elapsedSeconds=sum(r['wallSeconds'] for r in report['updates']))
            write(report_path, report)
            print(json.dumps(row), flush=True)
            env.close()
    finally:
        env.close()
    return report


def trial(mode, seed, seconds, scale, checkpoint=None, split='test'):
    """No candidate is installed in MAPPOCoordinator or runtime configuration."""
    label = Path(checkpoint).parent.name if checkpoint else mode
    name = f'{split}-{label}-d{scale}-s{seed}-t{seconds}'
    result_path, trips_path = OUT/'trials'/f'{name}.json', OUT/'trips'/f'{name}.xml'
    checkpoint_hash = hashlib.sha256(Path(checkpoint).read_bytes()).hexdigest() if checkpoint else None
    if result_path.exists():
        cached = json.loads(result_path.read_text())
        if (cached.get('checkpointSha256') != checkpoint_hash or cached['mode'] != mode
                or cached['provenance'] != provenance()):
            raise ValueError('Cached trial has different weights/controller/architecture; use a new output directory')
        return cached
    trips_path.parent.mkdir(parents=True, exist_ok=True)
    model = MAPPO.load(checkpoint) if checkpoint else None
    if mode == 'candidate' and model is None:
        raise ValueError('Candidate weights required')
    if model and (model.agents != 2 or model.observation_size != 8
                  or not all(torch.isfinite(p).all().item() for p in model.parameters())):
        raise ValueError('Candidate architecture/numerical checks failed')
    # The hint-free hybrid's executable controller is MPC; the runtime interface remains disabled.
    env = MultiJunctionEnv(seconds, mode='mpc' if mode in {'candidate', 'hybrid'} else mode,
                           demand_scale=scale, tripinfo=trips_path)
    queues, waits, latencies, spillbacks, red_ages = [], [], [], [], []
    inference_latencies, decision_latencies = [], []
    fallback_controller_seconds = 0
    hint_controller_seconds = 0
    joint_action_counts = {}
    departed_vehicles = 0
    pending_samples = []
    started = time.perf_counter()
    result = dict(mode=mode, model=label, seed=seed, seconds=seconds, demandScale=scale,
                  split=split, checkpoint=str(checkpoint) if checkpoint else None,
                  operationalPolicyEnabled=False, provenance=provenance(), checkpointSha256=checkpoint_hash)
    try:
        obs = env.reset(seed)
        result['sumoVersion'] = traci.getVersion()
        while traci.simulation.getTime() < seconds:
            tick = time.perf_counter()
            action = model.act(obs, deterministic=True)[0] if model else None
            inference_ms = (time.perf_counter()-tick)*1000 if model else 0.0
            inference_latencies.append(inference_ms)
            decision_ms = inference_ms
            if action is not None:
                key = ','.join(str(int(a)) for a in action)
                joint_action_counts[key] = joint_action_counts.get(key,0)+1
            # Sample every simulator second, retaining the same recommendation for five seconds.
            for _ in range(min(5, seconds-int(traci.simulation.getTime()))):
                control_started = time.perf_counter()
                env.network.before_step(training_actions=action)
                control_ms = (time.perf_counter()-control_started)*1000
                latencies.append(control_ms)
                decision_ms += control_ms
                fallback_controller_seconds += sum(c.diagnostics.get('policy') == 'max_pressure_fallback'
                                                   for c in env.controllers.values())
                if action is not None:
                    if any(c.coordination_hint != int(action[i]) for i,c in enumerate(env.controllers.values())):
                        raise RuntimeError('Candidate recommendation did not reach MPC')
                    hint_controller_seconds += len(env.controllers)
                traci.simulationStep()
                env.network.after_step()
                departed_vehicles += traci.simulation.getDepartedNumber()
                pending_samples.append(len(traci.simulation.getPendingVehicles()))
                now = traci.simulation.getTime()
                approaches = [a for raw in env.network.raw.values() for a in raw['approaches'].values()]
                queues.append(sum(a['queued'] for a in approaches))
                waits.append(max((a['avgWaitTimeSec'] for a in approaches), default=0))
                spillbacks.append(sum(d['spillbackIndicator'] for raw in env.network.raw.values() for d in raw['downstream'].values()))
                red_ages.append(max(now-t for services in env.network.last_service.values() for t in services.values()))
            decision_latencies.append(decision_ms)
            obs = env.observations()
        result.update(status='completed', arrivedVehicles=env.network.total_arrived,
                      departedVehicles=departed_vehicles, endPendingVehicles=pending_samples[-1],
                      maxPendingVehicles=max(pending_samples), meanPendingVehicles=float(np.mean(pending_samples)),
                      observedInsertionDemandVehicles=departed_vehicles+pending_samples[-1],
                      throughputVehiclesPerHour=env.network.total_arrived*3600/seconds,
                      meanNetworkQueue=float(np.mean(queues)), maxNetworkQueue=max(queues),
                      maxApproachMeanWaitSeconds=max(waits), maxServiceAgeSeconds=max(red_ages),
                      spillbackEdgeSeconds=int(sum(spillbacks)),
                      meanControlLatencyMs=float(np.mean(latencies)), p95ControlLatencyMs=float(np.percentile(latencies,95)),
                      maxControlLatencyMs=max(latencies),
                      meanPolicyInferenceMs=float(np.mean(inference_latencies)),
                      p95PolicyInferenceMs=float(np.percentile(inference_latencies,95)),
                      meanDecisionControlComputeMs=float(np.mean(decision_latencies)),
                      p95DecisionControlComputeMs=float(np.percentile(decision_latencies,95)),
                      fallbackControllerSeconds=fallback_controller_seconds,
                      hintControllerSeconds=hint_controller_seconds, jointActionCounts=joint_action_counts,
                      supervisors={a:c.supervisor.report() for a,c in env.controllers.items()},
                      pedestrianConstraints='not_applicable_no_crossings_in_corridor',
                      emergencyResponse='not_measured_no_emergency_in_corridor',
                      safetyFaults=0)
    except Exception as exc:
        result.update(status='failed', fault=f'{type(exc).__name__}: {exc}', safetyFaults=1)
    finally:
        env.close()
    result['wallSeconds'] = time.perf_counter()-started
    if trips_path.exists():
        trips = ET.parse(trips_path).getroot().findall('tripinfo')
        completed = [t for t in trips if float(t.get('arrival','-1')) >= 0]
        delays = [float(t.get('timeLoss','0')) for t in completed]
        waiting = [float(t.get('waitingTime','0')) for t in completed]
        result.update(completedTrips=len(completed), unfinishedTrips=len(trips)-len(completed),
                      meanCompletedTimeLossSeconds=float(np.mean(delays)) if delays else None,
                      meanCompletedWaitingSeconds=float(np.mean(waiting)) if waiting else None,
                      p95CompletedWaitingSeconds=float(np.percentile(waiting,95)) if waiting else None,
                      maxCompletedWaitingSeconds=max(waiting) if waiting else None)
    write(result_path, result)
    print(json.dumps({k:v for k,v in result.items() if k not in {'provenance','supervisors'}}), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir',default=str(OUT))
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('train')
    p.add_argument('--seeds', type=int, nargs='+', default=[11,22,33])
    p.add_argument('--updates', type=int, default=16)
    p.add_argument('--rollout', type=int, default=64)
    p.add_argument('--resume', action='store_true')
    p = sub.add_parser('benchmark')
    p.add_argument('--seeds', type=int, nargs='+', default=[2901,2902,2903])
    p.add_argument('--seconds', type=int, default=300)
    p.add_argument('--scales', type=float, nargs='+', default=[1.0,1.75])
    p.add_argument('--modes', nargs='+', default=['fixed_time','max_pressure','mpc','hybrid'])
    p.add_argument('--checkpoints', nargs='*', default=[])
    p.add_argument('--split', choices=['selection','test'], default='test')
    args = parser.parse_args()
    OUT = Path(args.output_dir).resolve()
    if args.command == 'train':
        if args.updates < 1 or args.rollout < 1 or len(set(args.seeds)) != len(args.seeds):
            parser.error('Positive sizes and unique seeds required')
        for seed in args.seeds:
            train(seed,args.updates,args.rollout,args.resume)
    else:
        if args.seconds < 1 or len(set(args.seeds)) != len(args.seeds):
            parser.error('Positive horizon and unique seeds required')
        for checkpoint in args.checkpoints:
            training = json.loads((Path(checkpoint).parent/'training.json').read_text())
            if training['provenance']['architectureFingerprint'] != qualification_fingerprint():
                parser.error('Candidate was trained against a different architecture')
            if set(args.seeds) & {u['episodeSeed'] for u in training['updates']}:
                parser.error('Evaluation overlaps training seeds')
        selection_path = OUT/'selection.json'
        if args.split == 'test' and selection_path.exists():
            selection = json.loads(selection_path.read_text())
            if set(args.seeds) & set(selection['selectionSeeds']):
                parser.error('Final test overlaps model-selection seeds')
        for scale in args.scales:
            for seed in args.seeds:
                for mode in args.modes:
                    trial(mode,seed,args.seconds,scale,split=args.split)
                for checkpoint in args.checkpoints:
                    trial('candidate',seed,args.seconds,scale,checkpoint,args.split)
