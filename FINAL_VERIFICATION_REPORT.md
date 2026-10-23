# Final verification report — corrected Phase 4 study

Verified continuation: 2026-10-23. The bounded `phase4-demand-corrected` experiment was already complete at checkpoint `a2ae3d06fad46cd395c7ae216197637810df2a8e`. This continuation verified its integrity and consolidated the completion assessment; it did not repeat completed training or benchmarks. **No policy qualified. Operational MAPPO remains disabled; supervised Max-Pressure and constrained MPC remain available.**

## Exact experiment status

| Milestone | Recorded completion |
|---|---|
| Corrected training | Seeds 21/31/41, each 16 updates ×64 joint decisions =1024 decisions; all 48 checkpoints audited |
| Reproducibility | Seed21 first64 decisions replayed with bit-identical parameters, maximum difference0 |
| Frozen model selection | 12 trials, selection seeds2801–2803, demand1.0,300s; model41 selected before final testing |
| Held-out benchmarking | 30 trials: five modes ×two loads ×three seeds2901–2903,300s |
| Separate candidate safety trials | Seeds2951–2953,240s each; recorded numerical/safety checks passed |
| Qualification | Failed performance/fairness screens and incomplete candidate pedestrian/emergency coverage; not eligible |
| Final regression | Completed on corrected implementation; exact results below |

Selected checkpoint: `.checkpoints/phase4-demand-corrected/train-41/update-0016.pt`. SHA-256: `a013e764890ebb8d9367f56909a93fdedd29c61a5efeb1057babfd58df66ea47`. Current architecture fingerprint: `282bde4934a3e5eaa61e7758f956aad190b28dfd7a16b12cb486e0bfdf3f2492`.

## Does MAPPO improve over MPC?

There is **no qualified MAPPO policy and no established consistent improvement over MPC**. The frozen, unqualified candidate produced these measured completed-trip SUMO timeLoss means across three held-out seeds:

| Demand scale | MPC delay seconds | Candidate delay seconds | Candidate change |
|---|---:|---:|---|
| 0.75 | 20.299584 | 20.459940 | 0.789948% worse |
| 1.75 | 36.080208 | 35.611565 | 1.298892% better |

Neither stratum met the predeclared2% improvement requirement. Two lower-demand trials exceeded5% paired delay regression. Maximum service age increased in all six paired trials. The worst candidate age57s remained below the supervisor120s bound: this is a comparative fairness-screen failure, not a recorded safety-bound violation. Recorded candidate benchmark/safety trials had zero safety faults and zero supervisor rejections. Candidate pedestrian/emergency coverage is missing. The actual runtime gate was checked again and refused the checkpoint.

Three seeds,300s cold-start horizons and completed-trip censoring limit inference. No significance or controller superiority is claimed. No untrained/static-hint ablation establishes that learning caused the small higher-demand benefit. See [benchmark report](CONTROLLER_BENCHMARK_REPORT.md), [qualification report](POLICY_QUALIFICATION_REPORT.md) and [machine-readable results](research/phase4/benchmark-summary.json) for variability, throughput, queues, waiting, unfinished trips, insertion backlog and latency.

## Feature completion assessment

| Feature | Verified scope | Remaining limitation |
|---|---|---|
| React dashboard, FastAPI, WebSocket, SUMO/TraCI | Real browser and external HTTP/WebSocket/SUMO scenarios passed; both junctions stream telemetry | Research demonstration, not production availability assurance |
| State estimation, Max-Pressure, constrained MPC | Executable adaptive pipeline; movement pressure, receiving capacity, forecast inputs and timeout fallback exercised | Models/objective not field calibrated; no optimization-superiority claim |
| Independent signal supervisor | Adaptive timing writes checked; legal phase ring, clearance, timing, fairness and fault handling regression-tested | Supplied scenarios do not constitute formal safety certification; native fixed-time is a separate SUMO baseline |
| Pedestrian protection and emergency priority | Supplied baseline demonstrations and safety regressions passed; emergency case response70s | Learned candidate not validated with combined pedestrian/emergency demand |
| Multi-junction MAPPO | Shared actor/central critic, PPO/GAE, joint observations, checkpoints, offline recommendations→MPC→supervisor exercised | Limited training; failed qualification; no positive qualified-policy operational/browser test |
| Camera perception | Actual recorded-video detection/tracking and fallback demonstration passed | No field/live-camera accuracy guarantee or camera-controlled benchmark |
| Historical/weather forecasts | Integrated fallback and forecast-to-MPC demonstration; earlier live weather retrieval recorded | No genuine held-out historical forecast accuracy or adverse-weather robustness study |
| Spillback and failure fallback | Blocked-exit and sensor/controller-failure demos passed | Primary benchmark recorded zero spillback edge-seconds; learned spillback robustness unestablished |
| Startup and recovery | Readiness/cleanup smoke passed; source/artifacts/Git bundle verified | Separate recovery copies are on the same device; no remote/off-device backup |

