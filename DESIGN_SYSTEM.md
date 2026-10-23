# SYNCHROFLOW design system

Phase 6 uses a restrained dark operations interface. Navy surfaces establish hierarchy; teal identifies interaction, green means connected/healthy, amber means uncertainty/stale/experimental, and red denotes emergency/failure. Every color state has a text label.

Tokens in `src/index.css`: background `#080f1a`, panel `#101b2a`, elevated `#152337`, border `#253449`, text `#e6edf6`, muted `#a3b3c8`, accent `#49c9bd`, warning `#f2bd65`, danger `#f2838d`. The native system sans-serif stack works offline. Tabular numerals and monospaced metadata support comparison.

Shared components in `src/components/live/`: `Badge`, `Metric`, `Panel`, status header, map, explanation, history charts and operation workflow. Card radius 16px, control radius 8px, base spacing 4px with 8/12/16/24/32px steps. Headings use sentence case; units accompany numbers. Empty values use an em dash with an availability explanation, never a fabricated zero.

Navigation preserves all destinations in four task-oriented groups. Header shortcuts are removed to avoid duplication. The tablet rail preserves accessible names/tooltips; main content uses flexible columns that stack below 1100px. Controls wrap; tables scroll inside their container. Desktop command map and insight panel form a primary/secondary hierarchy.

Interaction: native keyboard-operable controls, explicit focus-visible outline, disabled contrast/cursor plus explanatory text, request busy state, reserved metric skeletons before the first observation and visible error/status feedback. Reduced motion suppresses animation and transition. The live map never animates extrapolated trajectories: each position is an observed SUMO sample. SVG graphics include titles, accessible labels and a legend; stale observations are labelled. Desktop operations use a bottom dock; tablet/phone operations stack above the map to avoid obscuring observations.

Charts use bounded observation histories, units, tooltip titles, window selection and provenance. Advanced raw diagnostics remain expandable. Source badges distinguish live SUMO, recorded camera, forecast estimates, browser demonstration and offline research.
