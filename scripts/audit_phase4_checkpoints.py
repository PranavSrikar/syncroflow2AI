"""Validate all preserved main-run checkpoints without actuating SUMO."""
import hashlib
import json
from pathlib import Path
import sys
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.rl.mappo import MAPPO
from app.services.mappo_coordination import qualification_fingerprint


def main():
    records=[]
    for seed in (21,31,41):
        folder=ROOT/f'.checkpoints/phase4/train-{seed}'
        training=json.loads((folder/'training.json').read_text())
        if training['trainedDecisionSteps']!=1024 or len(training['updates'])!=16:
            raise ValueError('Main training incomplete')
        if training['provenance']['architectureFingerprint']!=qualification_fingerprint():
            raise ValueError('Training architecture has changed')
        initial=MAPPO(seed=seed)
        last=None
        for update in range(1,17):
            p=folder/f'update-{update:04d}.pt'
            model=MAPPO.load(p)
            if model.trained_steps!=64*update or model.seed!=seed:
                raise ValueError('Checkpoint metadata mismatch')
            if not all(torch.isfinite(t).all().item() for t in model.parameters()):
                raise ValueError('Nonfinite parameters')
            for state in model.optimizer.state.values():
                if any(isinstance(t,torch.Tensor) and not torch.isfinite(t).all().item() for t in state.values()):
                    raise ValueError('Nonfinite optimizer state')
            records.append(dict(modelSeed=seed,update=update,jointDecisions=model.trained_steps,
                                checkpoint=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
            last=model
        actor_delta=sum(float((a-b).square().sum()) for a,b in zip(initial.actor.parameters(),last.actor.parameters()))**.5
        critic_delta=sum(float((a-b).square().sum()) for a,b in zip(initial.critic.parameters(),last.critic.parameters()))**.5
        if not actor_delta or not critic_delta:
            raise ValueError('Actor or critic did not update')
        print(json.dumps(dict(seed=seed,actorParameterL2Change=actor_delta,criticParameterL2Change=critic_delta)),flush=True)
    report=dict(checkpointsVerified=len(records),finiteParametersAndOptimizer=True,
                architectureFingerprint=qualification_fingerprint(),records=records,
                usefulnessEstablished=False)
    (ROOT/'.checkpoints/phase4/checkpoint-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Verified all48 main-run checkpoints; no operational qualification implied')


if __name__=='__main__': main()