## Exact regression evidence

These are retained results from the corrected release, not newly rerun test counts. Before documentation changes, every archived source file and research artifact matched the working tree byte-for-byte; repeating the full suite was unnecessary.

| Check | Actual result |
|---|---|
| Full backend suite | 108 passed,0 failures,0 errors,0 skipped;245.780s; one existing Starlette/httpx warning |
| Real Edge integration | 4 passed,32.3s |
| Frontend production build | Passed |
| TypeScript | Passed |
| Frontend unit/demo groups | 8/8 passed |
| Python dependency check | Passed |
| Startup readiness/cleanup smoke | Passed on backend8020/frontend3020 |
| External scenarios A–H | 8/8 passed: normal,unequal demand,spillback,pedestrian,emergency,multi-junction,fallback,recorded camera |

Raw evidence: [backend JUnit XML](.checkpoints/phase4-demand-corrected/backend-final.xml), [verification record](.checkpoints/phase4-demand-corrected/verification.json), [external demos](.checkpoints/phase4-demand-corrected/full-demo-results.json), [continuation audit](.checkpoints/phase4-demand-corrected/continuation-verification.json). The backend XML records the run timestamp as2026-10-23T01:38:17+05:30. Build,TypeScript and frontend group checks predate the final backend-only fixes; their source remained unchanged.

## Preservation and current runtime

The continuation rechecked both archive copies against SHA-256, ZIP CRCs and all manifest entries. All219 source entries and458 artifact entries matched the working files; selected weights and the current qualification fingerprint matched. No experiment weights, route files or controller code were changed. The separate earlier studies remain `.checkpoints/phase4` / `research/phase4-pre-fix` and `.checkpoints/phase4-final` / `research/phase4-saturated`; neither contributes weights or trial rows to the corrected primary study. All previous recovery archives remain preserved.

At2026-10-23T01:55:33Z, frontend3001 and backend8001 returned HTTP200. SUMO was stopped/disconnected, camera processing inactive and MAPPO unloaded/disabled. The API's `cvxpyMpcReady=false` flag while stopped is not evidence that an adaptive simulation is currently running; this report relies on the recorded real controller trials. The stopped API still exposes an explicitly labeled Stage2 smoke-training summary; corrected research status is in these Phase4 reports and artifacts, not that historical summary.

Git is installed at `C:/Program Files/Git/cmd/git.exe`. The exact Stage3 archive is preserved by `stage3-verified-demo`; the completed experiment is tagged `phase4-evaluated-research`. The new documentation handoff receives a local commit and verified recovery archive via [recovery pointer](.checkpoints/PHASE4_RECOVERY.json). No push or remote publication occurs. See [recovery guide](RECOVERY_GUIDE.md).

## Startup and demonstration

From the project folder in PowerShell:

```powershell
.\backend\.venv\Scripts\python.exe scripts/run_dev.py
```

Open http://127.0.0.1:3001 and http://127.0.0.1:8001/docs. Startup defaults to stopped fixed-time; choose Hybrid and a network, then Start. Keep `SYNCHROFLOW_MAPPO_CHECKPOINT` and `SYNCHROFLOW_MAPPO_VALIDATION` unset. Hybrid uses supervised MPC with Max-Pressure fallback and no learned hints. If the existing launcher already occupies these ports, use that running instance. Ctrl+C cleans up processes owned by that launcher. Complete scenario procedures, expected observations and dependency instructions are in [RUN_INSTRUCTIONS.md](RUN_INSTRUCTIONS.md).

The prototype is a runnable, experimentally evaluated research demonstration. More training, new held-out data, candidate emergency/pedestrian validation, longer/more diverse trials, field-calibrated perception/forecasts and off-device recovery remain necessary. See [training report](MAPPO_TRAINING_REPORT.md) and [research next steps](RESEARCH_NEXT_STEPS.md). No real-road certification or fully trained useful MAPPO controller is delivered.
