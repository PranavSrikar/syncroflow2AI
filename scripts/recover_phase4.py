"""Make verified, independently copied source/research/Git recovery checkpoints."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_zip(path):
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:
            raise ValueError('ZIP CRC failed')
        manifest=json.loads(z.read('CHECKPOINT_MANIFEST.json'))
        for name,expected in manifest.items():
            if hashlib.sha256(z.read(name)).hexdigest()!=expected:
                raise ValueError(f'Manifest mismatch: {name}')
    return len(manifest)


def recover(label='final'):
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    separate=ROOT.parent/'synchroflow-known-good-recovery'
    separate.mkdir(exist_ok=True)
    source=json.loads(subprocess.check_output([sys.executable,str(ROOT/'scripts/checkpoint.py')],cwd=ROOT,text=True))
    source_path=Path(source['archive'])
    git=shutil.which('git') or 'C:/Program Files/Git/cmd/git.exe'
    bundle=ROOT/f'.checkpoints/phase4-final-history-{stamp}.bundle'
    subprocess.run([git,'bundle','create',str(bundle),'--all'],cwd=ROOT,check=True,capture_output=True)
    subprocess.run([git,'bundle','verify',str(bundle)],cwd=ROOT,check=True,capture_output=True)
    artifacts=ROOT/f'.checkpoints/phase4-final-artifacts-{stamp}.zip'
    paths=[p for folder in (ROOT/'.checkpoints/phase4-final',ROOT/'.checkpoints/phase4')
           for p in folder.rglob('*') if p.is_file() and p.suffix!='.tmp']
    paths += [ROOT/f'.checkpoints/{n}' for n in ('STAGE1_RECOVERY.json','STAGE2_RECOVERY.json','STAGE3_RECOVERY.json','phase4-recovery-audit.json')]
    paths += [p for p in (ROOT/f'.checkpoints/perception/{n}' for n in ('road.mp4','yolo11n.pt','cameras-api.json')) if p.is_file()]
    manifest={}
    with zipfile.ZipFile(artifacts,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(paths):
            relative=p.relative_to(ROOT).as_posix()
            data=p.read_bytes()
            manifest[relative]=hashlib.sha256(data).hexdigest()
            z.writestr(relative,data)
        z.writestr('CHECKPOINT_MANIFEST.json',json.dumps(manifest,indent=2))
    results=[]
    for p in (source_path,artifacts,bundle):
        verified=verify_zip(p) if p.suffix=='.zip' else None
        target=separate/p.name
        if target.exists(): raise FileExistsError(target)
        shutil.copy2(p,target)
        if digest(p)!=digest(target): raise ValueError('Separate recovery copy differs')
        if target.suffix=='.zip': verify_zip(target)
        results.append(dict(archive=str(p),separateCopy=str(target),sha256=digest(p),verifiedFiles=verified))
    pointer=dict(createdUtc=datetime.now(timezone.utc).isoformat(),label=label,archives=results,
                 gitAvailable=True,gitCommit=subprocess.check_output([git,'rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                 stage3Tag='stage3-verified-demo',remoteBackup=False,offDeviceBackup=False,
                 previousRecoveryCopiesPreserved=True)
    name='PHASE4_RECOVERY.json' if label=='final' else f'PHASE4_{label.upper()}_RECOVERY.json'
    (ROOT/'.checkpoints'/name).write_text(json.dumps(pointer,indent=2),encoding='utf-8')
    target=separate/f'{stamp}-{name}'
    target.write_text(json.dumps(pointer,indent=2),encoding='utf-8')
    print(json.dumps(pointer,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--label',default='final',choices=['final','progress'])
    recover(parser.parse_args().label)
