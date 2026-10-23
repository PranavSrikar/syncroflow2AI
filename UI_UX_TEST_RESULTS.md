# Phase 6 verification results

Verified 23 October 2026, Asia/Calcutta, on Windows with Node 24.21.0, Python 3.11.9, SUMO 1.28.0 and headless Microsoft Edge. Primary interface: `http://127.0.0.1:3001`; FastAPI: `http://127.0.0.1:8001/api/v1`.

| Check | Result | Evidence under `.checkpoints/phase6/` |
|---|---|---|
| Frontend unit suites | Eight original suites plus five repair checks passed | `frontend-unit.log` |
| TypeScript | Passed (`tsc --noEmit`) | `typescript.log` |
| Production build | Passed, 445ms reported by Vite | `build.log` |
| Edge end-to-end suite against 3001/8001 | **11 passed**, 36.4 seconds | `browser-3001.log` |
| Backend regression, including real video | **112 passed, zero skips/failures/errors**, 240.34 seconds | `backend-regression.xml`, `backend.log` |
| New actual-TraCI geometry/position/service-age cases | Vehicle, pedestrian, corridor: three passed | `digital-twin.xml` (also included in full regression) |
| External scenarios A–H | **Eight passed** | `external-demos.json`, `external-demos.log` |
| Built-asset browser smoke (3037 → 8001) | Passed Start → Pause → observed positions/queues → Stop → Restart → Stop | `production-smoke.json`, `production-smoke.log` |
| Startup/shutdown smoke (3027/8027) | Passed; no owned port left listening | `shutdown-smoke.log` |
| Whitespace/source review | `git diff --check` passed; no controller/supervisor algorithms changed | Git diff / recovery bundle |

## End-to-end coverage

1. All 14 navigation destinations in live and synthetic modes; final navigation sweep records no script/console errors or failed HTTP responses.
2. Authoritative synthetic controls: camera presets, weather, speed/play/pause/step, emergency, scenario search/select/override, pedestrian call/reset.
3. Historical CSV, example flag, forecast toggle, monitoring horizon and uncertainty graphic, manual rainfall/configuration and live snapshot JSON.
4. Browser seven-controller benchmark with seed zero, CSV/JSON downloads, prediction/network/V2I/role selectors and actual legacy backend ACK.
5. Rejected Start, retained backend state, Stop/Restart and closed-WebSocket disabled controls.
6. Actual in-viewport vehicle coordinates and all four KPI cards against paused SUMO, link-state marker comparison, MAPPO qualification disclosure, analytics window and pedestrian clearance display.
7. A0/B0 camera focus, viewport bounds, reduced-motion environment, 1366/1024/768/390px overflow checks, keyboard Stop and disconnected state.
8. Full live lifecycle with forecasts/camera fallback, Max-Pressure protected pedestrians, constrained MPC diagnostics, emergency activation and cancellation.
9. Real recorded-video inference/fusion and explicit recorded-source label, then stop fallback.
10. Corridor MPC-success rendering, per-junction supervisor counters and B0 emergency.
11. Actual measured spillback and externally selected unequal-demand scenario synchronization.

The deterministic MPC-success rendering case explicitly requests a 1000ms budget in its test setup and retains the constrained_mpc assertion. This avoids mistaking legitimate 50ms deadline fallback under native scheduling load for UI breakage. The production default remains 50ms. Demo G explicitly forces timeout and verifies fallback separately; all safety tests remain intact.

External cases run A normal adaptive, B unequal demand, C blocked south receiver/spillback, D protected pedestrians, E emergency priority, F corridor coordination, G sensor/controller fallback, H actual YOLO/ByteTrack recorded video. A's example-history/weather opt-in is explicitly marked demonstration data, not measured history. No unqualified policy was activated.

## Screenshots and measured performance

Before: [desktop](.checkpoints/phase6/before-desktop.png).

After: [analytics](.checkpoints/phase6/after-analytics.png), [emergency](.checkpoints/phase6/after-incidents.png), [camera](.checkpoints/phase6/after-perception.png), [forecast](.checkpoints/phase6/after-prediction.png), [desktop](.checkpoints/phase6/after-desktop.png), [1366](.checkpoints/phase6/after-1366.png), [1024](.checkpoints/phase6/after-1024.png), [768](.checkpoints/phase6/after-768.png), [390](.checkpoints/phase6/after-390.png), [production build](.checkpoints/phase6/production-desktop.png).

These are real paused SUMO observations, not fabricated mockups. The new browser geometry case observed 17 vehicles across the simulation and 12 within the selected viewport; all 12 positions are compared with backend values. Its snapshot serialized to 25,607 bytes. The recorded developer-server navigation reached DOMContentLoaded at 326.1ms and load at 327.7ms. A later pedestrian-page DOM sample had 313 nodes; it is not a map stress-test count.

Built-asset smoke reached DOMContentLoaded at 122.1ms and load at 122.2ms in that local run; snapshot was 22,112 bytes at simulation second 31. Raw timing entries are `browser-performance.json` and `production-smoke.json`. These are individual local observations, not benchmarks, frame-rate measurements, repeatable latency guarantees or claimed improvement over baseline. No FPS claim is made.

The map runs on observed 500ms WebSocket snapshots, caps rendered in-viewport vehicles at 1,500 with disclosure and bounds history to 120 distinct samples. The cap is a protective implementation limit, not a validated high-load capacity. Large-network/long-duration/device performance testing remains future work.

## Limits

No physical roadside camera/V2I/LiDAR, Open-Meteo successful external fetch, calibrated detector/forecast accuracy, screen-reader certification, exhaustive WCAG audit, all tablet models, clipboard-denial path or sustained 1,500-vehicle stress test was established. The 390px check establishes basic containment, not full mobile usability. Raw technical tables can scroll. Multiple signal movements at one lane endpoint overlap on the map; detailed phase states preserve every link. Vite configuration/chunk-size and optional Three driver precision/Starlette deprecation warnings remain nonfatal.

Initial failed layout/error/viewport tests were corrected and rerun. No failed intermediate run is counted as a pass. Reproduction commands are in `FINAL_FRONTEND_READINESS_REPORT.md`.
