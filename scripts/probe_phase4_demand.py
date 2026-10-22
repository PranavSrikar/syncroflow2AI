"""Measure actual insertion counts under the two primary demand scales."""
import json
from pathlib import Path
import sys
import traci
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.rl.sumo_env import MultiJunctionEnv


def main():
    results=[]
    for scale in (.75,1.75):
        env=MultiJunctionEnv(episode_seconds=100,demand_scale=scale)
        departed=arrived=0
        try:
            env.reset(701)
            for _ in range(100):
                env.network.before_step(); traci.simulationStep(); env.network.after_step()
                departed+=traci.simulation.getDepartedNumber()
                arrived+=traci.simulation.getArrivedNumber()
            results.append(dict(seed=701,demandScale=scale,seconds=100,
                                departedVehicles=departed,arrivedVehicles=arrived,
                                pendingVehicles=len(traci.simulation.getPendingVehicles())))
        finally: env.close()
    if results[1]['departedVehicles']<=1.7*results[0]['departedVehicles']:
        raise ValueError('Demand scales failed to produce materially distinct inserted demand')
    out=ROOT/'.checkpoints/phase4-demand-corrected'; out.mkdir(exist_ok=True)
    (out/'demand-probe.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2))


if __name__=='__main__': main()
