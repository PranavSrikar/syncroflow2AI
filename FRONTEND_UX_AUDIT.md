# Phase 6B frontend UX audit

Audited before implementation on 23 October 2026. The reference image is visual inspiration, not a source of traffic measurements, weather values, future phases or performance claims. The pasted Phase 6B brief supplements the user's prioritized acceptance criteria; no attachment-sourced metric is used as telemetry.

Base: `phase6-verified-live-digital-twin` (`570b49f`). Development branch: `phase6b-ux-refinement`. Recovery tag before changes: `phase6b-before-refinement`; verified source ZIP and full Git bundle in `.checkpoints/`. Phase 5 and Phase 6 remain preserved.

## Runtime findings

Real browser audit: `.checkpoints/phase6b/before-audit.json`, `before-1366.png`, `before-1920.png`. All 14 existing live destinations were visited. Integration/source inspection covered shared WebSocket snapshots, lifecycle/injection commands, map geometry/positions, controller diagnostics, camera/forecast APIs and the retained synthetic components.

| Area | Confirmed issue | Refinement |
|---|---|---|
| 1366×768 dashboard | 1,551px page in a 613px viewport; map y543–903; fixed dock y584–732 covers it | Height-aware dashboard with controls in normal flow |
| 1920×1080 | Page still scrolls; map remains fixed at 360px | Flexible map consumes remaining space |
| Hierarchy | Large headers, four KPIs plus duplicated rows/status/raw metrics | Four primary KPIs; compact phase, reason, approaches and safety |
| Live map | Wide field of view makes actual vehicles too small | Actual-coordinate zoom/focus and clearer road/vehicle/signal rendering |
| Explanations | Unknown policy strings fall through to pressure-extension wording; snapshot/decision timing not clear | Explicit policy mapping, last supervisor trace and observed-input qualification |
| Other pages | Repeated live map and automatically open technical diagnostics dominate focused tasks | Dedicated analytics, controller, scenario, safety and health surfaces; optional details |
| Camera/prediction | Camera and forecast sections repeated together | Separate primary monitoring views; preserve all settings in advanced sections |
| Synthetic dashboard | Absolute dock competes with viewport HUD | Keep scene and controls in separate layout rows; collapsible overlays |
| Scientific claims | Educational MPC/QP and hardware specifications can sound operational | Match explanations to finite-candidate code; visibly qualify illustrative hardware |
| Navigation | Research scenarios mixed into monitoring; duplicated mode/status prose | Task-oriented groups, persistent source badge and concise mode control |

No safety-critical backend change is planned. Existing detailed measurements and explanations remain accessible through inspection sections and research views.

Final verification: see FRONTEND_INTEGRATION_VERIFICATION.md and RESPONSIVE_TEST_RESULTS.md. Expanded diagnostic map sizing was additionally repaired after browser automation exposed moving controls.
