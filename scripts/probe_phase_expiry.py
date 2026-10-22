"""Controlled supervised one-second release experiment; no raw signal writes."""
import argparse
import json
from pathlib import Path
import sys
import traci
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.rl.sumo_env import MultiJunctionEnv


def probe(output):
    env=MultiJunctionEnv(episode_seconds=55)
    trace=[]
    first_transition={}
    try:
        env.reset(701)
        initial={a:r['trafficLights'][a]['phaseIndex'] for a,r in env.network.raw.items()}
        for c in env.controllers.values():
            def release(raw,phase,spent,scores,c=c):
                return 1.0 if c.supervisor.MIN_GREEN<=spent<c.supervisor.MAX_GREEN else None
            c.recommend_remaining=release
        for _ in range(55):
            env.network.before_step()
            traci.simulationStep(); env.network.after_step()
            row={'simTime':traci.simulation.getTime(),'junctions':{}}
            for a,raw in env.network.raw.items():
                light=raw['trafficLights'][a]
                row['junctions'][a]=dict(phase=light['phaseIndex'],nextSwitch=light['nextSwitch'],
                                         spent=traci.trafficlight.getSpentDuration(a))
                if light['phaseIndex']!=initial[a] and a not in first_transition:
                    first_transition[a]=raw['simTime']
            trace.append(row)
    finally:
        env.close()
    result=dict(seed=701,controlledRecommendation='release after minimum green with remaining=1 second',
                firstPhaseTransition=first_transition,trace=trace)
    Path(output).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(first_transition))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True)
    probe(p.parse_args().output)
