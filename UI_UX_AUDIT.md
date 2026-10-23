# Phase 6 UI/UX audit

Starting checkpoint: `frontend-functionality-repaired` (8116bb8), based on preserved `phase5-evaluated-prototype`. Development branch: `phase6-live-digital-twin`. Date: 23 October 2026.

Audit performed before implementation by inspecting the running 3001 interface, previous feature/browser evidence, React navigation and views, WebSocket provider, SUMO adapter/runtime, supervisory and controller diagnostic contracts. Before screenshot: `.checkpoints/phase6/before-desktop.png`. The preceding detailed functionality audit remains `FRONTEND_FUNCTIONALITY_AUDIT.md`.

| Area | Finding | Planned disposition |
|---|---|---|
| Overview | Long telemetry form, camera settings before primary controls; no live map | Prioritize actual network map, KPIs and compact operation dock |
| Navigation | 14 destinations and duplicated header shortcuts; detailed implementation names | Group monitoring, intelligence, experimentation and system tools; remove duplicate shortcuts while preserving every destination |
| Live/synthetic | Explicit separation exists but browser visual is more prominent than live measurements | Retain synthetic mode; give live mode its own authoritative visual |
| Geometry/vehicles | Adapter already includes actual positions, dimensions, angles, class and lane IDs; road shapes absent from wire | Add read-only cached lane/junction geometry; use SVG SUMO world coordinates, never generated positions |
| Signals | Raw link-order state and nextSwitch available | Map actual controlled links to lane ends; label priority/yielding states; countdown from last authoritative sample |
| Controller | Raw JSON is dominant; policy/fallback/supervisor trace available | Add plain-language policy description and observed-input summary; disclose scope and last decision |
| Analytics | Only aggregate queue plot in live mode | Bounded observed histories with units, windows, tooltips and rates; use vehicle-weighted current wait |
| Camera/forecast | Functional controls but dense prose and all controls exposed on dashboard | Separate monitoring workflow, compact source cards and expandable settings; add source-kind/freshness metadata without exposing source credentials |
| Emergency/pedestrians | Text-only, backend safely controls service | Keep actual injection endpoint; visually distinguish request states and crossing permission/occupancy |
| Responsiveness | Fixed 256px sidebar and nowrap header overflow laptop/tablet | Compact rail on tablets, wrapping controls, bounded content, keyboard/focus support |
| Failure states | Existing stale/disconnected logic works but status scattered | Persistent data-age/connection banner and unavailable metrics; retain last observation with explicit stale labels |
| Research claims | Synthetic and offline modules exist; operational MAPPO disabled | Keep provenance explicit, experimental qualification badge, advanced diagnostic disclosure |

No controller algorithm or safety constraints will be changed. Exact causal decisions will only be described from controller/supervisor telemetry; otherwise explanations are explicitly observed-input summaries. Existing unsupported live reset/speed/pedestrian-call/benchmark APIs remain explained rather than invented.

## Implemented outcome and verification

| Workflow | Final experience | Actual verification |
|---|---|---|
| Monitor traffic | Live SVG map, source-labelled KPIs, desktop operation dock, network focus | Every rendered in-viewport position compared with API; signal-link states and all four KPIs compared with paused SUMO |
| Understand decisions | Dedicated Controller Intelligence destination and Why this signal? panel | Reported MPC policy, supervisor counters and primary/corridor state checked; no causal trace fabricated |
| Analyze performance | Queue/wait/throughput plots, per-approach rates and session windows | Real session observations and window selector tested; not an offline comparison |
| Predict demand | Source/time/horizon, uncertainty plot, existing history/weather controls | CSV, example flag, 120-second monitoring horizon, forecast graph, manual rainfall and settings tested |
| Observe cameras | Source-kind/freshness metadata and calibrated/unavailable measures | Recorded-video YOLO/ByteTrack start/stop and source label tested; physical camera not tested |
| Protect pedestrians | Permission/occupancy/clearance cards | Actual pedestrian fixture, rendered status and backend safety tests |
| Manage emergencies | Request cards, recovery timeline, supervised injection | North/B0 injection, observed activation and Stop cancellation checked |
| Experiment | Five real SUMO fixtures and preserved 25 browser scenarios | Network selection, custom synthetic inflows, seeds and local benchmark/export tested |
| Inspect system | Live health/settings/export plus retained research/hardware tools | Actual legacy ACK, live/synthetic exports and all 14 destinations in both modes tested |
| Failure/recovery | Always-visible dock errors and confirmed status, stale labels/disabled commands | Rejected Start, closed WebSocket and full Stop/Restart tested |
| Responsive/accessibility | Compact rail, stacked tablet operation controls, focus-visible and reduced motion | No document/main horizontal overflow at 1366/1024/768/390px; keyboard Stop and reduced-motion mode exercised |

Browser inspection found and fixed hidden errors inside collapsed diagnostics, flex minimum-width overflow, oversized map stretching and the desktop dock obscuring the intersection. Tests preserve assertions; the MPC-success browser case uses an explicit test-only 1000ms backend solve budget so native scheduling load does not turn it into the fallback case. Production budget and fallback/safety checks remain unchanged. Exact evidence, screenshots and limitations are in `UI_UX_TEST_RESULTS.md`.
