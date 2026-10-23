"""Isolated diagnostic ablations; never installs a policy in the operational API.

Shadow MPC calls compare recommendations at identical observed states. They do
not actuate signals. Only the normal controller/supervisor path applies actions.
Latency includes instrumentation and must not be treated as production latency.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import time

import research_phase4 as research
import numpy as np
import torch
from app.services.constrained_mpc import ConstrainedMPC

ROOT = research.ROOT
OUT = ROOT / '.checkpoints/phase5'
CHECKPOINT = ROOT / '.checkpoints/phase4-demand-corrected/train-41/update-0016.pt'
VARIANTS = ('none', 'trained', 'untrained', 'release', 'hold', 'random')


def run(seed, seconds, scale, variant):
    if seed not in (5101, 5102, 5103):
        raise ValueError('Only preregistered fresh diagnostic seeds accepted')
    research.OUT = OUT / 'ablations' / variant
    traces, observations = [], []
    original_recommend = ConstrainedMPC.recommend_remaining
    original_load = research.MAPPO.load
    rng = np.random.default_rng(seed + 500000)

    def recommend(controller, raw, phase, spent, scores):
        # This method only evaluates plans and updates diagnostics; no TraCI writes.
        hint = getattr(controller, 'coordination_hint', None)
        saved = copy.deepcopy(controller.diagnostics)
        controller.coordination_hint = None
        shadow = original_recommend(controller, raw, phase, spent, scores)
        shadow_policy = controller.diagnostics.get('policy')
        controller.diagnostics = saved
        controller.coordination_hint = hint
        actual = original_recommend(controller, raw, phase, spent, scores)
        traces.append(dict(tls=controller.tls, simTime=raw['simTime'], phase=phase,
                           spent=spent, hint=hint, withoutHint=shadow, withHint=actual,
                           changed=shadow != actual, policy=controller.diagnostics.get('policy'),
                           shadowPolicy=shadow_policy,
                           nextGreen=controller.diagnostics.get('plannedNextGreenSec')))
        return actual

    def load(path):
        model = original_load(path)
        if variant == 'untrained':
            model = research.MAPPO(seed=41)
        original_act = model.act

        def act(obs, deterministic=False):
            action, log, value = original_act(obs, deterministic)
            observations.append(np.asarray(obs).tolist())
            if variant in ('release', 'hold'):
                action = np.full(2, int(variant == 'hold'), dtype=np.int64)
            elif variant == 'random':
                action = rng.integers(0, 2, size=2)
            return action, log, value
        model.act = act
        return model

    ConstrainedMPC.recommend_remaining = recommend
    research.MAPPO.load = load
    try:
        row = research.trial('mpc' if variant == 'none' else 'candidate', seed, seconds, scale,
                             None if variant == 'none' else CHECKPOINT, split='diagnostic')
        if row['status'] != 'completed':
            raise RuntimeError(row.get('fault'))
        eligible = [r for r in traces if r['withHint'] is not None and r['withoutHint'] is not None
                    and r['policy'] == r['shadowPolicy'] == 'constrained_mpc']
        report = dict(variant=variant, seed=seed, scale=scale, seconds=seconds,
                      operationallyEnabled=False, sourceCheckpointSha256=hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest(),
                      result=row, influence=dict(recommendationCalls=len(traces), eligibleMpcComparisons=len(eligible),
                      changedRemaining=sum(r['changed'] for r in eligible)), traces=traces,
                      observations=observations,
                      limitations='Shadow computation adds overhead. Same-state changes are recommendations, not counterfactual traffic outcomes. Static/random/untrained variants do not represent the trained checkpoint despite shared trial storage label.')
        research.write(OUT/f'diagnostics/{variant}-d{scale}-s{seed}-t{seconds}.json',report)
        print(json.dumps(dict(variant=variant,seed=seed,scale=scale,**report['influence'])),flush=True)
    finally:
        ConstrainedMPC.recommend_remaining = original_recommend
        research.MAPPO.load = original_load


def gradients():
    """Measure separate actor/critic gradient norms on a fresh genuine rollout."""
    model = research.MAPPO.load(CHECKPOINT)
    env = research.MultiJunctionEnv(episode_seconds=320)
    rollout = [[] for _ in range(6)]
    try:
        obs=env.reset(5199)
        for _ in range(64):
            action,log,value=model.act(obs)
            following,reward,terminal,truncated,info=env.step(action)
            for bucket,item in zip(rollout,(obs.copy(),action,log,reward,value,terminal)): bucket.append(item)
            obs=following
        observations,actions,logs,rewards,values,terminals=rollout
        adv,returns=research.MAPPO.update.__globals__['generalized_advantages'](rewards,values,model.act(obs,True)[2],terminals)
        norm=(adv-adv.mean())/(adv.std(unbiased=False)+1e-8)
        ob=torch.tensor(np.asarray(observations),dtype=torch.float32)
        dist=model.distribution(ob)
        ratio=torch.exp(dist.log_prob(torch.tensor(np.asarray(actions)))-torch.tensor(np.asarray(logs)))
        actor=-torch.minimum(ratio*norm,ratio.clamp(.8,1.2)*norm).mean()-.01*dist.entropy().mean()
        predicted=model.critic(ob.flatten(start_dim=1))
        critic=.5*(predicted-returns).square().mean()
        ag=torch.autograd.grad(actor,list(model.actor.parameters()))
        cg=torch.autograd.grad(critic,list(model.critic.parameters()))
        an=float(torch.sqrt(sum(g.square().sum() for g in ag)))
        cn=float(torch.sqrt(sum(g.square().sum() for g in cg)))
        data=dict(seed=5199,decisions=64,actorGradientNorm=an,criticWeightedGradientNorm=cn,
                  jointClipMultiplier=min(1.,.5/(an*an+cn*cn)**.5),
                  returnMean=float(returns.mean()),returnStd=float(returns.std()),
                  predictedValueMean=float(predicted.mean().detach()),meanSquaredValueError=float((predicted-returns).square().mean().detach()),
                  rewardMean=float(np.mean(rewards)),entropy=float(dist.entropy().mean()),
                  observationsMin=np.min(ob.numpy(),axis=(0,1)).tolist(),observationsMax=np.max(ob.numpy(),axis=(0,1)).tolist(),
                  operationallyEnabled=False,weightsUpdated=False)
        # Adam can cancel nearly uniform gradient rescaling. Measure updates rather
        # than equating a small clipping multiplier with small parameter motion.
        baseline = torch.cat([p.detach().flatten() for p in model.actor.parameters()])
        original_clip = torch.nn.utils.clip_grad_norm_
        outcomes = {}
        for variant in ('joint_clip', 'separate_clip'):
            clone = research.MAPPO.load(CHECKPOINT)
            actor_count = len(list(clone.actor.parameters()))
            if variant == 'separate_clip':
                def separate(parameters, maximum):
                    params = list(parameters)
                    a = original_clip(params[:actor_count], maximum)
                    c = original_clip(params[actor_count:], maximum)
                    return torch.sqrt(a*a+c*c)
                torch.nn.utils.clip_grad_norm_ = separate
            try:
                metrics = clone.update(observations,actions,logs,rewards,values,model.act(obs,True)[2],terminals)
                delta = torch.cat([p.detach().flatten() for p in clone.actor.parameters()])-baseline
                outcomes[variant] = dict(actorParameterDeltaL2=float(delta.norm()),metrics=metrics,
                    changedGreedyActions=int((clone.act(ob[-1].numpy(),True)[0] != model.act(ob[-1].numpy(),True)[0]).sum()))
                outcomes[variant]['delta'] = delta
            finally: torch.nn.utils.clip_grad_norm_ = original_clip
        a,b=(outcomes[v].pop('delta') for v in ('joint_clip','separate_clip'))
        data['optimizerAblation'] = dict(variants=outcomes,
            actorDeltaDifferenceL2=float((a-b).norm()),actorDeltaCosine=float(torch.nn.functional.cosine_similarity(a,b,dim=0)),
            scope='One identical genuine rollout, four PPO epochs, restored optimizer state. No saved or operational weights; not a traffic performance evaluation.')
        research.write(OUT/'gradient-diagnostic.json',data); print(json.dumps(data))
    finally: env.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int);p.add_argument('--seconds',type=int,default=600)
    p.add_argument('--gradients',action='store_true');args=p.parse_args()
    if args.gradients: gradients()
    else:
        for scale in (.75,1.,1.75):
            for variant in VARIANTS: run(args.seed,args.seconds,scale,variant)
