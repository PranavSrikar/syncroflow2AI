# SYNCHROFLOW AI

A local traffic-management research platform with a React command center, FastAPI, actual SUMO/TraCI traffic simulation, live WebSocket telemetry, camera perception and reproducible controller experiments.

**Start here when returning: [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md).** It is the single entry point for humans and coding agents: architecture, setup, artifacts, tests, safety constraints, recovery and remaining work.

## Repository and preserved assets

[GitHub repository](https://github.com/PranavSrikar/syncroflow2AI) · default branch **phase6b-ux-refinement** · [recovery release](https://github.com/PranavSrikar/syncroflow2AI/releases/tag/project-pause-handoff).

Local development branches and checkpoint tags are pushed; older `main` is preserved. Optional camera/research assets and evidence are release attachments rather than source files. The release's `GITHUB_RECOVERY.json` identifies the final source/history archives. Start with PROJECT_HANDOFF.md when returning.

## Current state

Phase 6B is implemented and verified at **`phase6b-verified-ux`**, commit `8216ca8`. Subsequent handoff documentation is on branch `phase6b-ux-refinement`. Phase 5 research and earlier checkpoints remain preserved in Git.

- Dominant real SUMO digital twin, four primary KPIs, signal/decision/safety insights, compact simulation controls and responsive layouts.
- Max-Pressure and finite-candidate constrained MPC; Hybrid uses supervised MPC with Max-Pressure fallback.
- Independent timing, clearance, pedestrian, emergency, spillback and fairness protection.
- Camera observations, historical/weather-informed forecasts, analytics, offline research evidence and exports.
- Separate labelled synthetic Three.js demonstration and browser benchmark; its values do not represent SUMO measurements.
- **MAPPO is experimental and unqualified. Keep operational learned policies disabled.** The completed research did not establish superiority over MPC.

## Run locally

Verified environment: Windows/PowerShell, Python 3.11.9, Node 24.21.0, SUMO 1.28.0. Use one backend worker. Install SUMO and add its `bin` directory to PATH.

```powershell
# From the repository root; installation is needed only on a fresh setup.
py -3.11 -m venv backend/.venv
& backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
npm.cmd ci
& backend/.venv/Scripts/python.exe scripts/run_dev.py
```

Open **http://127.0.0.1:3001**. Backend: http://127.0.0.1:8001/api/v1; API docs: http://127.0.0.1:8001/docs. Select network/controller/seed and Start. Pause before Step; Start resumes; Stop before changing network/controller. Ctrl+C in the launcher stops its owned processes. Occupied ports are preserved; optional camera/research setup and alternative ports are in the handoff.

The SUMO-only application does not need Gemini credentials, camera weights or a trained MAPPO policy. This is an unauthenticated local research system; it is not a public production deployment.

## Verified results at the Phase 6B checkpoint

| Check | Result |
|---|---|
| Real-browser integration on 3001/8001 | 14 passed |
| Backend regression | 112 passed; no skips |
| External SUMO demonstrations A–H | All eight passed, including recorded-video inference |
| Frontend unit tests / TypeScript / production build | Passed |
| Built-asset browser / owned startup-shutdown smoke | Passed |
| Desktop screenshots and layout | Inspected at 1366×768 and 1920×1080 |

These are recorded results, not a promise that a future dependency/environment update passes without rerunning. See [test evidence](RESPONSIVE_TEST_RESULTS.md) and [readiness report](FINAL_UI_UX_READINESS_REPORT.md).

```powershell
npm.cmd test
npm.cmd run lint
npm.cmd run build
npm.cmd run test:e2e
& backend/.venv/Scripts/python.exe -m pytest backend/tests
```

The camera browser case needs optional dependencies/assets; otherwise it is skipped. Full reproduction of the recorded no-skip results requires restoring those assets. Tests control disposable simulation sessions.

## Preservation and limitations

Git contains source, scenarios, lockfile, reports, published research results and tests. Dependencies, credentials, build output and `.checkpoints` are excluded. **A Git clone alone does not include optional camera video/weights, raw training artifacts or full screenshot evidence.** [ARTIFACT_MANIFEST.json](ARTIFACT_MANIFEST.json) identifies separately preserved archives and SHA-256 hashes; [the handoff](PROJECT_HANDOFF.md) explains restoration and publication.

No physical roadside hardware, camera frame-stream preview, live reset/speed/manual pedestrian-call API or live benchmark-job API is implemented. Field calibration, comprehensive accessibility/cross-browser certification and high-count performance validation remain open. The large JS bundle advisory remains. Existing explanations are reorganized, not removed; no safety gates were weakened.
