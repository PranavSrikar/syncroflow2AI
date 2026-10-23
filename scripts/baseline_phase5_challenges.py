"""Complete installed-mode comparisons for asymmetric and blocked-exit cases."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import research_phase4 as research
from app.services.sumo_runtime import SumoRuntime


def run(seed):
    if seed not in (6401,6402,6403):raise ValueError('Unregistered seed')
    out=research.ROOT/'.checkpoints/phase5/challenges';out.mkdir(exist_ok=True)
    source=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for case,scenario in [('asymmetric','unequal'),('blocked_exit','spillback')]:
        for mode in ('fixed_time','max_pressure','hybrid'):
            path=out/f'{case}-{mode}-{seed}.json'
            if path.exists():raise FileExistsError(path)
            tripfile=out/f'{case}-{mode}-{seed}.xml'
            runtime=SumoRuntime();latencies=[];queues=[];waits=[];spills=[];ages=[];fallback=0
            result=dict(case=case,variant=mode,seed=seed,seconds=240,operationallyEnabled=False,
                        sourceSha256=source,architectureFingerprint=research.qualification_fingerprint(),
                        scope='Installed-mode single-junction baseline; native fixed-time issues no adaptive writes')
            try:
                original=research.traci.start
                def start(command,*args,**kwargs):
                    return original([*command,'--tripinfo-output',str(tripfile),'--tripinfo-output.write-unfinished','true'],*args,**kwargs)
                research.traci.start=start
                try:runtime.command('start',scenario=scenario,controller='sumo_fixed_time' if mode=='fixed_time' else mode,seed=seed,paused=True)
                finally:research.traci.start=original
                tls=next(iter(runtime.telemetry['trafficLights']))
                if runtime.controller is None:
                    program=research.traci.trafficlight.getProgram(tls)
                    phases=next(p for p in research.traci.trafficlight.getAllProgramLogics(tls) if p.programID==program).phases
                    last={i:0. for i,p in enumerate(phases) if any(s in 'Gg' for s in p.state) and 'y' not in p.state}
                for _ in range(240):
                    tick=time.perf_counter();runtime.command('step');latencies.append((time.perf_counter()-tick)*1000)
                    raw=runtime.telemetry
                    assert research.traci.simulation.getCollidingVehiclesNumber()==0
                    assert all(r['compatibleUnderSumoRules'] for r in raw['permissionAnalysis'].values())
                    queues.append(sum(a['queued'] for a in raw['approaches'].values()))
                    waits.append(max(a['avgWaitTimeSec'] for a in raw['approaches'].values()))
                    spills.append(sum(d['spillbackIndicator'] for d in raw['downstream'].values()))
                    if runtime.controller is not None:
                        ages.append(max(raw['simTime']-t for t in runtime.controller.supervisor.last_served.values()))
                        fallback+=runtime.controller.diagnostics.get('policy')=='max_pressure_fallback'
                    else:
                        phase=raw['trafficLights'][tls]['phaseIndex']
                        if phase in last:last[phase]=raw['simTime']
                        ages.append(max(raw['simTime']-t for t in last.values()))
                result.update(status='completed',metrics=runtime.metrics,meanQueue=float(np.mean(queues)),maxQueue=max(queues),
                    maxApproachMeanWaitSeconds=max(waits),spillbackEdgeSeconds=sum(spills),maxServiceAgeSeconds=max(ages),
                    fallbackControllerSeconds=fallback,meanFullStepLatencyMs=float(np.mean(latencies)),
                    p95FullStepLatencyMs=float(np.percentile(latencies,95)),safetyFaults=0,
                    supervisor=runtime.controller.supervisor.report() if runtime.controller else dict(status='native_fixed_time_no_adaptive_writes'))
            except Exception as exc:result.update(status='failed',fault=f'{type(exc).__name__}: {exc}',safetyFaults=1)
            finally:
                runtime.command('stop')
                if tripfile.exists():
                    trips=research.ET.parse(tripfile).getroot().findall('tripinfo')
                    complete=[t for t in trips if float(t.get('arrival','-1'))>=0]
                    result.update(completedTrips=len(complete),unfinishedTrips=len(trips)-len(complete),
                        meanCompletedTimeLossSeconds=float(np.mean([float(t.get('timeLoss','0')) for t in complete])) if complete else None,
                        maxObservedWaitingSeconds=max((float(t.get('waitingTime','0')) for t in trips),default=0.))
                research.write(path,result)
            print(json.dumps(dict(case=case,variant=mode,seed=seed,status=result['status'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,required=True);run(p.parse_args().seed)
