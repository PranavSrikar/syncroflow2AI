# Phase 4 research update

This section supersedes Stage3 research/Git status below; Stage3 demonstration results remain historical evidence. Fixed repeated postponement of an already-due signal expiry: the controlled release probe observed its first phase change at12s rather than46s, without weakening timing or clearance checks. Corrected Poisson rate/mean-gap units; exact legacy overload inputs and completed stress results remain preserved separately. Earlier research weights were invalidated by route/controller fingerprints. Three corrected-architecture/demand MAPPO runs completed,1024 joint decisions each;30 matched final corridor trials and separate held-out safety trials are recorded. **MAPPO remains unqualified and operationally disabled.** Read [MAPPO_TRAINING_REPORT.md](MAPPO_TRAINING_REPORT.md), [CONTROLLER_BENCHMARK_REPORT.md](CONTROLLER_BENCHMARK_REPORT.md), [POLICY_QUALIFICATION_REPORT.md](POLICY_QUALIFICATION_REPORT.md) and [RESEARCH_NEXT_STEPS.md](RESEARCH_NEXT_STEPS.md).

Final backend: 108 tests, 0 failures, 0 errors, 0 skipped, 245.78 s. Four Edge/browser tests passed in32.3s; frontend build,TypeScript,eight frontend groups,pip check,startup smoke and all eight fresh A-H external demos passed. Git2.55.0.windows.5 is installed; exact Stage3 archive preserved as local tag `stage3-verified-demo`, with new local research history. No earlier Git history existed in this export; no remote or push. Recovery pointer: `.checkpoints/PHASE4_RECOVERY.json` (created after final reporting).

Startup remains `./backend/.venv/Scripts/python.exe scripts/run_dev.py`; operational fallback and original network files are preserved. Research evidence/plots: `research/phase4`; raw data/checkpoints `.checkpoints/phase4-demand-corrected`. Current limitations include limited training, no qualified learned policy, one benchmark topology, short cold-start/censored experiments, and no candidate pedestrian/emergency qualification.

---

# SYNCHROFLOW AI - Final prototype status

Release: 2026-10-22, Asia/Calcutta. The existing project is stabilized and runnable; no project rebuild or speculative controller expansion was performed.

Verified: **97 backend tests passed in 350.63 s**, one existing Starlette warning; **4 isolated browser tests passed in 31.2 s** and **4 live browser tests passed in 30.4 s**. Production build, TypeScript, eight frontend test groups, pip check, startup/readiness/cleanup smoke and all eight A-H external demo cases pass. Real video inference: 60 frames / 260 tracked observations / 13 IDs. Live Open-Meteo retrieval succeeded.

The integrated path includes SUMO state/PCU estimation, scoped forecasts or observed-rate fallback, movement Max-Pressure, MAPPO recommendation interface, constrained MPC, independent supervisors, TraCI, API/WebSocket and dashboard. Single-junction, protected pedestrian/emergency and A0/B0 corridor operation are verified. Camera observations remain separate from signal actuation.

Stabilization fixed an occupancy ratio/percent error: blocked-exit occupancy now reads 90.61%, triggers spillback and gives north receiving supply zero. Live phase/program corruption pauses before stepping. Startup diagnostics and occupied-port ownership are tested; dashboard selectors follow external API demos. Original networks are unchanged; demo fixtures are additive.

MAPPO is training/inference-ready and operationally disabled. Historical 64-step smoke weights are unqualified and predate the occupancy normalization correction. Current architecture/checkpoint tests pass, but useful trained policy, qualified-policy runtime activation, controller superiority, field camera accuracy, real historical forecast accuracy and road safety are not established.

Live frontend: http://127.0.0.1:3001; backend docs: http://127.0.0.1:8001/docs. SUMO and camera workers are stopped for handoff. Processes are local and need restarting after process/session shutdown. Startup: `.\backend\.venv\Scripts\python.exe scripts/run_dev.py`.

Read FINAL_DEMO_REPORT.md for all twelve release topics and actual A-H results; RUN_INSTRUCTIONS.md for commands; TEST_RESULTS.md for exact checks; RECOVERY_GUIDE.md for verified recovery. Earlier milestone documents are historical; this final report supersedes earlier status claims.
