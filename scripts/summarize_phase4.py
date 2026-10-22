"""Publish measured research results; never manufacture policy eligibility."""
import csv
import hashlib
import json
from pathlib import Path
import statistics
import sys
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'.checkpoints/phase4'
PUBLIC = ROOT/'research/phase4'


def write(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,allow_nan=False),encoding='utf-8')


def main():
    selection = json.loads((OUT/'selection.json').read_text())
    safety = json.loads((OUT/'safety-qualification.json').read_text())
    rows = [json.loads(p.read_text()) for p in sorted((OUT/'trials').glob('test-*.json'))]
    if len(rows) != 30 or any(r['status'] != 'completed' for r in rows):
        raise ValueError('Expected 30 completed final trials; incomplete experiments cannot be summarized as complete')
    PUBLIC.mkdir(parents=True,exist_ok=True)
    keys = ['meanCompletedTimeLossSeconds','meanNetworkQueue','maxNetworkQueue',
            'throughputVehiclesPerHour','meanCompletedWaitingSeconds','p95CompletedWaitingSeconds',
            'maxCompletedWaitingSeconds','maxApproachMeanWaitSeconds','maxServiceAgeSeconds',
            'spillbackEdgeSeconds','meanControlLatencyMs','p95ControlLatencyMs','maxControlLatencyMs',
            'completedTrips','unfinishedTrips','meanPolicyInferenceMs','p95PolicyInferenceMs',
            'meanDecisionControlComputeMs','p95DecisionControlComputeMs','fallbackControllerSeconds']
    for row in rows:
        row['supervisorRejections'] = sum(s['rejectedActions'] for s in row['supervisors'].values())
        row['supervisorAcceptedActions'] = sum(s['acceptedActions'] for s in row['supervisors'].values())
        trip_name = f"test-{row['model']}-d{row['demandScale']}-s{row['seed']}-t{row['seconds']}.xml"
        trips = ET.parse(OUT/'trips'/trip_name).getroot().findall('tripinfo')
        waits = np.array([float(t.get('waitingTime','0')) for t in trips])
        losses = [float(t.get('timeLoss','0')) for t in trips]
        # Include right-censored unfinished trips as observed partial timeLoss only.
        row['meanObservedTimeLossIncludingUnfinished'] = float(np.mean(losses))
        row['meanDepartDelaySeconds'] = float(np.mean([float(t.get('departDelay','0')) for t in trips]))
        row['waitingGiniIncludingUnfinished'] = (float(np.abs(waits[:,None]-waits[None,:]).sum()/(2*len(waits)*waits.sum()))
                                                 if waits.sum() else 0.0)
    keys += ['supervisorRejections','supervisorAcceptedActions','meanObservedTimeLossIncludingUnfinished',
             'meanDepartDelaySeconds','waitingGiniIncludingUnfinished']
    fields = ['mode','model','seed','seconds','demandScale',*keys,'wallSeconds','safetyFaults']
    with (PUBLIC/'trials.csv').open('w',newline='',encoding='utf-8') as f:
        writer = csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
        writer.writeheader(); writer.writerows(rows)
    groups=[]
    for scale in (.75,1.75):
        for mode in ('fixed_time','max_pressure','mpc','hybrid','candidate'):
            members=[r for r in rows if r['demandScale']==scale and r['mode']==mode]
            groups.append(dict(mode=mode,demandScale=scale,n=len(members),
                               metrics={k:dict(mean=statistics.mean(r[k] for r in members),
                                               sampleSD=statistics.stdev(r[k] for r in members)) for k in keys}))
    paired=[]
    checks=[]
    for scale in (.75,1.75):
        ratios=[]
        for seed in (901,902,903):
            base=next(r for r in rows if r['mode']=='mpc' and r['seed']==seed and r['demandScale']==scale)
            candidate=next(r for r in rows if r['mode']=='candidate' and r['seed']==seed and r['demandScale']==scale)
            ratio=candidate['meanCompletedTimeLossSeconds']/base['meanCompletedTimeLossSeconds']
            ratios.append(ratio)
            paired.append(dict(seed=seed,demandScale=scale,delayRatio=ratio,
                               delayDifferenceSeconds=candidate['meanCompletedTimeLossSeconds']-base['meanCompletedTimeLossSeconds'],
                               throughputDifference=candidate['arrivedVehicles']-base['arrivedVehicles']))
            checks += [dict(name=f'no_delay_regression_over_5pct_d{scale}_s{seed}',passed=ratio<=1.05),
                       dict(name=f'no_throughput_loss_over_2pct_d{scale}_s{seed}',passed=candidate['arrivedVehicles']>=.98*base['arrivedVehicles']),
                       dict(name=f'no_service_age_increase_d{scale}_s{seed}',passed=candidate['maxServiceAgeSeconds']<=base['maxServiceAgeSeconds']),
                       dict(name=f'no_safety_fault_or_rejection_d{scale}_s{seed}',passed=candidate['safetyFaults']==0 and candidate['supervisorRejections']==0)]
        b=next(g for g in groups if g['mode']=='mpc' and g['demandScale']==scale)['metrics']['meanCompletedTimeLossSeconds']['mean']
        c=next(g for g in groups if g['mode']=='candidate' and g['demandScale']==scale)['metrics']['meanCompletedTimeLossSeconds']['mean']
        checks.append(dict(name=f'at_least_2pct_mean_delay_reduction_d{scale}',passed=c<=.98*b,
                           measuredReductionPercent=(b-c)/b*100))
    checks.append(dict(name='candidate_combined_pedestrian_emergency_validation',passed=False,
                       reason='Corridor has neither pedestrians nor emergency arrivals; baseline regressions are separate'))
    qualification=dict(**safety)
    qualification.update(eligibleForEvaluation=False,usefulnessEstablished=False,
                         status='not_qualified_keep_operational_policy_disabled',
                         performanceValidation=dict(passed=False,checks=checks,pairedComparisons=paired,
                                                    protocol='PHASE4_EXPERIMENT_PLAN.md'),
                         selection=selection, operationallyEnabled=False)
    write(PUBLIC/'policy-qualification.json',qualification)
    write(PUBLIC/'benchmark-summary.json',dict(groups=groups,pairedComparisons=paired,selection=selection,
                                               limitations='Three seeds; cold start; completed-trip delay censored; one topology; no statistical superiority claim'))
    write(PUBLIC/'trials.json',rows)
    plot_dir=PUBLIC/'plots'; plot_dir.mkdir(exist_ok=True)
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    training=[]
    for seed in (21,31,41):
        report=json.loads((OUT/f'train-{seed}/training.json').read_text())
        training.append(report)
        x=[u['trainedDecisionSteps'] for u in report['updates']]
        axes[0].plot(x,[sum(u['reward'])/128 for u in report['updates']],label=f'seed {seed}')
        axes[1].plot(x,[u['valueLoss'] for u in report['updates']],label=f'seed {seed}')
    axes[0].set_ylabel('Mean reward per agent decision'); axes[1].set_ylabel('Clipped critic loss')
    for ax in axes: ax.set_xlabel('Joint training decisions'); ax.legend(); ax.grid(alpha=.2)
    fig.suptitle('MAPPO training: changing episode seeds, no convergence claim'); fig.tight_layout()
    for extension in ('png','svg'): fig.savefig(plot_dir/f'training.{extension}',dpi=160)
    plt.close(fig)
    labels=['fixed_time','max_pressure','mpc','hybrid','candidate']
    fig,axes=plt.subplots(2,3,figsize=(13,7))
    for i,scale in enumerate((.75,1.75)):
        for j,(key,title) in enumerate([('meanCompletedTimeLossSeconds','Completed-trip timeLoss (s)'),
                                        ('meanNetworkQueue','Mean network queue (vehicles)'),
                                        ('throughputVehiclesPerHour','Throughput (vehicles/h)')]):
            values=[next(g for g in groups if g['mode']==m and g['demandScale']==scale)['metrics'][key] for m in labels]
            axes[i,j].bar(range(5),[v['mean'] for v in values],yerr=[v['sampleSD'] for v in values],capsize=4)
            axes[i,j].set_xticks(range(5),['Fixed','MP','MPC','Hybrid','Candidate'],rotation=20)
            axes[i,j].set_title(f'Demand {scale}: {title}'); axes[i,j].grid(axis='y',alpha=.2)
    fig.suptitle('Held-out 300-second corridor trials: mean ± sample SD, n=3; candidate offline only')
    fig.tight_layout()
    for extension in ('png','svg'): fig.savefig(plot_dir/f'benchmarks.{extension}',dpi=160)
    plt.close(fig)
    write(PUBLIC/'training-summary.json',training)
    print(json.dumps(dict(trials=len(rows),qualification=qualification['status'],
                          failedChecks=[c for c in checks if not c['passed']]),indent=2))


if __name__=='__main__':
    main()
