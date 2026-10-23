"""Aggregate real Phase5 evidence; fail closed on incomplete experiments."""
import csv
import hashlib
import json
from pathlib import Path
import statistics
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.services.mappo_coordination import MAPPOCoordinator,qualification_fingerprint

OUT=ROOT/'.checkpoints/phase5'
PUB=ROOT/'research/phase5'


def read(path):return json.loads(Path(path).read_text(encoding='utf8'))
def write(path,data):Path(path).write_bytes((json.dumps(data,indent=2,allow_nan=False)+'\n').encode('utf8'))
def md(name,text): (ROOT/name).write_bytes(text.encode('utf8'))
def mean(rows,key):return statistics.mean(r[key] for r in rows)
def table(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in rows)


def main():
    PUB.mkdir(exist_ok=True,parents=True)
    diagnostics=[read(p) for p in sorted((OUT/'diagnostics').glob('*.json'))]
    trials=[read(p) for p in sorted((OUT/'evaluation/trials').glob('test-*.json'))]
    challenges=[read(p) for p in sorted((OUT/'challenges').glob('*.json'))]
    if len(diagnostics)!=54 or len(trials)!=45 or len(challenges)!=24:
        raise ValueError(f'Incomplete expected evidence: diagnostics{len(diagnostics)}/54,trials{len(trials)}/45,challenges{len(challenges)}/24')
    if any(d['result']['status']!='completed' for d in diagnostics) or any(r['status']!='completed' for r in trials):
        raise ValueError('Failed traffic trial; inspect raw evidence, do not report complete benchmark')
    selection=read(OUT/'evaluation/selection.json');safety=read(OUT/'safety-qualification.json')
    gradients=read(OUT/'gradient-diagnostic.json')
    groups=[];ablations=[]
    equivalence=[]
    trained_actions={}
    for d in diagnostics:
        if d['variant']!='trained':continue
        for key,value in d['result']['jointActionCounts'].items():trained_actions[key]=trained_actions.get(key,0)+value
        for variant in ('untrained','hold','release','random'):
            other=next(r for r in diagnostics if r['variant']==variant and r['seed']==d['seed'] and r['scale']==d['scale'])
            def trip_attributes(row):
                r=row['result'];p=OUT/f"ablations/{row['variant']}/trips/diagnostic-train-41-d{r['demandScale']}-s{r['seed']}-t{r['seconds']}.xml"
                return sorted((t.attrib for t in ET.parse(p).getroot().findall('tripinfo')),key=lambda t:t['id'])
            equivalence.append(dict(seed=d['seed'],scale=d['scale'],comparison=variant,
                                    exactTripAttributesIdentical=trip_attributes(d)==trip_attributes(other)))
    for scale in (.75,1.,1.75):
        for variant in ('none','trained','untrained','release','hold','random'):
            ds=[d for d in diagnostics if d['scale']==scale and d['variant']==variant]
            rs=[d['result'] for d in ds]
            eligible=sum(d['influence']['eligibleMpcComparisons'] for d in ds)
            changed=sum(d['influence']['changedRemaining'] for d in ds)
            ablations.append(dict(scale=scale,variant=variant,n=len(rs),delayMean=mean(rs,'meanCompletedTimeLossSeconds'),
                delaySD=statistics.stdev(r['meanCompletedTimeLossSeconds'] for r in rs),
                throughputMean=mean(rs,'throughputVehiclesPerHour'),maxServiceAge=max(r['maxServiceAgeSeconds'] for r in rs),
                recommendationCalls=sum(d['influence']['recommendationCalls'] for d in ds),
                eligibleComparisons=eligible,changedRemaining=changed,changedPercent=100*changed/eligible if eligible else 0,
                safetyFaults=sum(r['safetyFaults'] for r in rs),fallbackControllerSeconds=sum(r['fallbackControllerSeconds'] for r in rs)))
        for mode in ('fixed_time','max_pressure','mpc','hybrid','candidate'):
            rs=[r for r in trials if r['mode']==mode and r['demandScale']==scale]
            groups.append(dict(scale=scale,mode=mode,n=len(rs),delayMean=mean(rs,'meanCompletedTimeLossSeconds'),
                delaySD=statistics.stdev(r['meanCompletedTimeLossSeconds'] for r in rs),
                throughputMean=mean(rs,'throughputVehiclesPerHour'),meanQueue=mean(rs,'meanNetworkQueue'),
                maxQueue=max(r['maxNetworkQueue'] for r in rs),maxServiceAge=max(r['maxServiceAgeSeconds'] for r in rs),
                unfinishedMean=mean(rs,'unfinishedTrips'),spillbackEdgeSeconds=sum(r['spillbackEdgeSeconds'] for r in rs),
                controlMeanMs=mean(rs,'meanControlLatencyMs'),fallbackControllerSeconds=sum(r['fallbackControllerSeconds'] for r in rs)))
    checks=[];improvements={}
    for scale in (.75,1.,1.75):
        cg=next(g for g in groups if g['scale']==scale and g['mode']=='candidate')
        bg=next(g for g in groups if g['scale']==scale and g['mode']=='mpc')
        reduction=100*(bg['delayMean']-cg['delayMean'])/bg['delayMean'];improvements[str(scale)]=reduction
        checks.append(dict(name=f'at_least_2pct_mean_delay_reduction_d{scale}',passed=reduction>=2,value=reduction))
        for seed in (6301,6302,6303):
            c=next(r for r in trials if r['mode']=='candidate' and r['seed']==seed and r['demandScale']==scale)
            b=next(r for r in trials if r['mode']=='mpc' and r['seed']==seed and r['demandScale']==scale)
            for name,passed in [('no_delay_regression_over_5pct',c['meanCompletedTimeLossSeconds']<=b['meanCompletedTimeLossSeconds']*1.05),
                ('no_throughput_loss_over_2pct',c['arrivedVehicles']>=b['arrivedVehicles']*.98),
                ('no_service_age_increase',c['maxServiceAgeSeconds']<=b['maxServiceAgeSeconds']),
                ('no_safety_fault_or_rejection',c['safetyFaults']==0 and all(s['rejectedActions']==0 for s in c['supervisors'].values()))]:
                checks.append(dict(name=f'{name}_d{scale}_s{seed}',passed=bool(passed)))
    performance=all(c['passed'] for c in checks)
    candidate_challenges=[r for r in challenges if r['variant']=='candidate']
    challenge_ok=all(r['status']=='completed' and r['safetyFaults']==0 and r['supervisor']['rejectedActions']==0 for r in candidate_challenges)
    # These single-junction transfer challenges do not cover the original
    # two-junction policy with combined protected crossings/emergency demands.
    qualification=dict(safety,performanceValidation=dict(passed=performance,checks=checks),
        candidateSingleJunctionTransferChallengesPassed=challenge_ok,
        candidateCombinedMultiJunctionPedestrianEmergencyValidation=False,
        eligibleForEvaluation=False,usefulnessEstablished=False,operationallyEnabled=False,
        status='not_qualified_keep_operational_policy_disabled',
        incompleteConditions=['Original two-junction policy combined pedestrian/emergency coverage absent',
                              'Positive qualified-policy operational API/browser path not performed'])
    write(OUT/'policy-qualification.json',qualification);write(PUB/'policy-qualification.json',qualification)
    coordinator=MAPPOCoordinator(('A0','B0'),selection['selectedCheckpoint'],PUB/'policy-qualification.json')
    assert coordinator.model is None
    summary=dict(selection=selection,groups=groups,ablations=ablations,meanDelayReductionPercent=improvements,
                 gradientDiagnostic=gradients,qualification=qualification,trainedDiagnosticJointActions=trained_actions,
                 trainedTripEquivalence=equivalence,
                 operationalGateRefusesCandidate=True,architectureFingerprint=qualification_fingerprint())
    write(PUB/'results.json',summary)
    write(PUB/'trials.json',trials);write(PUB/'challenge-results.json',challenges)
    with (PUB/'trials.csv').open('w',newline='',encoding='utf8') as f:
        keys=['mode','seed','demandScale','seconds','meanCompletedTimeLossSeconds','throughputVehiclesPerHour',
              'meanNetworkQueue','maxNetworkQueue','maxServiceAgeSeconds','spillbackEdgeSeconds',
              'meanControlLatencyMs','fallbackControllerSeconds','unfinishedTrips','safetyFaults']
        w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(trials)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plots=PUB/'plots';plots.mkdir(exist_ok=True)
    fig,axes=plt.subplots(1,3,figsize=(15,5),layout='constrained')
    for ax,scale in zip(axes,(.75,1.,1.75)):
        gs=[g for g in groups if g['scale']==scale]
        ax.bar([g['mode'] for g in gs],[g['delayMean'] for g in gs],yerr=[g['delaySD'] for g in gs],capsize=3)
        ax.set_title(f'Demand {scale}; n=3');ax.tick_params(axis='x',rotation=45);ax.set_ylabel('Completed-trip timeLoss (s)')
    fig.suptitle('Phase5 frozen candidate (offline supervised); mean ±sample SD; 600s cold start')
    for ext in ('png','svg'):fig.savefig(plots/f'benchmarks.{ext}',dpi=160)
    plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(15,5),layout='constrained')
    for ax,scale in zip(axes,(.75,1.,1.75)):
        gs=[g for g in ablations if g['scale']==scale]
        ax.bar([g['variant'] for g in gs],[g['delayMean'] for g in gs],yerr=[g['delaySD'] for g in gs],capsize=3)
        ax.set_title(f'Demand {scale}; n=3');ax.tick_params(axis='x',rotation=45);ax.set_ylabel('Completed-trip timeLoss (s)')
    fig.suptitle('Diagnostic hint ablations; 600s cold start; shadow solve instrumentation')
    for ext in ('png','svg'):fig.savefig(plots/f'ablations.{ext}',dpi=160)
    plt.close(fig)
    backend=ET.parse(OUT/'backend.xml').getroot().find('testsuite').attrib
    demos=read(OUT/'demo-results.json')
    assert demos['complete'] and all(r['status']=='passed' for r in demos['results'])
    testtext=f"Backend: {backend['tests']} tests, {backend['failures']} failures, {backend['errors']} errors, {backend['skipped']} skipped, {backend['time']}s; one existing Starlette/httpx warning. Frontend build, TypeScript and8/8 unit/demo groups passed. Browser initial run:3 passed/1 camera skipped in29.9s; camera rerun with config:1 passed in18.2s (all four distinct cases passed). External A–H:8/8 passed. Startup smoke/readiness/cleanup on8026/3026 and pip check passed."
    failnames=[c['name'] for c in checks if not c['passed']]
    training=[]
    for seed in (61,71,81):
        r=read(OUT/f'training/train-{seed}/training.json')
        training.append([seed,r['trainedDecisionSteps'],f"{r['elapsedSeconds']:.2f}",f"{r['updates'][0]['valueLoss']:.2f} → {r['updates'][-1]['valueLoss']:.2f}"])
    bench_table=table(['Load','Mode','Delay mean ±SD s','Throughput veh/h','Mean queue','Worst service age s'],
        [[g['scale'],g['mode'],f"{g['delayMean']:.3f} ±{g['delaySD']:.3f}",f"{g['throughputMean']:.1f}",f"{g['meanQueue']:.2f}",g['maxServiceAge']] for g in groups])
    ab_table=table(['Load','Hint','Delay mean ±SD s','Changed /eligible MPC calls','Worst service age s'],
        [[g['scale'],g['variant'],f"{g['delayMean']:.3f} ±{g['delaySD']:.3f}",f"{g['changedRemaining']}/{g['eligibleComparisons']} ({g['changedPercent']:.1f}%)",g['maxServiceAge']] for g in ablations])
    changes=', '.join(f"load{k}: {v:+.3f}%" for k,v in improvements.items())
    md('FINAL_DEMO_READINESS_REPORT.md',f'''# Final demo readiness — Phase5

The existing demonstration remains runnable in supervised MPC/Max-Pressure mode. MAPPO remains disabled. No controller, supervisor, route, existing learner or frontend implementation was replaced. Phase4 reports, data and weights remain separate and preserved.

## Completed verification

{testtext}

All eight cases exercised real HTTP/WebSocket/SUMO or recorded-video paths. Pedestrian and emergency controls, blocked receiver handling, forecasts and camera/sensor fallback were observed. Raw evidence: `.checkpoints/phase5/backend.xml`, `browser.log`, `browser-camera.log`, `demo-results.json`, `startup-smoke.log` and frontend logs. Runs on the same machine may overlap, so durations are not isolated performance measures.

## Completion and limitations

Frontend/API/WebSocket/SUMO, state estimation, adaptive controls, independent safety gate, supplied pedestrian/emergency scenarios, camera recording and forecast demonstration paths: verified within supplied cases. MAPPO training, inference-to-MPC and offline ablation infrastructure: verified; useful qualified policy: incomplete/failed screening. Live field camera accuracy, historical forecast accuracy, road deployment, exhaustive weather/safety validation: not performed. No tests are blocked on missing video in the final evidence; the initially skipped camera browser case passed after configuration.

New Phase5 scope:54 diagnostic ablations, three1024-decision independent-clipping training seeds,12 selection trials,45 held-out600s benchmark trials,three240s safety trials and24 single-junction challenge trials. Challenge outcomes and failed screens are in the research/qualification reports.

## Launch and preserve

Run `.\\backend\\.venv\\Scripts\\python.exe scripts/run_dev.py`; open http://127.0.0.1:3001. Select Hybrid/network then Start. Default is stopped fixed-time; keep policy environment variables unset. See [DEMONSTRATION_GUIDE.md](DEMONSTRATION_GUIDE.md) for a repeatable presentation and expected observations, [RUN_INSTRUCTIONS.md](RUN_INSTRUCTIONS.md) for installation, and `.checkpoints/PHASE5_RECOVERY.json` for verified source/artifact/Git-bundle copies. Copies are on this machine, not off-device. No publication/push.
''')
    md('MAPPO_DIAGNOSTIC_REPORT.md',f'''# MAPPO diagnostic report — Phase5

## Executable path and influence

SUMO per-junction observations → shared actor8→32→32→2 → release/hold preferences → HybridNetwork.before_step(training_actions) → constrained MPC candidate objective → selected remaining green → independent supervisor.validate_duration/apply_duration → TraCI setPhaseDuration. No research actor writes signals directly. Emergency handling precedes normal MPC; clearance/minimum service/fairness can remove hint influence. The runtime qualification gate stays intact.

At each normal MPC call, a no-write shadow solve evaluated the same observed state without hints; diagnostics were restored before the actual solve. Denominator below includes only pairs where both solves succeeded as constrained MPC. These are recommendation changes, not independent causal traffic counterfactuals. The full recommendation traces plus retained supervisor decisions are archived. End-to-end traffic effects come from separate matched rollouts. Shadow overhead affects latency/timeout exposure; do not treat instrumented timings as operational timing.

{ab_table}

Frozen Phase4 actor joint action counts across all nine diagnostic trials: `{json.dumps(trained_actions)}`. Exact tripinfo attribute equivalence to constant hold: {sum(r['exactTripAttributesIdentical'] for r in equivalence if r['comparison']=='hold')}/9; to untrained seed41 actor: {sum(r['exactTripAttributesIdentical'] for r in equivalence if r['comparison']=='untrained')}/9. Exact equality is checked on sorted completed/unfinished trip attributes,not assumed from mean delay. It does not prove identical full trajectories. Full action histograms and traces remain in raw evidence.

![Ablations](research/phase5/plots/ablations.png)

## Learning and observation diagnosis

The two-action representation changes a preference penalty over remaining-green choices1/2/5/10s; it neither selects an arbitrary phase nor directly commits the planned next green. MPC replans every second, and recommendations are retained for five-second decisions. Actions during minimum service/clearance/expiry have no normal MPC control effect. This limits temporal credit assignment, but measured influence rules out a universally disconnected hint interface.

Actor inputs omit explicit maximum-red/service age, directional receiver occupancy, arrivals/forecast uncertainty, emergency and pedestrian state and neighboring-junction measurements. Only four queues, two green flags, remaining time and mean receiver occupancy are present. Reward penalizes service age and waiting that the actor cannot uniquely infer from these inputs. The centralized critic sees concatenated local inputs, not these missing hidden variables. Directional receiver averaging loses information. These are code-observed observability limitations, not a demonstrated quantitative cause of failure.

Seed5199 real64-decision diagnostic: actor gradient norm{gradients['actorGradientNorm']:.6f}; weighted critic{gradients['criticWeightedGradientNorm']:.6f}; joint clip multiplier{gradients['jointClipMultiplier']:.6f}. Mean return{gradients['returnMean']:.3f} versus critic prediction{gradients['predictedValueMean']:.3f}; value MSE{gradients['meanSquaredValueError']:.3f}. Reward scale/critic fit remain concerns. Adam partly cancels uniform gradient scaling, so raw clipping is not by itself proof of actor starvation.

Restored-optimizer four-epoch paired update probe: {json.dumps(gradients['optimizerAblation'],ensure_ascii=False)}

This supported one isolated independent-clipping training experiment. It does not establish optimizer superiority: new models use different initial seeds from Phase4, and no matched full-training joint-clipping cohort was run. Changes to reward/features/action space require new controlled training, not tuning on final tests. Training rewards are not qualification evidence. See [PHASE5_EXPERIMENT_RESULTS.md](PHASE5_EXPERIMENT_RESULTS.md).

## Evidence-supported next work

Inspect greedy action collapse and static/untrained equivalence in `research/phase5/results.json` and raw jointActionCounts before spending more training. Add explicit service-age and directional receiving state only in a versioned offline observation experiment, with new model compatibility hashes. Diagnose critic normalization/value learning with paired training seeds. Compare richer timing actions only after state/credit-assignment ablations, keeping MPC/supervisor authority. No additional speculative production features were added.
''')
    md('PHASE5_EXPERIMENT_RESULTS.md',f'''# Phase5 experiment results

Protocol: [PHASE5_EXPERIMENT_PLAN.md](PHASE5_EXPERIMENT_PLAN.md). Diagnostic seeds5101–5103,three loads,600s; gradient seed5199. Training seeds61/71/81,episode seeds61000–61015,71000–71015,81000–81015. Independent actor/critic0.5 clipping is the sole learner change; same actor/critic,reward,observations,PPO settings and safe actuation path. Each run16×64=1024 joint decisions/2048 agent samples. Limited experience is not convergence. CPU-only Torch and Phase4 environment retained; raw provenance contains versions and experimental learner SHA.

{table(['Seed','Joint decisions','Measured update wall seconds','First →last critic loss'],training)}

Times include SUMO/control/training/checkpoint I/O, exclude import/model setup and inter-update reporting, and sum concurrent processes rather than calendar elapsed time. All checkpoints/progress logs preserved. Selection seeds6201–6203,demand1.0,300s; selected checkpoint `{selection['selectedCheckpoint']}`, SHA256 `{selection['checkpointSha256']}`. Selection was frozen before final seeds6301–6303 at0.75/1.0/1.75,600s. Safety seeds6501–6503,240s. Challenge seeds6401–6403. No original Phase4 held-out seeds used for tuning or new selection.

## Held-out installed-controller comparison

{bench_table}

Mean candidate delay reduction versus MPC: {changes}. A positive number means lower completed-trip timeLoss; it is not proof of significance or learning causality. Hint-free hybrid is MPC without hints. Native fixed-time uses its original clearance budget, unlike adaptive modes; candidate–MPC comparisons share the same adaptive safety program. Cold-start,censored completed trips,one corridor and n=3 limit generalization. Full metrics include throughput,unfinished trips,waiting,queues,spills,fairness,latency and fallback exposure in [trial JSON](research/phase5/trials.json) and [CSV](research/phase5/trials.csv).

![Benchmarks](research/phase5/plots/benchmarks.png)

## Asymmetric, blocked-exit and protected-user challenges

{table(['Case','Variant','Seed','Status','Mean completed timeLoss s','Worst service age s'],[[r['case'],r['variant'],r['seed'],r['status'],round(r.get('meanCompletedTimeLossSeconds',0) or 0,3),r.get('maxServiceAgeSeconds','n/a')] for r in challenges])}

These24 trials use the existing single-junction runtime for MPC and the frozen shared actor. Duplicated local input satisfies the unused two-agent critic shape; each actor remains local. They are candidate-specific topology-transfer tests, not equivalent two-junction combined pedestrian/emergency qualification. Delay/throughput/queues/spillback,full-step latency,waiting/service age,faults and fallback exposure are retained. Full-step timing includes simulation/telemetry and is not comparable to corridor before_step-only latency. Failed assertions/faults remain visible,never relabeled passed.

## Completed, failed, blocked and unperformed

Completed:54 diagnostic runs,three training runs,12 selection,45 final corridor trials,three safety trials,24 challenge attempts and regression evidence. Failed performance screens: {len(failnames)}; failed challenge trials: {sum(r['status']!='completed' for r in challenges)}. Blocked by dependencies: none recorded after camera configuration. Not performed: paired full-training optimizer causal ablation,large-budget convergence,unseen-network multi-junction protected-user qualification,positive qualified-policy operational/browser activation,field/perception/weather accuracy and statistical superiority. No model is activated. Further broad training is deferred until these diagnostics justify a new controlled protocol.

{testtext}
''')
    md('UPDATED_POLICY_QUALIFICATION_REPORT.md',f'''# Updated policy qualification — Phase5

**Not qualified; MAPPO remains operationally disabled.** Supervised MPC with Max-Pressure fallback is preserved. Actual MAPPOCoordinator refused the selected candidate with the published report. The Phase4 report remains unchanged and its failed policy was not reused as new training weights.

Selected SHA256 `{selection['checkpointSha256']}`; source/controller fingerprint `{qualification_fingerprint()}`. Trained1024 decisions; numerical checks:{safety['numericalChecksPassed']}; separate safety validation:{safety.get('safetyValidationPassed',False)}. Mean delay reductions versus MPC: {changes}.

The original gate requires≥2% mean delay reduction in every demand stratum,no paired delay regression>5%,no throughput loss>2%,no increased maximum service age,no faults/rejections,current provenance and independent protected-user evidence. These are conservative research screens,not road certification. No criterion was relaxed.

Failed performance conditions:

{chr(10).join('- '+n for n in failnames) or '- None recorded; remaining coverage requirements still prevent activation.'}

Candidate single-junction transfer challenge checks passed:{challenge_ok}. Combined pedestrian/emergency operation on the original two-junction policy topology remains unverified. A positive qualified-policy API/browser test was not attempted. These missing requirements are not reported as safety failures or successful tests. Full machine evidence: [policy-qualification.json](research/phase5/policy-qualification.json).

No policy environment variables were set. No learned actor writes TraCI signals directly; all offline preferences pass through MPC and the existing independent supervisor. Keep both SYNCHROFLOW_MAPPO_CHECKPOINT and SYNCHROFLOW_MAPPO_VALIDATION unset. Future selection/tuning requires new held-out seeds,not reusing6301–6303. No improvement,convergence,statistical significance,real-road superiority or safety certification is inferred beyond the measured results.
''')
    write(OUT/'final-verification.json',dict(backend=backend,externalDemos=8,browserDistinctCasesPassed=4,
        initialBrowserSkipped=1,cameraRerunPassed=True,frontendBuild='passed',typescript='passed',frontendGroupsPassed=8,
        startupSmoke='passed_owned_ports_closed',pipCheck='passed',diagnosticTrials=54,benchmarkTrials=45,
        challengeTrials=24,challengeFailures=sum(r['status']!='completed' for r in challenges),
        failedPerformanceScreens=failnames,operationallyEnabled=False,architectureFingerprint=qualification_fingerprint()))
    print(json.dumps(dict(meanDelayReductionPercent=improvements,failedPerformanceChecks=failnames,challengePassed=challenge_ok),indent=2))


if __name__=='__main__':main()
