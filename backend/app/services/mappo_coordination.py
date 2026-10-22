"""Bounded coordination preferences only. Never imports or writes TraCI signals."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import numpy as np


def qualification_fingerprint():
    backend = Path(__file__).resolve().parents[2]
    files = ['app/services/hybrid_network.py', 'app/services/signal_supervisor.py',
             'app/services/pedestrian_supervisor.py', 'app/services/constrained_mpc.py',
             'app/services/max_pressure_controller.py', 'app/services/sumo_runtime.py',
             'app/services/sumo_adapter.py', 'app/services/emergency_priority.py',
             'app/services/traffic_estimation.py', 'app/services/forecasting.py',
             'app/services/mappo_coordination.py', 'app/rl/mappo.py',
             'sumo_scenarios/two_junction/corridor.net.xml']
    return hashlib.sha256(b''.join((backend/name).read_bytes() for name in files)).hexdigest()


def local_observations(raws, controllers, agents):
    rows = []
    for agent in agents:
        raw = raws[agent]
        light = raw['trafficLights'][agent]
        controller = controllers.get(agent)
        greens = controller.supervisor.green_indices if controller else [0, 2]
        rows.append([raw['approaches'][d]['queued']/20 for d in ('north', 'south', 'east', 'west')]
                    + [float(light['phaseIndex'] == g) for g in greens]
                    + [max(0, light['nextSwitch']-raw['simTime'])/45,
                       sum(d['occupancyPercent'] for d in raw['downstream'].values())/400])
    return np.asarray(rows, dtype=np.float32)


class MAPPOCoordinator:
    def __init__(self, agents, checkpoint=None, validation=None):
        self.agents = tuple(agents)
        self.model = None
        self.inference_calls = 0
        self.last_actions = None
        self.healthy = True
        self.reason = 'Training/inference-ready; no qualified checkpoint configured; supervised MPC fallback'
        checkpoint = checkpoint or os.environ.get('SYNCHROFLOW_MAPPO_CHECKPOINT')
        validation = validation or os.environ.get('SYNCHROFLOW_MAPPO_VALIDATION')
        if checkpoint or validation:
            try:
                if not checkpoint or not validation:
                    raise ValueError('Both checkpoint and validation report required')
                report = json.loads(Path(validation).read_text(encoding='utf-8'))
                digest = hashlib.sha256(Path(checkpoint).read_bytes()).hexdigest()
                evidence = report.get('closedLoopValidation', {})
                if (report.get('checkpointSha256') != digest or not report.get('eligibleForEvaluation')
                    or report.get('architectureFingerprint') != qualification_fingerprint()
                    or report.get('trainedDecisionSteps', 0) < 1024
                    or len(set(evidence.get('seeds', []))) < 3 or evidence.get('secondsPerSeed', 0) < 240
                    or evidence.get('safetyFaults') != 0 or not report.get('numericalChecksPassed')):
                    raise ValueError('Checkpoint lacks required numerical and multi-seed supervised closed-loop validation')
                from app.rl.mappo import MAPPO
                model = MAPPO.load(checkpoint)
                if model.agents != len(self.agents) or model.observation_size != 8 or model.trained_steps != report['trainedDecisionSteps']:
                    raise ValueError('Checkpoint observation/agent/training metadata mismatch')
                self.model = model
                self.reason = 'Qualified for supervised SUMO research inference; comparative usefulness unproven'
            except Exception as exc:
                self.reason = str(exc)+'; supervised MPC fallback'

    def recommend(self, observations):
        if self.model is None:
            self.last_actions = None
            return None
        try:
            observations = np.asarray(observations, dtype=np.float32)
            if observations.shape != (len(self.agents), 8) or not np.isfinite(observations).all():
                raise ValueError('Invalid MAPPO observations')
            actions = self.model.act(observations, deterministic=True)[0]
            actions = self.validate_actions(actions)
            self.inference_calls += 1
            self.healthy = True
            self.last_actions = actions.tolist()
            return actions
        except Exception as exc:
            self.reason = 'MAPPO inference failed: '+str(exc)+'; supervised MPC fallback'
            self.healthy = False
            self.last_actions = None
            return None

    def validate_actions(self, actions):
        actions = np.asarray(actions)
        if actions.shape != (len(self.agents),) or not np.isin(actions, [0, 1]).all():
            raise ValueError('One binary hold/release preference per junction required')
        return actions.astype(int)

    def snapshot(self):
        return dict(torchAvailable=importlib.util.find_spec('torch') is not None,
                    operationalPolicyEnabled=self.model is not None and self.healthy,
                    status=('qualified_research_inference' if self.healthy else 'inference_failed_fallback') if self.model else 'training_inference_ready',
                    reason=self.reason, inferenceCalls=self.inference_calls, lastRecommendations=self.last_actions,
                    actionSemantics='0 release preference, 1 hold preference; MPC and supervisor may override',
                    agents=list(self.agents))
