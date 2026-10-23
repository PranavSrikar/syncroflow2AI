> Current entry point: [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md) and [README.md](README.md). The phase-specific notes below are retained historical instructions; use the handoff for current code, safety constraints, setup and tests.

# Phase 5 demonstration

Start from the project folder with `.\backend\.venv\Scripts\python.exe scripts/run_dev.py`, open http://127.0.0.1:3001, choose Hybrid/network, then Start. Keep both MAPPO policy environment variables unset: the new candidate failed qualification. Supervised MPC/Max-Pressure remains operational. Existing occupied ports are preserved.

Read [DEMONSTRATION_GUIDE.md](DEMONSTRATION_GUIDE.md) for the eight repeatable scenarios, camera configuration and expected observations; [FINAL_DEMO_READINESS_REPORT.md](FINAL_DEMO_READINESS_REPORT.md) records startup/shutdown and regression outcomes. Phase5 experiments are complete; raw evidence is in `.checkpoints/phase5`, published results in `research/phase5`, and recovery in `.checkpoints/PHASE5_RECOVERY.json`. Earlier installation/research instructions follow.

---

# Phase 4 research commands

Set `$env:DEBUG='false'` before research commands in PowerShell. The existing demo startup is unchanged: `./backend/.venv/Scripts/python.exe scripts/run_dev.py`. MAPPO remains disabled; do not configure unqualified candidate weights. Git is installed; restart older terminals to refresh PATH, or use `C:/Program Files/Git/cmd/git.exe`.

Read PHASE4_EXPERIMENT_PLAN.md and the four research reports before new experiments. Training: `./backend/.venv/Scripts/python.exe scripts/research_phase4.py train --seeds 51 61 71 --updates 16 --rollout 64`. Use fresh model seeds/directories; existing checkpoints are protected. Resume only with matching original code/configuration. Offline trials accept `benchmark --seconds 300 --seeds 1001 1002 1003 --scales .75 1.75 --modes fixed_time max_pressure mpc hybrid --split test`; candidate weights require `--checkpoints <path>`, matching training provenance and disjoint seeds. These research trials retain all existing supervisor checks.

Rebuild this completed experiment's charts and reports with `scripts/summarize_phase4.py` followed by `scripts/report_phase4.py`, using the project Python. Artifacts are restored from the Phase4 recovery archive. Do not overwrite frozen selection/test evidence for a new experiment. Install optional training/plotting dependencies with `./backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-research.txt`; the run's environment-freeze.txt records exact installed versions. Use `--output-dir <new-folder>` before the training/benchmark subcommand for separate research data. The three-seed protocol driver `scripts/run_phase4_experiments.py` waits for the recorded21/31/41 runs and reuses matching cached trials; it is not a generic experiment partition generator.

---

# Launch and demonstrate SYNCHROFLOW AI

Run PowerShell from the project folder. Verified environment: Python 3.11.9, Node 24.21.0, SUMO 1.28.0; dependency versions are preserved in the artifact freeze. Use one backend worker.

## Start the existing installed prototype

```powershell
./backend/.venv/Scripts/python.exe scripts/run_dev.py
```

Open http://127.0.0.1:3001; backend docs http://127.0.0.1:8001/docs. Startup reports detected dependencies, SUMO version, actual backend/frontend readiness, controller and simulation status. Default startup is stopped fixed-time. Choose Hybrid and a Network, then Start. Pause before stepping; Stop before changing network/controller.

Ctrl+C cleans up this launcher's own SUMO/cameras and child servers. Occupied ports are preserved and reported; use different ports if needed:

```powershell
./backend/.venv/Scripts/python.exe scripts/run_dev.py --backend-port 8020 --frontend-port 3020
./backend/.venv/Scripts/python.exe scripts/run_dev.py --backend-port 8020 --frontend-port 3020 --smoke-test
```

The agent verified and left the final services on 8001/3001, with SUMO/cameras stopped. If still running, open the existing URL instead of launching duplicates. Processes need restarting after session/process shutdown.

## Restore missing dependencies

If no environment exists:

```powershell
py -3.11 -m venv backend/.venv
./backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
npm.cmd ci
```

Install SUMO 1.28 and place its bin directory on PATH. Camera libraries and torch are optional for SUMO-only operation. To use video/research training:

```powershell
./backend/.venv/Scripts/python.exe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
./backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-perception.txt
```

Verified torch/torchvision: 2.14.1+cpu / 0.29.1. Use the preserved environment freeze for exact reconstruction. Never enable archived unqualified research weights.

## Camera demo configuration

Restore video/weights from the Phase 4 artifact archive (the original Stage 3 copy also remains available), or use the source URLs in STAGE1_IMPLEMENTATION.md. From the project root, regenerate an API camera array with this workspace's absolute paths:

