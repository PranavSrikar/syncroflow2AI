"""Research-only independent actor/critic clipping; production learner preserved."""
import argparse
import hashlib
from pathlib import Path
import research_phase4 as research
import torch

BASE = research.MAPPO
BASE_PROVENANCE = research.provenance


class IndependentClipMAPPO(BASE):
    def update(self, *args, **kwargs):
        original = torch.nn.utils.clip_grad_norm_
        count = len(list(self.actor.parameters()))
        norms = {}

        def clip(parameters, maximum):
            parameters = list(parameters)
            actor = original(parameters[:count], maximum)
            critic = original(parameters[count:], maximum)
            norms.update(actorGradientNorm=float(actor), criticGradientNorm=float(critic))
            return torch.sqrt(actor*actor+critic*critic)

        # Isolated single-thread learner process. Restore even on failed updates.
        torch.nn.utils.clip_grad_norm_ = clip
        try:
            return dict(super().update(*args, **kwargs), **norms,
                        optimizerVariant='independent_actor_critic_clipping')
        finally:
            torch.nn.utils.clip_grad_norm_ = original


def provenance():
    return dict(BASE_PROVENANCE(), experimentalLearner='independent_actor_critic_clipping',
                experimentalLearnerSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--seed',type=int,required=True)
    parser.add_argument('--updates',type=int,default=16)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    if args.seed not in (61,71,81) or not 1<=args.updates<=16:
        parser.error('Preregistered seeds61/71/81, positive maximum16 updates')
    research.OUT=research.ROOT/'.checkpoints/phase5/training'
    research.MAPPO=IndependentClipMAPPO
    research.provenance=provenance
    research.train(args.seed,args.updates,64,args.resume)
