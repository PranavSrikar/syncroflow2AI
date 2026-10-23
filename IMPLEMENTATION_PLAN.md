# Phase 5 completion

The bounded Phase5 diagnostic and independent-clipping experiment is complete. All existing application/safety implementations remain intact; the new policy failed qualification and stays disabled. No further broad training is justified without a new controlled observation/credit-assignment experiment. Read [diagnostics](MAPPO_DIAGNOSTIC_REPORT.md), [results](PHASE5_EXPERIMENT_RESULTS.md), [qualification](UPDATED_POLICY_QUALIFICATION_REPORT.md) and [demonstration guide](DEMONSTRATION_GUIDE.md). Earlier plans follow.

---

# Phase 4 research update

This section supersedes Stage3 research/Git status below; Stage3 demonstration results remain historical evidence. Fixed repeated postponement of an already-due signal expiry: the controlled release probe observed its first phase change at12s rather than46s, without weakening timing or clearance checks. Corrected Poisson rate/mean-gap units; exact legacy overload inputs and completed stress results remain preserved separately. Earlier research weights were invalidated by route/controller fingerprints. Three corrected-architecture/demand MAPPO runs completed,1024 joint decisions each;30 matched final corridor trials and separate held-out safety trials are recorded. **MAPPO remains unqualified and operationally disabled.** Read [MAPPO_TRAINING_REPORT.md](MAPPO_TRAINING_REPORT.md), [CONTROLLER_BENCHMARK_REPORT.md](CONTROLLER_BENCHMARK_REPORT.md), [POLICY_QUALIFICATION_REPORT.md](POLICY_QUALIFICATION_REPORT.md) and [RESEARCH_NEXT_STEPS.md](RESEARCH_NEXT_STEPS.md).

Final backend: 108 tests, 0 failures, 0 errors, 0 skipped, 245.78 s. Four Edge/browser tests passed in32.3s; frontend build,TypeScript,eight frontend groups,pip check,startup smoke and all eight fresh A-H external demos passed. Git2.55.0.windows.5 is installed; exact Stage3 archive preserved as local tag `stage3-verified-demo`, with new local research history. No earlier Git history existed in this export; no remote or push. Recovery pointer: `.checkpoints/PHASE4_RECOVERY.json` (created after final reporting).

Startup remains `./backend/.venv/Scripts/python.exe scripts/run_dev.py`; operational fallback and original network files are preserved. Research evidence/plots: `research/phase4`; raw data/checkpoints `.checkpoints/phase4-demand-corrected`. Current limitations include limited training, no qualified learned policy, one benchmark topology, short cold-start/censored experiments, and no candidate pedestrian/emergency qualification.

---

# Implementation plan - final stabilization complete

## Completed and verified

1. Existing React/FastAPI/SUMO/WebSocket runtime preserved and stabilized.
2. Actual state/PCU estimation, historical/weather prediction and observation fallback integrated with Max-Pressure/MPC.
3. Independent signal gate, phase order, timing/fairness, clearance, protected pedestrians and emergency priority retained and regression-tested. Live feedback is checked before stepping; unapproved programs cannot receive timing writes.
4. Shared multi-junction runtime/training code, centralized critic/shared actor, joint preferences, checkpoints and qualification/evaluation gates implemented. Learned operational policy remains disabled.
5. Real pretrained recorded-video inference and camera API/dashboard observations verified; no road-camera actuation added.
6. A-H repeatable demo runner, unequal-demand/blocked-exit fixtures, startup diagnostics/ownership checks and final documentation completed.
7. Final verification: 97 backend tests, four isolated and four live browser tests, build/TypeScript/eight frontend groups/pip check/startup smoke and eight A-H demos pass. Recovery pointer: .checkpoints/STAGE3_RECOVERY.json.

## Deferred research (not release blockers)

Meaningful MAPPO training/disjoint-seed qualification, positive qualified-policy runtime validation, broader topology/multi-junction pedestrians, calibrated PCU/saturation/receiver/reward models, real historical forecast evaluation, camera field calibration/accuracy/live hardware, calibrated uncertainty, comparative benchmarks and production persistence/security/safety assurance. No completion claims for these.

Release scope is frozen. Read FINAL_DEMO_REPORT.md and RUN_INSTRUCTIONS.md. Prior status versions remain in preserved archives; STAGE1_IMPLEMENTATION.md and STAGE2_IMPLEMENTATION.md are historical milestone detail.
