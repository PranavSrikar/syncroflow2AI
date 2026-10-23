# Phase 6B design system

Existing React, SVG, Three.js and Tailwind architecture is retained. `src/refinement.css`, imported after `index.css`, incrementally refines the existing primitives.

| Pattern | Rule |
|---|---|
| Canvas / panel / raised | #070f1b / #0d1b2a / #122438 |
| Border / secondary text | #243c50 / #a7b8cb |
| Primary accent | #55d3c5; restrained actions and selection |
| Status | Green healthy; amber uncertain/stale/synthetic; red actual emergency/critical |
| Typography | System sans; monospace for technical values; title 21px, compact labels 10–12px |
| Rhythm | 10–18px gaps/padding; 6–12px corner radii |
| Navigation | 212px desktop rail; 224px wide desktop; compact tablet rail |
| Dashboard | Four KPIs; dominant twin and insight column; in-flow dock; optional diagnostics |
| Secondary pages | Focused cards/tabs; native expandable scientific detail |
| Actions | Pending disable; backend acknowledgement; explicit success/error/source |

1366×768 and 1920×1080 are primary targets. Below 1050px the layout stacks and scrolls. Opening dashboard diagnostics intentionally allows scrolling with a fixed 500px visualization, preventing a ResizeObserver sizing feedback loop. Synthetic scene and controls occupy separate rows; telemetry tables scroll horizontally within their panel.

Map zoom changes a real-coordinate viewport. No city decoration, fake traffic/weather, or fabricated performance deltas are used. Existing reduced-motion, semantic controls and visible focus are retained. Full accessibility certification has not been performed.
