# SYNCHROFLOW AI repeatable demonstration

Use PowerShell from the project folder. Keep `SYNCHROFLOW_MAPPO_CHECKPOINT` and `SYNCHROFLOW_MAPPO_VALIDATION` unset: no saved policy currently has operational qualification.

```powershell
.\backend\.venv\Scripts\python.exe scripts/run_dev.py
```

Open http://127.0.0.1:3001 and backend documentation http://127.0.0.1:8001/docs. The launcher checks dependencies/SUMO and actual readiness. If those ports already host the existing demo, use that instance or choose free ports with `--backend-port 8025 --frontend-port 3025`. It preserves occupied ports. Default state is stopped fixed-time; select Hybrid and a network before Start. Ctrl+C stops this launcher's own simulation/cameras and server processes. Stop before switching network/controller; Pause before single-stepping.

For the real recorded-video case, configure available local assets before launching:

```powershell
$env:SYNCHROFLOW_CAMERA_CONFIG=(Resolve-Path '.checkpoints/perception/cameras-api.json').Path
.\backend\.venv\Scripts\python.exe scripts/run_dev.py --backend-port 8025 --frontend-port 3025
```

The config contains absolute asset paths; inspect/update a copied config after relocating the project. Without suitable video/weights the camera case explicitly skips; it must not be described as a pass. Camera observations do not independently actuate signals. Forecast examples are explicitly labeled synthetic.

With the disposable backend stopped but ready, run the automated presentation from a second terminal:

```powershell
.\backend\.venv\Scripts\python.exe scripts/demo_release.py --base-url http://127.0.0.1:8025/api/v1 --output .checkpoints/phase5/presentation-results.json --with-example-forecast
```

Use a new output filename to retain previous presentation evidence. The runner refuses an active simulation/camera session, checks actual API/WebSocket state, stops each case and disables the example forecast afterward. An assertion aborts the run and saves the failure. These are fast reproducible checks, not an uninterrupted wall-clock dashboard presentation.

| Case | Procedure/expected observation | Automated scope |
|---|---|---|
| A Normal | Vehicle network, Hybrid; queues and MPC decisions change; labeled EXAMPLE forecast reaches MPC | 140 simulated seconds; REST/WebSocket agree |
| B Unequal | Unequal network; north arrival rate exceeds east | 140s, actual estimator counts |
| C Spillback | Spillback network; receiving occupancy reaches80%+, north receiving supply becomes zero | 80s, pressure/MPC receiving diagnostics |
| D Pedestrians | Pedestrian network; walkers, protected walk phases and15s clearance requirement visible | 180s, compatible permissions and pedestrian observations |
| E Emergency | Same protected network, injected east emergency priority3; preemption observed and request completes | 180s; preserves pedestrian clearance |
| F Coordination | Corridor network; A0/B0 telemetry and independent accepted supervisor actions | 180s; MAPPO availability shown without activation |
| G Failure | Corridor with forced zero MPC budget; Max-Pressure fallback and missing-camera fallback visible | 80s; real fallback diagnostics |
| H Camera | Start recorded-video perception; camera_fusion counts/tracks appear; Stop returns unavailable fallback | Actual YOLO/ByteTrack input, not field accuracy |

The dashboard can show a case manually by selecting its network/controller, starting, pausing and stepping. The automated runner advances quickly; use the manual flow when explaining each signal transition. Native fixed-time is a comparison mode; Hybrid runs constrained MPC with supervised Max-Pressure fallback. Learned recommendations remain offline research only.

Phase5 actual demonstration results are preserved in `.checkpoints/phase5/demo-results.json`; readiness/test outcomes are in [FINAL_DEMO_READINESS_REPORT.md](FINAL_DEMO_READINESS_REPORT.md). Full installation and older validated scenario commands remain in [RUN_INSTRUCTIONS.md](RUN_INSTRUCTIONS.md). This is a research demonstration, not a road-deployment safety assurance.
