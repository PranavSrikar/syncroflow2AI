# Final test results - 2026-10-22

## Exact results

| Check | Result |
|---|---|
| Pre-stabilization backend baseline | 90 passed, 1 warning, 294.39 s |
| Final full backend (real-video enabled) | **97 passed, 1 existing warning, 350.63 s** |
| Isolated actual Edge integration | **4 passed, 31.2 s** |
| Actual Edge against live 8001/3001 | **4 passed, 30.4 s** |
| Production build and TypeScript | Passed |
| Frontend unit/demo groups | 8/8 passed |
| pip check | No broken requirements |
| Startup/readiness/cleanup smoke | Passed on 8020/3020 |
| Focused startup/demo/fault tests | 7 passed, 5.80 s |
| External HTTP/WebSocket/SUMO demos | A-H all passed, none skipped |
| Real recorded-video CLI | 60 frames, 260 observations, 13 IDs |
| Live Open-Meteo request | Succeeded, 0.0 mm/h in snapshot |
| Archived MAPPO qualification | Numerical pass; insufficient training, evaluation refused |

Machine evidence: .checkpoints/stage3-baseline.xml, stage3-backend-tests.xml, stage3-demo-results.json, stage3-weather-check.json, stage3-policy-qualification.json, stage3-policy-evaluation-gate.json, perception/stage3-road-inference.jsonl and STAGE3_RECOVERY.json.

## Coverage and corrections

Full regression includes actual SUMO lifecycle/control, WebSocket snapshots, stopped-walker clearance protection, emergency arrivals in walk/green/yellow/congestion, timing/fairness/forced solver fallback, actual two-junction actor/critic updates and checkpoint inference, scoped forecasts/weather outages, actual pretrained video/tracking and camera fallback.

New startup tests cover missing dependencies/SUMO, invalid ports and occupied-service preservation without cleanup requests. New SUMO tests use unequal demand and a receiving lane containing 44 stopped cars. The initial blocked-exit check exposed native occupancy 0.906 being mislabeled percent. A direct probe confirmed 220 m / 242.8 m = 0.90609555. Normalization to 90.6096% corrected dashboard, spillback gating, MPC supply and actor observation scaling. The corrected regression verifies >=80%, actual queued traffic and zero north receiving supply.

Fault tests assert that changed live phase/program feedback pauses before simulated time advances. All controller-originated signal writes remain inside independent supervisors. Browser checks verify actual blocked-exit telemetry and selector synchronization after API-started demos.

## Actual demo evidence

A: 140 s normal hybrid; explicit EXAMPLE forecasts reached MPC. B: 140 s unequal demand. C: 80 s blocked exit, measured 90.61% occupancy/zero north supply. D: 180 s pedestrians/15 s clearance. E: 180 s emergency completed. F: 180 s A0/B0 hybrid. G: 80 s forced timeout/missing-camera fallback. H: real YOLO/ByteTrack API observations and stop fallback. REST/WebSocket measurements match. See FINAL_DEMO_REPORT.md for arrivals/limitations.

## Warnings and unverified claims

One existing Starlette/httpx warning remains. Vite reports __dirname/configLoader and bundle-size warnings; build/browser checks pass. No field accuracy, exhaustive weather robustness, robust MPC, superiority, road certification or useful trained MAPPO claim. Historical Stage 2 weights/evaluation metrics predate corrected occupancy and are not current performance evidence. Earlier test histories remain in prior source archives.
