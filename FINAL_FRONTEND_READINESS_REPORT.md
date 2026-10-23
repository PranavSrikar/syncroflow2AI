# Phase 6 frontend readiness

SYNCHROFLOW now has a backend-connected command dashboard, a real SUMO digital twin, observed analytics, controller explanations, provenance-aware camera/forecast monitoring, safety displays and responsive navigation. The synthetic Three.js demonstration, 25 browser scenarios, benchmark/export tools, model explorer, protocol inspector and legacy provider diagnostics remain available in their labelled workspace.

The verified scope is a local research interface for the supplied SUMO fixtures. It is not a field-deployed traffic controller, certified road-safety system, calibrated camera/forecast product or qualified MAPPO policy. **Hybrid remains supervised constrained MPC with Max-Pressure fallback. Operational MAPPO remains disabled.**

## Start the verified interface

PowerShell, repository root:

```powershell
Set-Location C:\Users\prana\Documents\TrafficRegulationResearch\syncroflow2AI-main
# Optional: real recorded-video observations using the existing local assets.
$env:SYNCHROFLOW_CAMERA_CONFIG = (Resolve-Path .checkpoints/perception/cameras-api.json).Path
& backend/.venv/Scripts/python.exe scripts/run_dev.py
```

Open **http://127.0.0.1:3001**. Backend is **http://127.0.0.1:8001/api/v1**. A running verified development session is left available; the simulation is stopped after testing. Do not launch a duplicate on occupied ports. The launcher preserves unrelated services; use `--backend-port`/`--frontend-port` for an isolated session. Ctrl+C cleans up the launcher's owned SUMO/camera/server processes.

If dependencies are absent, use `npm.cmd ci` and the project Python environment/`backend/requirements.txt`; SUMO must be on PATH. Camera weights/video are optional and excluded from source recovery ZIPs; existing Phase 5 artifact archives contain them. The camera JSON must point to valid local paths. Do not expose this unauthenticated local research API publicly.

## First-use workflow

1. In Overview choose a network, controller and seed. Desktop controls sit at the bottom; tablet/phone controls stack above the map. Start creates a run; Start on a paused session resumes it.
2. Inspect actual vehicles/signals in the map and the source-labelled KPI cards. Use Entire network or a junction focus for corridor observations. A focused map omits vehicles outside its bounds; aggregate counts describe the selected monitored approaches.
3. Read Why this signal? and Controller Intelligence. Expand reported policy/pressure details if needed. A countdown is the last SUMO scheduled switch, not a guarantee that an adaptive controller will retain it.
4. Use Traffic Analytics for observed trends/rates, Traffic Predictions for history/weather/uncertainty, and Camera & Sensor Monitoring for actual recorded-video observations.
5. Choose the pedestrian fixture for protected crossings. Emergency injection is available only with an active supervised adaptive run. No UI can bypass mandatory service, clearance or safety gates.
6. Pause/Step, Stop, and Start again. Stop ends the current SUMO connection; a new Start creates a fresh run. Live reset and speed adjustment are unavailable and explicitly explained.
7. Switch to synthetic demonstration for the separate 3D browser model and offline-style browser experiments. These metrics never stand in for live SUMO.

## Verification

- 11 real-browser tests passed against 3001/8001, including all destinations in both modes, lifecycle/restart, API-to-DOM KPI/position/signal agreement, responsive layouts, failures and disconnection.
- 112 backend tests passed with real SUMO and recorded-video inference; no skips/failures/errors.
- All eight external demonstration scenarios passed.
- Frontend original and repair unit suites, TypeScript and production build passed.
- Built-asset browser smoke and owned-server startup/shutdown smoke passed.

Full commands/evidence, single-run browser timings, screenshots and testing limitations are in [UI_UX_TEST_RESULTS.md](UI_UX_TEST_RESULTS.md). There is no arbitrary frame-rate or comparative improvement claim.

## Changed files

