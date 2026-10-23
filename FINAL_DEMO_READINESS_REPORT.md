# Final demo readiness — Phase5

The existing demonstration remains runnable in supervised MPC/Max-Pressure mode. MAPPO remains disabled. No controller, supervisor, route, existing learner or frontend implementation was replaced. Phase4 reports, data and weights remain separate and preserved.

## Completed verification

Backend: 108 tests, 0 failures, 0 errors, 0 skipped, 165.027s; one existing Starlette/httpx warning. Frontend build, TypeScript and8/8 unit/demo groups passed. Browser initial run:3 passed/1 camera skipped in29.9s; camera rerun with config:1 passed in18.2s (all four distinct cases passed). External A–H:8/8 passed. Startup smoke/readiness/cleanup on8026/3026 and pip check passed. Actual PTY Ctrl+C after starting SUMO on8027/3027 closed both owned ports; the interrupted terminal wrapper returned exit1,not a clean-exit0 claim.

All eight cases exercised real HTTP/WebSocket/SUMO or recorded-video paths. Pedestrian and emergency controls, blocked receiver handling, forecasts and camera/sensor fallback were observed. Raw evidence: `.checkpoints/phase5/backend.xml`, `browser.log`, `browser-camera.log`, `demo-results.json`, `startup-smoke.log`, `ctrlc-startup.json` and frontend logs. A real browser screenshot and measured corridor state are retained as dashboard.png/dashboard-check.json. Runs on the same machine may overlap, so durations are not isolated performance measures. The full application suite ran before the offline scripts were finalized; application/frontend/controller bytes remained unchanged,and the new research paths were exercised by the actual experiments.

## Completion and limitations

Frontend/API/WebSocket/SUMO, state estimation, adaptive controls, independent safety gate, supplied pedestrian/emergency scenarios, camera recording and forecast demonstration paths: verified within supplied cases. MAPPO training, inference-to-MPC and offline ablation infrastructure: verified; useful qualified policy: incomplete/failed screening. Live field camera accuracy, historical forecast accuracy, road deployment, exhaustive weather/safety validation: not performed. No tests are blocked on missing video in the final evidence; the initially skipped camera browser case passed after configuration.

New Phase5 scope:54 diagnostic ablations, three1024-decision independent-clipping training seeds,12 selection trials,45 held-out600s benchmark trials,three240s safety trials and42 single-junction challenge trials. Challenge outcomes and failed screens are in the research/qualification reports.

## Launch and preserve

Run `.\backend\.venv\Scripts\python.exe scripts/run_dev.py`; open http://127.0.0.1:3001. Select Hybrid/network then Start. Default is stopped fixed-time; keep policy environment variables unset. See [DEMONSTRATION_GUIDE.md](DEMONSTRATION_GUIDE.md) for a repeatable presentation and expected observations, [RUN_INSTRUCTIONS.md](RUN_INSTRUCTIONS.md) for installation, and `.checkpoints/PHASE5_RECOVERY.json` for verified source/artifact/Git-bundle copies. Copies are on this machine, not off-device. No publication/push.
