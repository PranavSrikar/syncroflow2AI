# Phase 5 recovery checkpoint

Current pointer: `.checkpoints/PHASE5_RECOVERY.json`. Phase5 source, raw research data, all checkpoints, camera assets and Git history are archived with verified manifests and separate same-machine copies. The Phase4 pointer and every previous archive remain preserved. Branch: `phase5-diagnostics`; final tag: `phase5-evaluated-prototype`. Nothing pushed; these copies are not off-device backups.

Restore into a new empty folder using the matching source/artifact archives and hashes. Keep the original archives intact. Do not activate unqualified weights. Read [FINAL_DEMO_READINESS_REPORT.md](FINAL_DEMO_READINESS_REPORT.md), [PHASE5_EXPERIMENT_RESULTS.md](PHASE5_EXPERIMENT_RESULTS.md) and [DEMONSTRATION_GUIDE.md](DEMONSTRATION_GUIDE.md). Phase5 completed its bounded experiments; do not restart completed training. Earlier recovery notes follow.

---

# Phase 4 recovery and Git update

Git for Windows2.55.0.windows.5 is installed at `C:/Program Files/Git/cmd/git.exe`. New shells inherit its installed machine PATH; existing shells may need restarting or the absolute path. The original export had no Git history. Local tag `stage3-verified-demo` preserves all167 manifest files byte-for-byte in its initial commit; later commits preserve research changes. No force-push, remote or publication occurred.

Stage3 source/artifact archives, their separate copies, ZIP CRCs and every manifest entry were verified before changes. The final Phase4 recovery pointer `.checkpoints/PHASE4_RECOVERY.json` lists source/artifact archives and a Git bundle, exact hashes and separate copies. Research artifacts include every update checkpoint, raw tripinfo, training/configuration logs, qualification,tests,environment freeze and the available recorded-video/YOLO assets. Original Stage1/2/3 recovery copies remain untouched. Separate copies are on the same machine, not off-device backups.

Restore source into a new empty folder; verify SHA-256 and CHECKPOINT_MANIFEST.json before extracting matching artifacts. Never extract over current work. For Git history use `git clone <bundle-path> <new-folder>`; do not initialize over another repository. Install dependencies and rerun checks using RUN_INSTRUCTIONS.md. Templates/Dockerfile/extensionless public assets are now included by the source archiver; personal.env credentials remain excluded. Never enable unqualified saved weights. Keep checkpoint/architecture hashes intact; Git line-ending conversion or controller edits can invalidate byte-based qualification fingerprints, requiring fresh validation.

After relocating a restored run,update only the copied training.json `latestCheckpoint` path to the restored file before `--resume`; preserve original archived reports,weight bytes and source/configuration hashes. Recreate matching dependencies and use a new run if compatibility checks fail. Stage3 recovery notes below are historical; the current Git availability and Phase4 paths above supersede them.

---

# Final recovery guide

Final source/artifact archives and separate copies are listed in `.checkpoints/STAGE3_RECOVERY.json`, with SHA-256 hashes and verified-file counts. Copies reside under `../synchroflow-known-good-recovery`. Git remains absent from PATH/standard locations and this export has no .git directory. No history initialization, commits, push or remote backup is claimed.

Stage 1/2 and older known-good archives were preserved. Their pointers remain `.checkpoints/STAGE1_RECOVERY.json` and `STAGE2_RECOVERY.json`. Before Stage 3, all 159 Stage 2 source hashes and both archive copies verified. Four original networks retain prior hashes; demo fixtures are additive.

## Restore safely

1. Extract source into a **new empty folder**, never over this workspace.
2. Verify every CHECKPOINT_MANIFEST.json entry against its SHA-256. ZIP CRC and archived hashes were checked at creation and after separate copying.
3. Extract matching artifacts there. They include video/weights, research smoke weights/reports, test evidence and environment freeze. Generated assets are separate from source.
4. Recreate Python environment; install backend/requirements.txt and npm.cmd ci. Camera/torch dependencies remain optional. SUMO 1.28.0 must be on PATH; occupancy normalization was verified with that version.
5. Regenerate camera absolute paths using RUN_INSTRUCTIONS.md. Reload process-local historical/weather/settings. Preserve personal .env separately; credentials are excluded.
6. Rerun startup smoke/backend/browser checks. Never activate archived unqualified MAPPO weights.

## Runtime recovery

Inspect faults, Stop, select fixed-time baseline, then Start. Invalid feedback, occupied clearance or fairness infeasibility pauses simulation; do not bypass gates. A stuck native camera driver may require backend restart. Use one backend worker. The startup helper preserves occupied ports and cleans up only its owned servers.

Startup: `.\backend\.venv\Scripts\python.exe scripts/run_dev.py`. Read FINAL_DEMO_REPORT.md and RUN_INSTRUCTIONS.md. `scripts/checkpoint.py` creates a new verified source ZIP, not Git history or an off-device backup.