```powershell
$camera=Get-Content backend/examples/camera-road.example.json -Raw | ConvertFrom-Json
$camera.source=(Resolve-Path '.checkpoints/perception/road.mp4').Path
$camera.weights=(Resolve-Path '.checkpoints/perception/yolo11n.pt').Path
$json=ConvertTo-Json -InputObject @($camera) -Depth 12
[IO.File]::WriteAllText((Join-Path (Get-Location) '.checkpoints/perception/cameras-api.json'),$json,(New-Object Text.UTF8Encoding($false)))
$env:SYNCHROFLOW_CAMERA_CONFIG=(Resolve-Path '.checkpoints/perception/cameras-api.json').Path
./backend/.venv/Scripts/python.exe scripts/run_dev.py
```

Set the variable before backend startup. The command writes BOM-free UTF-8 and works in Windows PowerShell 5.

Choose Configured cameras and Start cameras in the dashboard. Camera mode supplies observations only. No physical calibration, live-hardware accuracy or road-signal actuation is established. Offline CLI:

```powershell
./backend/.venv/Scripts/python.exe scripts/perceive_video.py --config backend/examples/camera-road.example.json --output .checkpoints/perception/demo-inference.jsonl --max-frames 60
```

## A-H repeatable release demos

Use a stopped disposable simulation/camera session. The runner refuses active sessions and saves actual results after each completed case:

```powershell
./backend/.venv/Scripts/python.exe scripts/demo_release.py --base-url http://127.0.0.1:8001/api/v1 --with-example-forecast --output .checkpoints/my-demo-results.json
```

The example-forecast flag explicitly feeds labeled artificial history/weather into MPC for A only, then disables forecasting. It does not establish real forecast accuracy. Omit the flag for measured-arrival fallback. `--scenario A` through `H` runs one case. H explicitly skips when no camera config exists; invalid configured sources fail visibly.

A normal adaptive; B unequal north demand; C blocked south exit/spillback; D pedestrians; E emergency; F A0/B0 hybrid; G missing-camera/zero-budget fallback; H actual video inference. FINAL_DEMO_REPORT.md contains startup selections, expected observations, actual results and limitations for every case.

API example for reproducible paused corridor operation:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8001/api/v1/sumo/start?scenario=corridor&controller=hybrid&seed=95&paused=true' -Method Post
Invoke-RestMethod 'http://127.0.0.1:8001/api/v1/sumo/step' -Method Post
Invoke-RestMethod 'http://127.0.0.1:8001/api/v1/sumo/status'
Invoke-RestMethod 'http://127.0.0.1:8001/api/v1/sumo/stop' -Method Post
```

Normal unseeded starts preserve SUMO's default seed 23423. `mpc_budget_ms=0` deliberately tests fallback; it is not a normal performance setting. Scenario values: vehicle, unequal, spillback, pedestrian, corridor. Controller values: sumo_fixed_time, max_pressure, mpc, hybrid. Emergency JSON accepts junctionId A0/B0 in corridor mode. WebSocket: /api/v1/sumo/ws. History/weather configuration: STAGE1_IMPLEMENTATION.md; qualified-policy workflow: STAGE2_IMPLEMENTATION.md, interpreted with the final report's current validation limits.

## Tests

```powershell
$env:DEBUG='false'
$env:SYNCHROFLOW_TEST_VIDEO=(Resolve-Path '.checkpoints/perception/road.mp4').Path
$env:SYNCHROFLOW_TEST_WEIGHTS=(Resolve-Path '.checkpoints/perception/yolo11n.pt').Path
Push-Location backend
./.venv/Scripts/python.exe -m pytest -o addopts='-ra'
Pop-Location
npm.cmd run build
npm.cmd run lint
npm.cmd test
$env:SYNCHROFLOW_CAMERA_CONFIG=(Resolve-Path '.checkpoints/perception/cameras-api.json').Path
npm.cmd run test:e2e
```

Browser tests use installed Edge and isolated ports 8017/3017. Do not run them against an active user's simulation. To verify the running final services instead:

```powershell
$env:SYNCHROFLOW_EXTERNAL_SERVERS='1'
$env:SYNCHROFLOW_TEST_URL='http://127.0.0.1:3001'
$env:SYNCHROFLOW_TEST_API='http://127.0.0.1:8001/api/v1'
npm.cmd run test:e2e
```

This changes/stops simulation and camera state. Unset SYNCHROFLOW_EXTERNAL_SERVERS before returning to isolated test startup. Real-video tests explicitly skip if assets/dependencies are absent; they were enabled for the final release verification. See TEST_RESULTS.md for exact results and RECOVERY_GUIDE.md for archives/restoration. No push or remote backup occurred.
