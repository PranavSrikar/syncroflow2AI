# Phase 4 research update

Research is in progress. Git2.55.0.windows.5 is restored; stage3-verified-demo preserves the original release and no remote was configured. Found and fixed repeated postponement of an already-due signal expiry; supervised probe first observed phase change46s before /12s after. Corrected regression:107 backend tests passed in351.02s (one existing warning),4 browser tests in34.0s,all8 A-H external demos passed. The corrected emergency fixture completed its approach in70 simulated seconds.

Fresh corrected training for model seeds21/31/41 is underway in .checkpoints/phase4-final. Pre-fix runs remain in .checkpoints/phase4 and are invalid for the changed controller fingerprint. Fresh selection1801-1803,final1901-1903,safety1951-1953 are reserved. No policy is qualified or operationally enabled. Training/evaluation/report generation are not yet complete. Read PHASE4_EXPERIMENT_PLAN.md. Recovery milestones: .checkpoints/PHASE4_PROGRESS_RECOVERY.json; final pointer will be created after completed research reporting.

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
