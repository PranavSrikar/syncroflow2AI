"""Offline candidate topology-transfer challenges through the existing runtime.

No HTTP server is started and no qualified-policy gate/configuration is changed.
The shared actor sees one local observation. Duplicate input only satisfies the
unused centralized critic shape; actor outputs depend solely on local inputs.
"""
import argparse
import json
import time
from pathlib import Path
import numpy as np
import research_phase4 as research
from app.services.sumo_runtime import SumoRuntime


def run(checkpoint,seed):
    if seed not in (6401,6402,6403): raise ValueError('Unregistered challenge seed')
    model=research.MAPPO.load(checkpoint)
    out=research.ROOT/'.checkpoints/phase5/challenges';out.mkdir(exist_ok=True)
    for case,scenario,emergency in [('asymmetric','unequal',False),('blocked_exit','spillback',False),
                                    ('pedestrian','pedestrian',False),('pedestrian_emergency','pedestrian',True)]:
        for variant in ('mpc','candidate'):
            path=out/f'{case}-{variant}-{seed}.json'
            if path.exists(): raise FileExistsError('Preserve previous challenge results; use a new output study')
            runtime=SumoRuntime();calls=[];latencies=[];queues=[];spills=[];waits=[];ages=[];fallback=0
            phases=set();ped_seen=False;clearance=set();injected=None
            result=dict(case=case,variant=variant,seed=seed,seconds=240,checkpoint=str(checkpoint),
                        scope='Offline single-junction actor topology transfer; not operational policy activation',
                        operationallyEnabled=False)
            tripfile=out/f'{case}-{variant}-{seed}.xml'
            try:
                original_start=research.traci.start
                def start(command,*args,**kwargs):
                    return original_start([*command,'--tripinfo-output',str(tripfile),'--tripinfo-output.write-unfinished','true'],*args,**kwargs)
                research.traci.start=start
                try:
                    runtime.command('start',scenario=scenario,controller='hybrid' if variant=='candidate' else 'mpc',seed=seed,paused=True)
                finally: research.traci.start=original_start
                if variant=='candidate':
                    def recommend(obs):
                        action=model.act(np.repeat(obs,2,axis=0),True)[0][:1]
                        calls.append(action.tolist());return action
                    runtime.coordinator.recommend=recommend
                if emergency: injected=runtime.inject_emergency('east',3)
                for _ in range(240):
                    tick=time.perf_counter();runtime.command('step');latencies.append((time.perf_counter()-tick)*1000)
                    raw=runtime.telemetry
                    assert research.traci.simulation.getCollidingVehiclesNumber()==0,'SUMO reported a collision'
                    assert all(r['compatibleUnderSumoRules'] for r in raw['permissionAnalysis'].values())
                    phases.add(raw['trafficLights'][runtime.controller.tls]['phaseIndex'])
                    ped_seen |= bool(raw['pedestrians'])
                    clearance.update(p['clearanceRequirementSec'] for p in raw['pedestrianSignals'] if p['clearanceRequirementSec'] is not None)
                    queues.append(sum(a['queued'] for a in raw['approaches'].values()))
                    waits.append(max(a['avgWaitTimeSec'] for a in raw['approaches'].values()))
                    spills.append(sum(d['spillbackIndicator'] for d in raw['downstream'].values()))
                    ages.append(max(raw['simTime']-t for t in runtime.controller.supervisor.last_served.values()))
                    fallback += runtime.controller.diagnostics.get('policy')=='max_pressure_fallback'
                requests=runtime.emergencies.snapshot()['requests']
                result.update(status='completed',metrics=runtime.metrics,meanQueue=float(np.mean(queues)),maxQueue=max(queues),
                              maxApproachMeanWaitSeconds=max(waits),spillbackEdgeSeconds=sum(spills),
                              meanFullStepLatencyMs=float(np.mean(latencies)),p95FullStepLatencyMs=float(np.percentile(latencies,95)),
                              actorCalls=len(calls),holdActions=sum(a[0]==1 for a in calls),
                              maxServiceAgeSeconds=max(ages),fallbackControllerSeconds=fallback,
                              pedestrianSeen=ped_seen,clearanceRequirements=sorted(clearance),phases=sorted(phases),
                              emergencyRequests=requests,supervisor=runtime.controller.supervisor.report(),safetyFaults=0)
                if 'pedestrian' in case:
                    assert ped_seen and 15 in clearance,'Expected supplied pedestrian coverage absent'
                if emergency:
                    assert any(r['vehicleId']==injected['vehicleId'] and r['state']=='completed' for r in requests),'Emergency did not complete'
            except Exception as exc:
                result.update(status='failed',fault=f'{type(exc).__name__}: {exc}',safetyFaults=1)
            finally:
                runtime.command('stop')
                if tripfile.exists():
                    trips=research.ET.parse(tripfile).getroot().findall('tripinfo')
                    complete=[t for t in trips if float(t.get('arrival','-1'))>=0]
                    result.update(completedTrips=len(complete),unfinishedTrips=len(trips)-len(complete),
                        meanCompletedTimeLossSeconds=float(np.mean([float(t.get('timeLoss','0')) for t in complete])) if complete else None,
                        maxObservedWaitingSeconds=max((float(t.get('waitingTime','0')) for t in trips),default=0.))
                research.write(path,result)
            print(json.dumps(dict(case=case,variant=variant,seed=seed,status=result['status'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);p.add_argument('--seed',type=int,required=True)
    args=p.parse_args();run(args.checkpoint,args.seed)
