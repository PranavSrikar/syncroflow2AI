"""Unique verified Phase5 archives; never replaces the Phase4 recovery pointer."""
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
from recover_phase4 import ROOT,digest,verify_zip


def main():
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    separate=ROOT.parent/'synchroflow-known-good-recovery';separate.mkdir(exist_ok=True)
    source=json.loads(subprocess.check_output([sys.executable,str(ROOT/'scripts/checkpoint.py')],cwd=ROOT,text=True))
    source_path=Path(source['archive'])
    git=shutil.which('git') or 'C:/Program Files/Git/cmd/git.exe'
    bundle=ROOT/f'.checkpoints/phase5-history-{stamp}.bundle'
    subprocess.run([git,'bundle','create',str(bundle),'--all'],cwd=ROOT,check=True,capture_output=True)
    subprocess.run([git,'bundle','verify',str(bundle)],cwd=ROOT,check=True,capture_output=True)
    artifacts=ROOT/f'.checkpoints/phase5-artifacts-{stamp}.zip'
    paths=[p for folder in ('phase4','phase4-final','phase4-demand-corrected','phase5','perception')
           for p in (ROOT/'.checkpoints'/folder).rglob('*') if p.is_file() and p.suffix!='.tmp']
    paths += [p for p in (ROOT/'.checkpoints').glob('*RECOVERY.json') if p.name!='PHASE5_RECOVERY.json']
    manifest={}
    with zipfile.ZipFile(artifacts,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(set(paths)):
            name=p.relative_to(ROOT).as_posix();data=p.read_bytes()
            import hashlib
            manifest[name]=hashlib.sha256(data).hexdigest();z.writestr(name,data)
        z.writestr('CHECKPOINT_MANIFEST.json',json.dumps(manifest,indent=2))
    copies=[]
    for path in (source_path,artifacts,bundle):
        count=verify_zip(path) if path.suffix=='.zip' else None
        target=separate/path.name
        if target.exists():raise FileExistsError(target)
        shutil.copy2(path,target)
        if digest(path)!=digest(target):raise ValueError('Recovery copy differs')
        if target.suffix=='.zip':verify_zip(target)
        copies.append(dict(archive=str(path),separateCopy=str(target),sha256=digest(path),verifiedFiles=count))
    pointer=dict(createdUtc=datetime.now(timezone.utc).isoformat(),archives=copies,
        gitCommit=subprocess.check_output([git,'rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        phase4PointerPreserved=True,offDeviceBackup=False,operationalPolicyEnabled=False)
    text=json.dumps(pointer,indent=2)
    (ROOT/'.checkpoints/PHASE5_RECOVERY.json').write_text(text,encoding='utf8')
    (separate/f'{stamp}-PHASE5_RECOVERY.json').write_text(text,encoding='utf8')
    print(text)


if __name__=='__main__':main()