| Files | Purpose |
|---|---|
| `src/index.css` | Design tokens, shared visual language, responsive rail/dock/grid, focus indicators, loading skeletons and reduced-motion behavior |
| `src/components/live/primitives.tsx` | Reusable badges, panels and metric cards |
| `src/components/live/LiveStatusHeader.tsx` | Source, connectivity, freshness and simulation status |
| `src/components/live/LiveNetworkMap.tsx` | Actual lane/junction geometry, positions, classes, signals, pedestrians, direction arrows and viewport cap |
| `src/components/live/LiveCommandCenter.tsx` | KPI aggregation, junction focus, explanation/pressure/fallback/fairness and approach conditions |
| `src/components/live/LiveAnalytics.tsx` | Bounded observed trends, gaps, legends/tooltips, windows and rate comparisons |
| `src/components/live/LiveSafety.tsx` | Emergency state/recovery events and protected pedestrian cards |
| `src/App.tsx`, `src/components/navigation/Sidebar.tsx` | Remove duplicated shortcut navigation; task labels and Controller Intelligence routing; preserve synthetic mode; flex containment |
| `src/services/liveTraffic.tsx` | Bounded queue/wait/throughput/rate history and receipt freshness |
| `src/components/views/SumoLiveView.tsx` | Unified workflow, operation dock, errors outside collapsed diagnostics, backend acknowledgement, scoped panels and extended telemetry types |
| `src/components/views/HybridTelemetryPanel.tsx` | Shared extended telemetry typing |
| `src/components/views/TrafficInputsPanel.tsx` | Camera source-kind/age and prediction horizon/source/time/uncertainty visualization |
| `src/components/views/LiveUtilities.tsx` | Consistent live health/export presentation |
| `backend/app/services/sumo_adapter.py` | Cached read-only network geometry |
| `backend/app/services/sumo_runtime.py` | Read-only visibility of existing fairness service age |
| `backend/app/services/camera_runtime.py` | Recorded/live provenance and observation age |
| `index.html` | Remove unused external font requests; system typography works offline |
| `backend/tests/integration/test_digital_twin.py` | Actual TraCI shape/position/class/service-age checks |
| `tests/browser/phase6.spec.ts` | API/DOM fidelity, responsive/keyboard checks, screenshots and measured evidence |
| `tests/browser/sumo.spec.ts`, `tests/browser/frontend-audit.spec.ts` | Preserve prior assertions through new routes/disclosures; recorded-source/horizon checks; deterministic MPC-success test setup |
| `scripts/smoke_frontend.mjs` | Actual browser test of built assets with stopped-backend guard and cleanup |
| `scripts/checkpoint.py` | Include the new `.mjs` smoke script in verified source archives |
| Six Phase 6 Markdown deliverables | Audit, design system, digital twin, contracts, tests and readiness |

No controller implementation, supervisor safety logic, SUMO scenario, research result, training infrastructure or policy weights were modified.

## Reproduce checks

```powershell
npm.cmd test
npm.cmd run lint
npm.cmd run build
$env:DEBUG = 'false'
$env:SYNCHROFLOW_TEST_VIDEO = (Resolve-Path .checkpoints/perception/road-vehicles.mp4).Path
$env:SYNCHROFLOW_TEST_WEIGHTS = (Resolve-Path .checkpoints/perception/yolo11n.pt).Path
Push-Location backend
& .venv/Scripts/python.exe -m pytest tests
Pop-Location
# Default browser config starts isolated 3017/8017 servers.
$env:SYNCHROFLOW_CAMERA_CONFIG = (Resolve-Path .checkpoints/perception/cameras-api.json).Path
npm.cmd run test:e2e
```

To test an already running 3001/8001 session, set `SYNCHROFLOW_EXTERNAL_SERVERS=1`, `SYNCHROFLOW_TEST_URL=http://127.0.0.1:3001`, `SYNCHROFLOW_TEST_API=http://127.0.0.1:8001/api/v1` before the browser command. These tests stop/restart simulation; use a disposable session.

On a stopped backend with camera configuration, run:

```powershell
& backend/.venv/Scripts/python.exe scripts/demo_release.py --base-url http://127.0.0.1:8001/api/v1 --output .checkpoints/phase6/new-demo-results.json --with-example-forecast
```

To reproduce the production smoke, build then run `npm.cmd run preview -- --host 127.0.0.1 --port 3037` in another terminal, and `node scripts/smoke_frontend.mjs`. It preserves an already active SUMO session by refusing to start; when allowed it controls a disposable run and cleans it up. Shut down preview afterwards.

## Boundaries and recovery

No physical roadside hardware, annotated camera stream, manual live pedestrian call, live benchmark execution, live reset/speed API, enforced RBAC, calibrated forecast/detector accuracy or general high-load performance is claimed. Open-Meteo successful external fetching, comprehensive accessibility certification and exhaustive mobile usability remain unverified. These boundaries are disclosed in the UI/reports.

Development branch: `phase6-live-digital-twin`. Separate completion tag: `phase6-verified-live-digital-twin`. The original Phase 5 tag and `frontend-functionality-repaired` remain intact. Recovery pointer: `.checkpoints/PHASE6_RECOVERY.json`, with verified source ZIP, full Git bundle, evidence ZIP, SHA-256 hashes and separate same-machine copies. Restore into a new empty folder and verify manifests; combine with preserved Phase 5 artifact archives for weights/video/research assets. These are local recovery copies, not off-device backups.
