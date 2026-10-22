"""Passive paired-data audit of whether observed hints changed measured outcomes."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.checkpoints/phase4-final'


def trips(row):
    name=f"{row['split']}-{row['model']}-d{row['demandScale']}-s{row['seed']}-t{row['seconds']}.xml"
    return sorted((t.attrib for t in ET.parse(OUT/'trips'/name).getroot().findall('tripinfo')),key=lambda t:t['id'])


def decisions(row):
    return {agent:[{k:d.get(k) for k in ('simTime','accepted','phaseIndex','remainingSec')}
                   for d in report['decisions']] for agent,report in row['supervisors'].items()}


def main():
    rows=[json.loads(p.read_text()) for p in (OUT/'trials').glob('*.json')]
    pairs=[]
    for candidate in rows:
        if candidate['mode']!='candidate' or candidate['status']!='completed': continue
        baseline=next((r for r in rows if r['mode']=='mpc' and r['status']=='completed'
                       and all(r[k]==candidate[k] for k in ('split','seed','seconds','demandScale'))),None)
        if baseline is None: continue
        pairs.append(dict(split=candidate['split'],model=candidate['model'],seed=candidate['seed'],
                          demandScale=candidate['demandScale'],jointActionCounts=candidate['jointActionCounts'],
                          hintControllerSeconds=candidate['hintControllerSeconds'],
                          recordedTripAttributesIdentical=trips(candidate)==trips(baseline),
                          retainedSafetyDecisionsIdentical=decisions(candidate)==decisions(baseline),
                          delayDifferenceSeconds=candidate['meanCompletedTimeLossSeconds']-baseline['meanCompletedTimeLossSeconds']))
    report=dict(pairs=pairs,limitations='Passive comparisons only. Trip attributes are completed/unfinished outcome summaries, not trajectories. Safety histories retain only100 entries per junction. No causal all-hold/all-release intervention was run. Identical results do not distinguish constraint dominance, weak hint weight, or policy coverage.')
    (OUT/'hint-effect-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(pairs=len(pairs),identicalTripOutcomes=sum(p['recordedTripAttributesIdentical'] for p in pairs),
                          identicalRetainedSafetyDecisions=sum(p['retainedSafetyDecisionsIdentical'] for p in pairs))))


if __name__=='__main__': main()
