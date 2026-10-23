"""Execute the preregistered Phase5 selection/test partition without activation."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.checkpoints/phase5'
BENCH=OUT/'evaluation'


def batch(seed,split,checkpoints):
    command=[sys.executable,str(ROOT/'scripts/research_phase4.py'),'--output-dir',str(BENCH),'benchmark',
             '--seeds',str(seed),'--seconds','300' if split=='selection' else '600',
             '--scales',*(['1.0'] if split=='selection' else ['0.75','1.0','1.75']),
             '--modes',*(['mpc'] if split=='selection' else ['fixed_time','max_pressure','mpc','hybrid']),
             '--split',split,'--checkpoints',*[str(p) for p in checkpoints]]
    with (OUT/f'{split}-{seed}.log').open('w',encoding='utf8') as log:
        subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)


def main():
    checkpoints=[OUT/f'training/train-{s}/update-0016.pt' for s in (61,71,81)]
    deadline=time.monotonic()+7200
    while not all(p.exists() for p in checkpoints):
        if time.monotonic()>deadline: raise TimeoutError('Training not complete; no qualification attempted')
        time.sleep(5)
    # Check atomic progress report as well as the saved file.
    for p in checkpoints:
        r=json.loads((p.parent/'training.json').read_text())
        if r['trainedDecisionSteps']!=1024: raise ValueError('Incomplete training progress')
    BENCH.mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda s:batch(s,'selection',checkpoints),(6201,6202,6203)))
    rows=[json.loads(p.read_text()) for p in (BENCH/'trials').glob('selection-*.json')]
    if len(rows)!=12 or any(r['status']!='completed' for r in rows): raise ValueError('Selection incomplete/failed')
    scores={str(p):sum(r['meanCompletedTimeLossSeconds'] for r in rows if r['model']==p.parent.name)/3 for p in checkpoints}
    selected=min(checkpoints,key=lambda p:(scores[str(p)],p.parent.name))
    record=dict(scores=scores,selectedCheckpoint=str(selected),checkpointSha256=hashlib.sha256(selected.read_bytes()).hexdigest(),
                selectionSeeds=[6201,6202,6203],testSeeds=[6301,6302,6303],
                criterion='Lowest mean completed-trip timeLoss; model seed tie break',frozenBeforeFinalTesting=True)
    path=BENCH/'selection.json'
    if path.exists() and json.loads(path.read_text())!=record: raise ValueError('Refusing to replace frozen selection')
    path.write_text(json.dumps(record,indent=2),encoding='utf8')
    print(json.dumps(record),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda s:batch(s,'test',[selected]),(6301,6302,6303)))
    with (OUT/'safety.log').open('w',encoding='utf8') as log:
        subprocess.run([sys.executable,str(ROOT/'scripts/qualify_mappo.py'),'--checkpoint',str(selected),
                        '--output',str(OUT/'safety-qualification.json'),'--seeds','6501','6502','6503','--seconds','240'],
                        cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        def challenges(seed):
            with (OUT/f'challenges-{seed}.log').open('w',encoding='utf8') as log:
                subprocess.run([sys.executable,str(ROOT/'scripts/challenge_phase5.py'),'--checkpoint',str(selected),
                                '--seed',str(seed)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        list(pool.map(challenges,(6401,6402,6403)))
    (OUT/'experiments-complete.json').write_text(json.dumps(dict(selection=record,operationallyEnabled=False,
        qualification='Pending report aggregation; safety-only evidence never enables a policy'),indent=2),encoding='utf8')
    print('Phase5 experiments completed; policy remains disabled',flush=True)


if __name__=='__main__':main()
