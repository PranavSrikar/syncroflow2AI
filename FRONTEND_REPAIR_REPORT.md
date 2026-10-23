# Frontend repair report

23 October 2026, Asia/Calcutta. Continued from preserved Phase 5 tag `phase5-evaluated-prototype` (`975ce235217a260590bd4ca261ec3871289880e2`) on `frontend-functionality-repair`. The interrupted work was present on disk and was retained. No retraining or policy activation was performed.

## Result

The live workspace now uses shared FastAPI SUMO WebSocket state across navigation, headers, telemetry, charts and safety displays. Browser demonstrations are explicitly separated. Existing history/weather APIs are exposed, custom scenario overrides reach the engine, pedestrian calls modify authoritative state, remote commands require genuine acknowledgements, and failures cannot silently switch to local simulation. Additional browser-discovered defects fixed: duplicate alert IDs, pedestrian registration surviving reset, benchmark seed zero, missing favicon and deprecated shadow-map constant.

See `FRONTEND_FUNCTIONALITY_AUDIT.md` for the feature inventory, root causes and verification boundaries. This does not certify every scientific statement or physical-world capability.

## Validation

| Check | Result / evidence |
|---|---|
| Frontend unit tests | Existing eight suites and five repair checks pass; `.checkpoints/frontend-repair/unit-final.log` |
| TypeScript | `npm.cmd run lint` passes; `typescript-final.log` |
| Production build | `npm.cmd run build` succeeds; `build-final.log` |
| Actual Edge browser | Nine end-to-end tests against the requested `127.0.0.1:3001` and FastAPI `8001`; `browser-3001.log` |
| Backend regression | 107 passed, two optional video tests initially skipped, zero failures/errors; `backend-regression.xml` |
| Optional real camera regression | Both previously skipped tests rerun with recorded road video and pretrained weights: two passed; `camera-regression.xml` |
| External scenarios A–H | Eight passed; real HTTP/WebSocket/SUMO and actual video inference, `external-demos.json` |
| Runtime screenshot | `repaired-3001.png`; `port3001-smoke.json` records no script errors or failed HTTP responses |
| Clean shutdown | Startup helper `--smoke-test` on disposable 8027/3027; owned servers stopped and neither port left listening; `shutdown-smoke.log` |

The browser suite visits all 14 pages in both modes and checks console/script errors and failed HTTP responses. It exercises simulation lifecycle and restart, telemetry/API agreement, MPC and protected pedestrian display, corridor state and emergency injection, spillback, recorded camera start/stop, CSV history, manual weather, forecasts, both export formats, benchmark execution, seed zero, local scenario overrides, pedestrian calls/reset, camera presets, play/pause/step/weather/speed, educational selectors, actual legacy ACK, rejected commands and disconnected WebSocket controls.

External cases: A normal adaptive operation (140 simulation seconds); B unequal demand (140); C downstream spillback (80); D pedestrian protection (180); E emergency priority (180); F two-junction coordination (180); G forced controller fallback (80); H actual recorded-video YOLO/ByteTrack observations and stop fallback. A used explicitly marked example history/weather and an explicit demonstration-only MPC opt-in. That is not measured historical data. Learned policy remained disabled.

Initial checks exposed environmental/test problems as well: inherited `DEBUG=release` fails Pydantic validation (run regressions with `DEBUG=false`); ambiguous text selectors and lack of per-test cleanup contaminated subsequent browser cases; importing a bare Vite module URL during HMR can create a separate test singleton (the test now imports the actual loaded provider URL). Failed intermediate runs were corrected and rerun; they were not counted as successful checks.

## Changed files

