# SYNCHROFLOW AI - Final research demo status

Release: 2026-10-22, Asia/Calcutta. The existing project is stabilized and runnable; no project rebuild or speculative controller expansion was performed.

Verified: **97 backend tests passed in 350.63 s**, one existing Starlette warning; **4 isolated browser tests passed in 31.2 s** and **4 live browser tests passed in 30.4 s**. Production build, TypeScript, eight frontend test groups, pip check, startup/readiness/cleanup smoke and all eight A-H external demo cases pass. Real video inference: 60 frames / 260 tracked observations / 13 IDs. Live Open-Meteo retrieval succeeded.

The integrated path includes SUMO state/PCU estimation, scoped forecasts or observed-rate fallback, movement Max-Pressure, MAPPO recommendation interface, constrained MPC, independent supervisors, TraCI, API/WebSocket and dashboard. Single-junction, protected pedestrian/emergency and A0/B0 corridor operation are verified. Camera observations remain separate from signal actuation.

Stabilization fixed an occupancy ratio/percent error: blocked-exit occupancy now reads 90.61%, triggers spillback and gives north receiving supply zero. Live phase/program corruption pauses before stepping. Startup diagnostics and occupied-port ownership are tested; dashboard selectors follow external API demos. Original networks are unchanged; demo fixtures are additive.

MAPPO is training/inference-ready and operationally disabled. Historical 64-step smoke weights are unqualified and predate the occupancy normalization correction. Current architecture/checkpoint tests pass, but useful trained policy, qualified-policy runtime activation, controller superiority, field camera accuracy, real historical forecast accuracy and road safety are not established.

Live frontend: http://127.0.0.1:3001; backend docs: http://127.0.0.1:8001/docs. SUMO and camera workers are stopped for handoff. Processes are local and need restarting after process/session shutdown. Startup: `.\backend\.venv\Scripts\python.exe scripts/run_dev.py`.

Read FINAL_DEMO_REPORT.md for all twelve release topics and actual A-H results; RUN_INSTRUCTIONS.md for commands; TEST_RESULTS.md for exact checks; RECOVERY_GUIDE.md for verified recovery. Earlier milestone documents are historical; this final report supersedes earlier status claims.
