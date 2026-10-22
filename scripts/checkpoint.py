"""Create a local source checkpoint with a verified SHA-256 manifest.

This is a recovery archive, not Git history or a remote backup. Credentials,
dependencies, generated data, caches and build/test outputs are excluded.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile
import os

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = ("src", "backend", "tests", "public", "scripts", "research")
EXCLUDED = {".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "test-results", "playwright-report"}
EXTENSIONS = {".py", ".ts", ".tsx", ".css", ".xml", ".sumocfg", ".md", ".json", ".toml", ".txt", ".csv", ".png", ".jpg", ".svg", ".html", ".ps1"}


def checkpoint():
    files = [p for p in ROOT.iterdir() if p.is_file() and (p.suffix in EXTENSIONS or p.name in {".gitignore", "bun.lock", ".env.example"}) and (not p.name.startswith(".env") or p.name == ".env.example")]
    for directory in SOURCE_DIRS:
        for parent, folders, names in os.walk(ROOT / directory):
            folders[:] = [d for d in folders if d not in EXCLUDED and not d.startswith(".")]
            for name in names:
                path = Path(parent) / name
                if (path.suffix in EXTENSIONS or name in {"Dockerfile", ".env.example"} or directory == 'public') and (not name.startswith(".env") or name == ".env.example"):
                    files.append(path)
    manifest = {}
    folder = ROOT / ".checkpoints"
    folder.mkdir(exist_ok=True)
    destination = folder / (datetime.now(timezone.utc).strftime("source-%Y%m%dT%H%M%S%fZ") + ".zip")
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(files)):
            relative = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            manifest[relative] = hashlib.sha256(data).hexdigest()
            archive.writestr(relative, data)
        archive.writestr("CHECKPOINT_MANIFEST.json", json.dumps(manifest, indent=2))
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        for relative, digest in manifest.items():
            if hashlib.sha256(archive.read(relative)).hexdigest() != digest:
                raise RuntimeError(f"Checkpoint verification failed: {relative}")
    print(json.dumps({"archive": str(destination), "verifiedFiles": len(manifest), "remoteBackup": False}))


if __name__ == "__main__":
    checkpoint()
