# SYNCHROFLOW AI — start here to resume

Prepared 23 October 2026 for an indefinite pause. This is the current handoff for a human or LLM. Older phase reports are historical evidence and can contain superseded setup/state descriptions. Read this document first, then the specific report/code needed for a task. Do not rerun completed training merely to reconstruct context.

## 1. Objective and current position

SYNCHROFLOW is a scientifically trustworthy local traffic-control research platform, not a certified road controller. The latest work refined the actual SUMO dashboard and remaining pages without changing safety-critical backend logic. The reference city image was visual inspiration; no vehicles, weather, percentages or causal explanations were invented to match it.

| Item | Preserved state |
|---|---|
| Current development branch | `phase6b-ux-refinement` |
| Verified UI code | `phase6b-verified-ux` / `8216ca8f61f6ea1b3d8385c5471a3b946fd19226` |
| Before refinement | `phase6b-before-refinement` / `570b49f` |
| Phase 6 | `phase6-verified-live-digital-twin` / `570b49f` |
| Frontend wiring repair | `frontend-functionality-repaired` / `8116bb8` |
| Phase 5 research | `phase5-evaluated-prototype` / `975ce235217a260590bd4ca261ec3871289880e2` |
| This handoff | Documentation commit after the verified UI; obtain exact hash with `git log -1` |
| GitHub | [PranavSrikar/syncroflow2AI](https://github.com/PranavSrikar/syncroflow2AI); default `phase6b-ux-refinement`; local branches/tags pushed, older `main` preserved |

Original workspace: `C:\Users\prana\Documents\TrafficRegulationResearch\syncroflow2AI-main`. Recovery copies: sibling `synchroflow-known-good-recovery`. Paths can change after restoration; rebuild camera absolute paths. Do not assume services survive closing the editor, restarting Windows or a long pause.

## 2. Safety and scientific invariants

1. Keep operational MAPPO disabled and labelled **Experimental — Not Qualified**. Hybrid is supervised MPC with Max-Pressure fallback, not a qualified RL deployment. Keep `SYNCHROFLOW_MAPPO_CHECKPOINT` and `SYNCHROFLOW_MAPPO_VALIDATION` unset. Inspect actual backend policy configuration before any experiment.
2. Preserve independent timing/clearance, pedestrian, emergency, receiving-capacity/spillback and maximum-red fairness supervision. Do not bypass a hold, force a phase, or weaken tests to make a demonstration pass.
3. The backend is authoritative for real state. Synthetic browser output, example history, forecasts and offline results must remain clearly distinguished from measured SUMO/camera observations.
4. Unknown policy strings do not establish causality; current observed inputs are not necessarily the inputs of the last decision. Display actual trace times/reasons when available.
5. A SUMO next-switch countdown is a scheduled value subject to adaptive change. Approach counts and viewport counts have different spatial scopes. Current waiting time is not completed-trip delay.
6. Preserve frozen research seeds, original checkpoints/hashes and failed qualification results. New studies need separate outputs, predeclared training/selection/test partitions and independent qualification.

## 3. Architecture and code map

```text
React / shared live provider <--- HTTP + WebSocket ---> FastAPI
         |                                            |
 Actual-coordinate SVG twin                         SUMO runtime / TraCI
 Observed analytics                                 estimator + forecasts
 Controller trace / safety                          Max-Pressure + constrained MPC
 Camera / forecast forms                            independent safety supervisor
                                                      |
 Separate browser engine / Three.js                 SUMO simulation
 (explicit synthetic demonstration)                 optional camera observations
```

| Location | Responsibility |
|---|---|
| `src/App.tsx` | Live/synthetic routing and workspace source separation |
| `src/services/liveTraffic.tsx` | Shared authoritative snapshots, WebSocket/freshness, bounded history |
| `src/services/trafficPresentation.ts` | Policy summaries and actual controlled-link approach permissions |
| `src/components/live/` | Dashboard, actual-coordinate map, analytics, controller intelligence, health, safety and offline evidence |
| `src/components/views/SumoLiveView.tsx` | Scoped live pages and acknowledged lifecycle/injection controls |
| `src/components/views/TrafficInputsPanel.tsx` | Camera, history, weather and forecast configuration/monitoring |
| `src/components/views/OverviewCommandCenter.tsx` | Separate synthetic 3D workspace; existing synthetic engine remains |
| `src/index.css`, `src/refinement.css` | Base design system and incremental Phase 6B responsive refinements |
| `backend/app/services/sumo_adapter.py`, `sumo_runtime.py` | TraCI geometry/measurements, runtime and controller integration |
| `backend/app/services/` | Controllers, independent supervision, forecasts, perception, RL infrastructure; inspect actual files before editing |
| `backend/sumo_scenarios/` | Versioned supplied SUMO fixtures |
| `scripts/` | Launcher, demos, production smoke, research drivers/reporting and source checkpoints |
| `tests/`, `backend/tests/` | Frontend units/browser and backend regression/integration |
| `research/phase4*`, `research/phase5` | Published offline results and charts, not current live performance |

Main endpoints are under `/api/v1`: `/sumo/status`, `/sumo/telemetry`, `/sumo/ws`; POST `/sumo/start`, `/pause`, `/step`, `/stop`; `/sumo/emergencies/inject` and `/status`; `/perception/start`, `/stop`, `/status`; `/traffic/source`; `/forecast`, `/forecast/history`, `/forecast/config`, `/forecast/enabled`; `/health`. Consult FastAPI `/docs` and route implementations for exact current contracts. Do not infer a new endpoint from a desired UI control.

## 4. Implemented user workflows

- Monitor real traffic: four KPIs, actual lane/vehicle/pedestrian/signal geometry, junction focus, zoom and Road IDs, current phase and scheduled switch, observed queues and safety events.
- Understand decisions: actual policy/pressure/service-age and supervisor timeline; separate architecture illustration and implemented finite-candidate MPC model assumptions. No continuous-QP claim for the live solver.
- Analyze: bounded observed queue/wait/throughput/rate trends and approach comparisons. Raw diagnostics remain expandable.
- Predict/perceive: history upload, manual/external weather configuration, forecast horizon/source/uncertainty/fallback, camera source/start/stop/coverage/freshness/confidence and recorded-video provenance. No frame-stream API is available.
- Safety: protected pedestrian fixture and adaptive-run emergency injection, including A0/B0 corridor selection, with authoritative clearance/recovery events. No manual live pedestrian-call endpoint exists.
- Research: five supplied SUMO fixtures; retained 25 browser scenarios; separate seeded browser benchmark/export; original offline research reports. Educational equations and V2I examples remain available with source limitations.
- All 14 navigation destinations remain available in both workspaces. Live reset/speed/manual call/offset editing and physical hardware control remain unsupported and explained.

## 5. Fresh setup and startup

Verified versions: Windows/PowerShell, Python **3.11.9**, Node **24.21.0**, SUMO **1.28.0**. Frontend uses `package-lock.json` via npm, backend requirements pin ranges rather than a complete environment lock. Archived environment freezes are the best exact historical dependency record. Future package compatibility must be checked rather than assumed.

```powershell
# In the restored/cloned repository root:
py -3.11 -m venv backend/.venv
& backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
npm.cmd ci
sumo --version
& backend/.venv/Scripts/python.exe scripts/run_dev.py
```

Install SUMO separately and add its bin directory to PATH. The core app needs no Gemini/API key or camera/torch setup. Do not overwrite an existing venv unnecessarily. Use one backend worker. Set `$env:DEBUG='false'` for research commands. The launcher sets frontend backend URL and uses 3001/8001; `npm run dev` alone defaults to port 3000 and is not the coordinated startup command.

Open http://127.0.0.1:3001; health http://127.0.0.1:8001/api/v1/health; API docs http://127.0.0.1:8001/docs. Existing occupied ports are preserved. To run independently:

```powershell
& backend/.venv/Scripts/python.exe scripts/run_dev.py --backend-port 8027 --frontend-port 3027
```

Choose a network, controller and seed; Start. Pause, then Step or Start to resume. Stop before changing network/controller. Stop then Start creates a fresh session. Ctrl+C in the launcher cleans up owned SUMO/camera/backend/frontend processes. History/weather/configuration can be process-local; reload inputs after restarting instead of assuming persistence. This is an unauthenticated local research API, not a public hosting configuration.

## 6. Optional camera and research restoration

Git excludes `.checkpoints`, dependencies, credentials and generated output. A clone alone runs the core SUMO workflow but cannot reproduce every camera/research result. `ARTIFACT_MANIFEST.json` records archive names/hashes and whether they are included in Git (they are not). Preserve or upload these archives separately alongside the repository. Same-machine copies do not protect against disk loss.

The final Phase 5 artifact archive contains raw research/checkpoint evidence, environment freezes, recorded road video and YOLO weights. Never enable its unqualified RL weights. Verify its SHA-256 and its embedded manifest before extraction into a new workspace. Archive source/checkpoint paths may be machine-specific. Preserve original archived reports and weight bytes; use separate writable output directories for new studies.

Optional packages:

```powershell
& backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-perception.txt
# Select a compatible CPU/GPU torch/torchvision pair for the restored environment.
# Historical exact package versions are in archived environment-freeze files.
# For training/plotting, also install backend/requirements-research.txt.
```

Perception dependencies do not themselves guarantee a compatible torch/torchvision installation. Restore the assets under `.checkpoints/perception`, then regenerate a BOM-free camera array with absolute paths:

```powershell
$camera = Get-Content backend/examples/camera-road.example.json -Raw | ConvertFrom-Json
$camera.source = (Resolve-Path .checkpoints/perception/road.mp4).Path
$camera.weights = (Resolve-Path .checkpoints/perception/yolo11n.pt).Path
$json = ConvertTo-Json -InputObject @($camera) -Depth 12
[IO.File]::WriteAllText((Join-Path (Get-Location) '.checkpoints/perception/cameras-api.json'), $json, (New-Object Text.UTF8Encoding($false)))
$env:SYNCHROFLOW_CAMERA_CONFIG = (Resolve-Path .checkpoints/perception/cameras-api.json).Path
& backend/.venv/Scripts/python.exe scripts/run_dev.py
```

Set configuration before starting the backend. In Camera & Sensor Monitoring, Start cameras; distinguish recorded replay time from wall-clock age and live hardware. The demo covers the configured approach only and has no field metric calibration.

## 7. Verification and recorded evidence

At `phase6b-verified-ux`: frontend units/repair checks, TypeScript, production build passed; **14 browser tests** passed against 3001/8001; **112 backend tests**, no skips/failures; **all eight external A–H demos** passed including actual recorded-video inference H and forced MPC fallback G. Built-asset browser and owned startup/shutdown smoke passed. Screenshots were inspected at 1366×768 and 1920×1080, with exactly four primary KPIs, no default dashboard scrolling or overlapping controls, and visible safety events.

```powershell
npm.cmd test
npm.cmd run lint
npm.cmd run build
# Install Edge or set SYNCHROFLOW_BROWSER_CHANNEL to an installed supported channel.
npm.cmd run test:e2e
& backend/.venv/Scripts/python.exe -m pytest backend/tests
& backend/.venv/Scripts/python.exe scripts/run_dev.py --backend-port 8027 --frontend-port 3027 --smoke-test
```

Browser tests normally launch isolated 3017/8017. Full camera coverage requires the optional assets/dependencies/config; without them the recorded-video browser case skips. Backend optional-dependency cases may likewise differ on a core-only environment. The final external-server browser run used:

```powershell
$env:SYNCHROFLOW_EXTERNAL_SERVERS = '1'
$env:SYNCHROFLOW_TEST_URL = 'http://127.0.0.1:3001'
$env:SYNCHROFLOW_TEST_API = 'http://127.0.0.1:8001/api/v1'
npm.cmd run test:e2e
```

On a stopped disposable configured backend, run all demonstrations:

```powershell
New-Item -ItemType Directory -Force .checkpoints/resume | Out-Null
& backend/.venv/Scripts/python.exe scripts/demo_release.py --base-url http://127.0.0.1:8001/api/v1 --output .checkpoints/resume/demos.json --with-example-forecast
```

The forecast flag explicitly opts into labelled example history. This is not evidence of operational forecast calibration. For built assets: `npm.cmd run preview -- --host 127.0.0.1 --port 3037` in another terminal, then `node scripts/smoke_frontend.mjs` on a stopped backend. The script currently writes evidence to `.checkpoints/phase6`; preserve historical evidence before repeating. Stop preview afterwards.

Successful-MPC browser rendering cases use an explicit 1000ms test budget; production remains 50ms, and fallback is independently tested. A real expanded-map feedback loop was fixed with stable diagnostic-mode sizing; the corridor test now waits for acknowledged Pause before API steps. Do not replace those assertions with forced clicks or arbitrary waits.

Historical evidence is in the Phase 6B artifact archive and `RESPONSIVE_TEST_RESULTS.md`. Single local production navigation was 132.2ms; build 723ms; JS about 1.09MB before gzip with a large-chunk advisory. These are single-run observations, not general latency/FPS promises.

## 8. Completed research and next work

Phase 5 completed bounded ablations/training/selection/test/challenge trials. It did **not** qualify MAPPO; candidate delay regressed against MPC. Read `PHASE5_EXPERIMENT_RESULTS.md`, `MAPPO_DIAGNOSTIC_REPORT.md`, `UPDATED_POLICY_QUALIFICATION_REPORT.md` and `research/phase5/README.md` before proposing another experiment. Preserve existing failed results and disjoint test partitions. Rebuilding reports is different from retraining; raw inputs are in the artifact archive.

Remaining work, in priority order:

1. Verify a fresh clone plus separately restored artifacts and environment using the commands above. Confirm GitHub remote/branch/tags and archive hashes actually exist off this machine.
2. Address measured frontend bundle size and high-count SVG/WebSocket performance with profiling. Preserve bounded histories and real-coordinate fidelity; do not claim an arbitrary FPS.
3. Broaden accessibility, keyboard/screen-reader and cross-browser/tablet checks. Existing desktop layout checks do not constitute full certification.
4. If needed, design safe camera frame-preview integration; current backend has observation telemetry but no annotated frame-stream endpoint. Preserve recorded/live provenance and missing coverage.
5. Independently validate external weather fetch success, forecast/calibration accuracy and real hardware only with suitable data/equipment. Current manual-weather/fallback tests do not establish those claims.
6. Consider reset/speed/manual pedestrian calls/live benchmark jobs only after defining safe backend semantics. Do not add dead or misleading controls.
7. New MAPPO research requires a separately scoped protocol, train/selection/fresh-test splits, controlled ablations and safety qualification. Never activate a candidate merely because training or inference runs.

No new feature implementation is requested by this handoff. Resume with audit and a fresh checkpoint, not a risky rewrite.

## 9. Git, artifacts and recovery

Publication completed on 23 October 2026 to the repository above. The [recovery release](https://github.com/PranavSrikar/syncroflow2AI/releases/tag/project-pause-handoff) contains source/history archives, Phase 5 research/perception artifacts and Phase 6B test/screenshot evidence. Download **GITHUB_RECOVERY.json** first for the latest documentation source, Git bundle and archive hashes. Earlier PAUSE_RECOVERY.json describes the initial `19b7a18` handoff and deliberately remains unchanged. Final documentation checkpoint: `project-pause-archived`.

The repository is public. Remote refs, asset sizes and GitHub SHA-256 digests were checked; a fresh clone selected the current branch automatically. These preservation checks are not a new application regression run or research-policy qualification. At pause, SUMO/cameras were stopped via their APIs and owned servers on 3001/8001 were shut down. Start the launcher when returning. Dependencies and credentials remain excluded.

```powershell
git status -sb
git remote -v
git log -1 --oneline
git show-ref --tags
```

If Git is absent from an old shell's PATH, use `& 'C:/Program Files/Git/cmd/git.exe' ...` or restart the terminal. Local history exists; do not initialize a replacement repository. `master` is an older Phase 4 branch: use `phase6b-ux-refinement` or the explicit verified tag when restoring current work.

To recover source/history from a bundle, clone it into a **new** folder, then check out the current branch. Verify source/artifact ZIP hashes before extraction. Do not restore over the current workspace. `.checkpoints/PHASE5_RECOVERY.json`, `PHASE6_RECOVERY.json`, `PHASE6B_RECOVERY.json` and the pause recovery pointer record local archives/copies. `scripts/checkpoint.py` creates a source ZIP with per-file hashes; it excludes binaries under `.checkpoints` and is not a full artifact or remote backup.

For GitHub, use the agreed remote, push current branch plus preserved branches/tags without force, and verify remote refs. Upload verified artifacts as separate release assets (or an explicitly chosen private archive service); do not check credentials, venv, node_modules or build caches into Git. Uploading source alone is not the entire reproducibility package. Inspect repository visibility and video/model redistribution terms before public artifact publication. A private repository is recommended for the initial archival push.

## 10. Prompt for the next coding agent

> Read PROJECT_HANDOFF.md first. Inspect Git status/remotes and the current branch before editing. Restore optional artifacts only after hash verification. Audit actual runtime and API/WebSocket behavior before making changes. Preserve Phase 5/6/6B tags and independent safety logic. Keep MAPPO disabled/unqualified. Never present browser-synthetic data, example history or inferred causal explanations as measured live traffic. Report what you actually tested, missing dependencies/assets and remaining limitations. Create a separate checkpoint before new work; use fresh output directories and research partitions. Ask for the user's next objective rather than treating the backlog as authorization to rewrite or retrain.