| Files | Purpose |
|---|---|
| `src/App.tsx`, `src/main.tsx`, `src/components/navigation/Sidebar.tsx` | Shared live provider, workspace routing and truthful status/control gating |
| `src/services/liveTraffic.tsx` (new) | Backend URL, request helper, shared WebSocket, stale/reconnect state and queue history |
| `src/components/views/SumoLiveView.tsx` | Reusable live modules, backend seed, lifecycle, controller/network and emergency controls |
| `src/components/views/LiveQueueChart.tsx` (new) | Chart actual WebSocket network queues |
| `src/components/views/LiveUtilities.tsx` (new) | Real health check and source-labelled backend snapshot export |
| `src/components/views/TrafficInputsPanel.tsx` | CSV/history/weather controls, safe config edits and request errors |
| `backend/app/api/routes/inputs.py` | Read forecast configuration without resetting it |
| `backend/tests/integration/test_inputs.py` | Regression for enable/config preservation |
| `src/services/trafficProvider.ts` | Genuine remote ACKs, explicit raw remote snapshot, reject offline mutation |
| `src/simulation/engine.ts` | Clone custom scenarios, authoritative pedestrian call, unique alerts |
| `src/components/views/ScenarioLabView.tsx` | Accessible inflow inputs and scenario/seed synchronization |
| `src/components/views/PedestrianCrossingView.tsx` | Engine-driven calls and registered status |
| `src/components/views/ComparisonLabView.tsx` | Benchmark provenance and seed zero |
| `src/components/views/BenchmarkExportView.tsx` | Source/controller/weather metadata and clipboard error handling |
| `src/components/views/ConfigApiView.tsx` | Legacy diagnostic state, truthful endpoint and acknowledgment display |
| `src/components/views/HealthSecurityView.tsx` | Remove unimplemented security/readiness claims |
| `src/components/views/PerceptionCameraView.tsx` | Label synthetic feeds and point to live observations |
| `src/components/v2i/V2IHardwareHub.tsx` | Disclose illustrative payload, no over-air transmission |
| `src/components/3d/TrafficScene.tsx`, `index.html` | Supported shadow map and explicit favicon |
| `tests/frontend-repairs.test.ts` (new), `tests/browser/frontend-audit.spec.ts` (new), `tests/browser/sumo.spec.ts`, `package.json` | Repair regressions, browser inventory/interactions and isolation |
| `FRONTEND_FUNCTIONALITY_AUDIT.md`, `FRONTEND_REPAIR_REPORT.md` (new) | Audit, limitations, reproduction and recovery instructions |

## Reproduce

From the repository root in PowerShell, install dependencies only if absent using `npm.cmd ci` and the existing backend requirements/environment. SUMO must be on PATH. Use one backend worker.

```powershell
$env:SYNCHROFLOW_CAMERA_CONFIG = (Resolve-Path .checkpoints/perception/cameras-api.json).Path
& backend/.venv/Scripts/python.exe scripts/run_dev.py
```

Open `http://127.0.0.1:3001`. The backend is `http://127.0.0.1:8001/api/v1`. The launcher preserves occupied ports; keep the existing healthy session or choose alternate ports. Camera configuration is optional; its JSON must reference existing video and weights. Recovery camera assets are in the Phase 5 artifact archive.

In the live workspace choose a network/controller/seed while stopped, Start, observe advancing time and actual queues, Pause/Step if desired, Stop and Start again. For protected pedestrian service choose the pedestrian network with Max-Pressure/MPC/hybrid. For A0/B0 choose corridor. Use the in-page SUMO emergency controls. Forecast uploads and manual weather are under the expandable history/weather section. Switch to the synthetic demonstration explicitly for 3D controls and the 25-scenario browser catalog.

```powershell
npm.cmd test
npm.cmd run lint
npm.cmd run build
$env:DEBUG = 'false'
Push-Location backend
& .venv/Scripts/python.exe -m pytest tests
Pop-Location
$env:SYNCHROFLOW_EXTERNAL_SERVERS = '1'
$env:SYNCHROFLOW_TEST_URL = 'http://127.0.0.1:3001'
$env:SYNCHROFLOW_TEST_API = 'http://127.0.0.1:8001/api/v1'
npm.cmd run test:e2e
```

For a disposable stopped backend, run `scripts/demo_release.py --base-url <api> --output <new-results.json> --with-example-forecast` using backend Python. This runs all eight scenarios; camera configuration is required for H. To run the two optional backend video tests set `SYNCHROFLOW_TEST_VIDEO` to `.checkpoints/perception/road-vehicles.mp4` and `SYNCHROFLOW_TEST_WEIGHTS` to `.checkpoints/perception/yolo11n.pt` as absolute paths.

## Limits and recovery

Open-Meteo successful external fetching, clipboard-denial UI, physical cameras/roadside devices and narrow-screen usability were not comprehensively tested. No manual live pedestrian API, live benchmarking API, physical V2I/LiDAR, enforced RBAC, annotated video streaming or live corridor-offset editing exists. The UI states these boundaries. Forecast bounds remain heuristic, and camera measurements do not actuate signals. Driver shader precision, Vite configuration/chunk-size and Starlette deprecation warnings are nonfatal and recorded. No claim of field accuracy, trained-policy superiority or road certification is made.

The separate recovery pointer is `.checkpoints/FRONTEND_REPAIR_RECOVERY.json`: it records a verified source archive, Git bundle, evidence archive, hashes and same-machine copies. Git checkpoint tag: `frontend-functionality-repaired`. The original Phase 5 tag and archives remain intact. Restore into a new empty folder, verify hashes/manifests, and use the Phase 5 artifact archive for excluded weights/video/research assets. Copies are local, not off-device backups. Ctrl+C in the startup helper stops its owned SUMO/camera/server processes; unrelated sessions are preserved.
