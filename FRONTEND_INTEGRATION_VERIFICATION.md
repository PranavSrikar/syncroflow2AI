# Phase 6B integration verification

Backend remains authoritative. No backend source, safety logic, policy or scenario changed. MAPPO remains disabled and labelled Experimental — Not Qualified.

| Frontend | Existing API / event | Verified behavior |
|---|---|---|
| Provider/header/twin/analytics | GET /sumo/status, /sumo/telemetry; WS /sumo/ws | Position, signal, queue, controller and freshness agreement; bounded history |
| Simulation controls | POST /sumo/start, /pause, /step, /stop | Pending/acknowledged/error states, lifecycle/restart, network/controller/seed |
| Safety views | POST /sumo/emergencies/inject; GET /sumo/emergencies/status; snapshot safety | Actual requests/events and pedestrian state; no phase bypass |
| Controller Intelligence | Snapshot controllerDiagnostics, safetySupervisor, serviceAge | Available policy/trace and inputs; unknown rationale explicitly unavailable |
| Camera panel | /traffic/source; /perception/start, /stop, /status | Configured recorded-video inference, provenance, coverage, confidence/age |
| Forecast panel | /forecast/history, /config, /enabled, /forecast; weather configuration | Upload provenance, selected horizon, weather and enabled state |
| System health | GET /health | Explicit refresh/checked time and errors |
| Research evidence | Bundled original Markdown reports | Offline provenance; no invented live benchmark API |
| Synthetic tools | Existing browser engine and explicit legacy provider | Separate source labels; reset confirmation; benchmarks/exports preserved |

Full prior API inventory remains in FRONTEND_BACKEND_INTEGRATION_REPORT.md. This phase adds presentation helpers, not a competing traffic engine.

Confirmed repairs: unknown-policy misleading text, mixed approach permissions, forecast horizon refresh, dock overlap, expanded-map resize feedback, synthetic table clipping and reset confirmation. Mapping regressions are unit-tested. Browser checks cover viewport geometry, zoom/labels, trace/model tabs, reset cancel and lifecycle with expanded diagnostics.

The corridor browser test now waits for backend-confirmed pause before HTTP stepping, fixing a test race without weakening assertions. Successful MPC rendering cases explicitly use a 1000ms test budget; production 50ms is unchanged and forced fallback is independently covered by demonstration G/backend tests.

Failure tests reject commands and disconnect WebSockets; controls disable and errors/freshness remain truthful. Owned-server shutdown and production smoke also pass. No physical equipment, camera frame streaming or external weather-service success is claimed.
