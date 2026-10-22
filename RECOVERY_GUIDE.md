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
