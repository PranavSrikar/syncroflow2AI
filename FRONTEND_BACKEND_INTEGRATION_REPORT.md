# Phase 6 frontend/backend integration

All live operations retain backend authority. No controller, safety supervisor, emergency policy, forecast algorithm or MAPPO qualification rule was rewritten. Additions are read-only telemetry and presentation. Existing synthetic controls still target the separate browser engine and are explicitly labelled.

## Contracts audited before implementation

| Interaction / component | Endpoint / event | Authority and behavior |
|---|---|---|
| `LiveTrafficProvider`, status header, map, KPIs, explanation | `WS /api/v1/sumo/ws` | Existing full runtime snapshot every 500ms; actual observations at simulation steps; disconnected after close/error or >4 seconds without a valid frame; reconnect after 1.5s |
| `SumoLiveView` network/controller/seed | `POST /sumo/start?scenario=&controller=&seed=` | Backend checks active-session compatibility; inputs lock while connected; Start resumes paused sessions |
| Start/Pause/Step/Stop | `POST /sumo/{start,pause,step,stop}` | Wait for backend response, then `GET /sumo/status`; visible request error or action acknowledgement; cannot step running simulation |
| Snapshot refresh | `GET /sumo/status` | Shared state, never local engine fallback |
| Live map | `telemetry.vehicleDetails`, `trafficLights`, `pedestrians`, new `networkGeometry` | Exact SUMO world coordinates, dimensions, heading, class and signal-link order; SVG changes coordinate orientation only |
| Map junction selection | Client read-only view of `junctions[id]` | Selects per-junction observations/diagnostics and map bounds; does not mutate SUMO |
| Queue/wait/throughput | Snapshot `approaches`, `metrics` | Approach sums, vehicle-weighted current wait, backend run throughput; session histories bounded to 120 distinct samples |
| Rate comparison | `telemetry.stateEstimates` | Existing identity-based arrival/discharge estimates in vehicles/s, not forecasts |
| Why this signal? | `controllerDiagnostics`, `safetySupervisor`, new `serviceAge` | Reported policy, pressure, receiving-supply heuristic, arrival source, actual fairness ages; no invented confidence or inferred improvement |
| Emergency injection | `POST /sumo/emergencies/inject` | Approach, priority=3 and optional corridor junctionId; adaptive-only; safe eligibility/clearance decided by backend |
| Emergency requests/events | Snapshot `emergencyPriority` | Actual request state, vehicle, approach, ETA and event time; UI cannot override supervisor |
| Pedestrian display | `telemetry.pedestrianSignals`, `pedestrians` | Existing permission state, waiting people, occupants and required clearance; no manual live-call API added |
| Source monitoring | `GET /traffic-state?source=sumo|camera` | Camera fusion when available, explicit fallback otherwise; observations never actuate live controller |
| Camera lifecycle | `POST /perception/start`, `/perception/stop` | Requires existing server configuration; actual YOLO/ByteTrack observations, errors shown |
| Camera provenance | Per-camera `sourceKind`, `observationAgeSec`, `timestampBasis` (new) | Recorded replay vs configured live source; monotonic receive-age; no device/file URL or credentials exposed |
| History CSV | `POST /forecast/history` | Existing CSV validation; explicit example-data flag; example remains barred from MPC unless separately explicitly enabled on backend |
| Forecast settings | `GET/POST /forecast/config`, `POST /forecast/enabled?enabled=` | Read before edit, preserve unrelated settings; enable toggle does not reset config |
| Prediction horizon | `GET /forecast?horizon_sec=60|120|300` | Read-only monitoring horizon; does not change controller prediction horizon/configuration |
| Weather | `POST /forecast/weather`, `/forecast/weather/refresh` | Manual rainfall is user input; Open-Meteo requires coordinates/network; missing inputs widen uncertainty |
| Forecast visuals | Backend `generatedAt`, `horizonSec`, approach `steps` and bounds | PCU/s estimates and heuristic bounds; generatedAt is query time, not history freshness |
| Health | `GET /health` and live snapshot | Actual service version/health; RBAC remains unavailable |
| Live export | Local download of actual received snapshot | Source/capture timestamp/limitations included; disabled when disconnected |
| Legacy provider diagnostics | `/ws/traffic`, existing `/simulation/*` | Separate backend synthetic provider, actual ACK required; raw remote state shown; no SUMO claim |
| Browser demonstration | `TrafficSimulationEngine` only | Existing camera, play/speed/weather, 25 scenarios, benchmark, export and pedestrian controls retained |
| Offline research | Existing Phase 5 reports/artifacts | Not presented as live comparative results; qualification remains failed |

## Backward-compatible backend additions

`SumoAdapter` caches lane shapes/widths/edge IDs and signalized-junction shapes/positions per connection; cache resets on Start. All values are read through TraCI, and no new mutator is introduced. Non-signalized empty boundary shapes are not queried: this SUMO build's shape decoder fails on them. Lane endpoints still describe boundary roads. Existing vehicle and signal fields are unchanged.

`SumoRuntime.snapshot()` adds `serviceAge` for single/per-junction controllers, derived from existing supervisor `last_served` and `MAX_RED`. Definition: time since phase last observed green, not individual waiting time or a new fairness calculation. `CameraRuntime.snapshot()` adds source-kind/age/basis. The original routes and WebSocket format remain compatible with prior clients ignoring new fields.

## Synchronization and failure behavior

Network/controller selectors follow externally started active runs. Disconnect leaves last observation explicitly stale, disables live commands, and makes KPI availability clear. Errors are outside collapsed diagnostics. Lifecycle controls show busy state and backend-confirmed status. Camera polling is cancelled on navigation/source changes; WebSocket listeners, stale timers and reconnect timers clean up on unmount. Chart samples reset on backwards simulation time and remain bounded. No browser-generated vehicle animation/extrapolation runs in live mode.

The existing remote-provider HMR test instrumentation imports the actual loaded module URL; otherwise Vite cache-busting can create a separate singleton. Production components do not use that test mechanism.
