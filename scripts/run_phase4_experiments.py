"""Wait for recorded training, freeze selection, then run the held-out protocol.

This script never sets operational MAPPO environment variables.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'.checkpoints/phase4-final'
PYTHON = sys.executable


def run(arguments, log_name):
    with (OUT/f'{log_name}.log').open('w', encoding='utf-8') as log:
        subprocess.run([PYTHON, str(ROOT/'scripts/research_phase4.py'), *arguments],
                       cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)


def batch(arguments, seeds, prefix):
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(run, [*arguments, '--seeds', str(seed)], f'{prefix}-{seed}') for seed in seeds]
        for future in futures:
            future.result()


def main():
    reports = [OUT/f'train-{seed}/training.json' for seed in (21,31,41)]
    while not all(p.exists() and len(json.loads(p.read_text())['updates']) >= 16 for p in reports):
        time.sleep(5)
    checkpoints = [str(Path('.checkpoints/phase4-final')/p.parent.name/Path(json.loads(p.read_text())['latestCheckpoint']).name)
                   for p in reports]
    batch(['benchmark','--seconds','300','--scales','1','--modes','mpc',
           '--checkpoints',*checkpoints,'--split','selection'], [1801,1802,1803], 'selection')
    scores = {}
    for checkpoint in checkpoints:
        label = Path(checkpoint).parent.name
        rows = [json.loads((OUT/'trials'/f'selection-{label}-d1.0-s{seed}-t300.json').read_text())
                for seed in (1801,1802,1803)]
        if any(r['status'] != 'completed' for r in rows):
            scores[checkpoint] = None
        else:
            scores[checkpoint] = sum(r['meanCompletedTimeLossSeconds'] for r in rows)/3
    finite = {k:v for k,v in scores.items() if v is not None}
    if not finite:
        raise RuntimeError('All selection candidates failed; inspect evidence')
    selected = min(finite, key=lambda k:(finite[k], int(Path(k).parent.name.split('-')[1])))
    selection = dict(scores=scores, selectedCheckpoint=selected,
                     checkpointSha256=hashlib.sha256(Path(selected).read_bytes()).hexdigest(),
                     selectionSeeds=[1801,1802,1803], testSeeds=[1901,1902,1903],
                     criterion='lowest mean completed-trip timeLoss; model-seed tie break',
                     frozenBeforeFinalTesting=True)
    selection_path = OUT/'selection.json'
    if selection_path.exists() and json.loads(selection_path.read_text()) != selection:
        raise RuntimeError('Frozen selection mismatch')
    selection_path.write_text(json.dumps(selection,indent=2),encoding='utf-8')
    batch(['benchmark','--seconds','300','--scales','.75','1.75',
           '--modes','fixed_time','max_pressure','mpc','hybrid',
           '--checkpoints',selected,'--split','test'], [1901,1902,1903], 'test')
    with (OUT/'qualification.log').open('w',encoding='utf-8') as log:
        subprocess.run([PYTHON,str(ROOT/'scripts/qualify_mappo.py'),'--checkpoint',selected,
                        '--output',str(OUT/'safety-qualification.json'),
                        '--seeds','1951','1952','1953','--seconds','240'],cwd=ROOT,
                       stdout=log,stderr=subprocess.STDOUT,check=True)
    (OUT/'experiments-complete.json').write_text(json.dumps(selection,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
