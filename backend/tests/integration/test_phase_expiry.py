import shutil
import pytest
import traci
from app.rl.sumo_env import MultiJunctionEnv


@pytest.mark.skipif(shutil.which('sumo') is None,reason='SUMO required')
def test_one_second_release_is_not_repeatedly_postponed():
    env=MultiJunctionEnv(episode_seconds=55)
    first={}
    phases={a:set() for a in env.agents}
    try:
        env.reset(701)
        for controller in env.controllers.values():
            def release(raw,phase,spent,scores,c=controller):
                return 1.0 if c.supervisor.MIN_GREEN<=spent<c.supervisor.MAX_GREEN else None
            controller.recommend_remaining=release
        for _ in range(55):
            env.network.before_step()
            traci.simulationStep(); env.network.after_step()
            for agent,raw in env.network.raw.items():
                phase=raw['trafficLights'][agent]['phaseIndex']
                phases[agent].add(phase)
                if phase!=0 and agent not in first: first[agent]=raw['simTime']
                assert not raw['permissionAnalysis'][agent]['incompatiblePermissions']
        assert set(first)==set(env.agents)
        assert all(10<=t<=12 for t in first.values()),first
        assert all(p==set(range(6)) for p in phases.values())
        assert all(c.supervisor.report()['rejectedActions']==0 for c in env.controllers.values())
    finally:
        env.close()
