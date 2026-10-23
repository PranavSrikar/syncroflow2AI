# Phase 6B readiness report

The local research interface now has a compact SUMO dashboard, dominant actual-coordinate twin, four KPIs, current signal/decision/safety insight and in-flow controls. Both target desktop sizes pass layout checks. Focused pages retain scientific detail in tabs/disclosures. Live, recorded, forecast, offline research and synthetic sources remain explicit. Hybrid is supervised MPC with Max-Pressure fallback; operational MAPPO stays disabled.

## Verification

- 14 real-browser tests pass against 3001/8001: telemetry agreement, lifecycle/restart, corridor, camera/forecast, navigation, errors and disconnection.
- 112 backend tests pass without skips; all eight external SUMO demonstrations pass.
- Frontend unit suites, TypeScript and production build pass.
- Built-asset browser and owned startup/shutdown smoke tests pass.
- Actual before/after screenshots at 1366×768 and 1920×1080 inspected. See RESPONSIVE_TEST_RESULTS.md for evidence and measured limits.

## Reproduce

PowerShell, repository root, existing dependencies and SUMO on PATH:

```powershell
Set-Location C:\Users\prana\Documents\TrafficRegulationResearch\syncroflow2AI-main
# Optional recorded-video configuration; requires existing valid video/weights paths.
$env:SYNCHROFLOW_CAMERA_CONFIG = (Resolve-Path .checkpoints/perception/cameras-api.json).Path
& backend/.venv/Scripts/python.exe scripts/run_dev.py
```

Open http://127.0.0.1:3001; API is http://127.0.0.1:8001/api/v1. The existing development session is left available with SUMO stopped; do not launch duplicate services on occupied ports. Without optional camera assets, SUMO works and camera coverage is unavailable. Install missing frontend dependencies with `npm.cmd ci`, Python dependencies from `backend/requirements.txt` into the project venv. Prior Phase 5 artifacts retain excluded video/weights.

Select network/controller/seed and Start. Pause then Step, or Start to resume. Stop before changing network/controller. Stop then Start creates a new run. Inspect Controller Intelligence or detailed telemetry. Switch explicitly to the synthetic workspace for its 3D demonstration and browser benchmark. Ctrl+C on the owned launcher cleans up its simulation, camera and server processes.

```powershell
npm.cmd test
npm.cmd run lint
npm.cmd run build
npm.cmd run test:e2e
& backend/.venv/Scripts/python.exe -m pytest backend/tests
& backend/.venv/Scripts/python.exe scripts/demo_release.py --base-url http://127.0.0.1:8001/api/v1 --output .checkpoints/phase6b/demo-repeat.json --with-example-forecast
```

Browser tests default to isolated 3017/8017. Configure SYNCHROFLOW_CAMERA_CONFIG for the video case. Final run used SYNCHROFLOW_EXTERNAL_SERVERS=1, SYNCHROFLOW_TEST_URL=http://127.0.0.1:3001 and SYNCHROFLOW_TEST_API=http://127.0.0.1:8001/api/v1. Tests control disposable simulations. Build preview on 3037 plus `node scripts/smoke_frontend.mjs` repeats production smoke on a stopped backend.

## Remaining limitations

No physical camera/V2I equipment, frame-preview API, live reset/speed/manual pedestrian-call API, live benchmark-job API or qualified MAPPO policy is present. External Open-Meteo success was not independently retested; manual weather and forecast fallback are covered. Calibration, general controller superiority, full accessibility certification, exhaustive browser/mobile coverage and high-count performance remain future work. The twin renders supplied geometry without an invented city. Large JS bundle advisory remains.

Phase 5/6 tags are preserved. Development branch: phase6b-ux-refinement; pre-change tag: phase6b-before-refinement; final tag: phase6b-verified-ux. Recovery pointer `.checkpoints/PHASE6B_RECOVERY.json` records source/Git/evidence archives and same-machine copies; these are not off-device backups.

## Modified files

App/main wiring; Sidebar; live LiveCommandCenter, LiveNetworkMap, LiveStatusHeader, LiveAnalytics and LiveSafety; SumoLiveView; TrafficInputsPanel; OverviewCommandCenter; ComparisonLabView; MathematicalModelExplorer; V2IHardwareHub; frontend-repairs unit tests; frontend-audit and sumo browser tests; production smoke script.

New: refinement.css, trafficPresentation.ts, ControllerIntelligence.tsx, SystemHealth.tsx, ResearchEvidence.tsx, phase6b browser tests, and the seven Phase 6B reports. Exact paths are recorded in CHANGED_FILES_PHASE6B.txt. No backend source or safety-critical logic changed.

Supporting reports: FRONTEND_UX_AUDIT.md, UI_DESIGN_SYSTEM.md, DIGITAL_TWIN_REFINEMENT_REPORT.md, PAGE_BY_PAGE_IMPROVEMENTS.md, FRONTEND_INTEGRATION_VERIFICATION.md and RESPONSIVE_TEST_RESULTS.md.
