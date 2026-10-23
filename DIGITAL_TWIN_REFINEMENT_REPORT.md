# Phase 6B digital twin refinement

The dominant live SVG uses actual SUMO lane/junction geometry, vehicle coordinates, headings, physical dimensions, class/speed, controlled-link signals and pedestrian observations from the existing API/WebSocket snapshot. No backend algorithm changed.

Aspect-aware framing, focused-junction zoom, Road IDs, lane outlines and direction markers improve legibility. Crossing styling follows supplied crossing lanes. Entire-network and A0/B0 focus support the corridor. Rendering remains capped at 1,500 visible vehicles without fabricated motion. No high-load frame-rate claim is made.

Four KPIs show monitored approach vehicles, halted vehicles, vehicle-weighted current mean wait and backend run throughput. They are not completed-trip delay, a network census or comparative improvement percentages. Early throughput can truthfully be zero. Viewport vehicle counts differ from approach counts because their spatial scopes differ.

Approach permissions derive from actual incoming controlled links; mixed permission is labelled partial green. Scheduled switch is SUMO's current next-switch value and can change adaptively. Unknown policies no longer receive an invented explanation. Observed inputs and the last supervisor event's timestamp/reason are distinguished.

| Resolution | Before | After |
|---|---|---|
| 1366×768 | [Baseline](.checkpoints/phase6b/before-1366.png) | [Refined](.checkpoints/phase6b/after-1366.png) |
| 1920×1080 | [Baseline](.checkpoints/phase6b/before-1920.png) | [Refined](.checkpoints/phase6b/after-1920.png) |

Baseline was reproduced from the preserved pre-refinement tag in an isolated worktree on port 3036. Final screenshots use actual paused SUMO on 3001/8001. Browser assertions compare displayed vehicles/coordinates, signals and queues with API snapshots. The separate labelled synthetic 3D scene remains available. This is a truthful engineering schematic, not a photorealistic reconstruction of the reference city.
