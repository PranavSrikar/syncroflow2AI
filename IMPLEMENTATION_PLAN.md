# Phase 4 research update

Primary corrected-demand research is in progress. Fixed two verified defects: repeated postponement of due phase expiry (controlled first phase change46s before /12s after) and reversed Poisson rate/mean-gap interpretation. Current synthetic base demand is2591.558veh/hour; exact legacy saturated input is preserved separately. Corrected-demand verification:108 backend tests passed in245.78s (one existing warning),four browser tests in32.3s; fresh A-H external demonstrations are running.

The completed earlier saturated study remains published at research/phase4-saturated (30 matched trials plus3 safety trials,no faults); its candidate failed2% delay-reduction screening and remains disabled. Fresh primary training uses .checkpoints/phase4-demand-corrected,model seeds21/31/41,selection2801-2803,final2901-2903,safety2951-2953. Do not mix cohorts or enable invalidated checkpoints. No policy is qualified or operationally enabled. Final reports/recovery follow completion of the primary study. Git is restored;stage3-verified-demo preserves the original release,no remote/push. See PHASE4_EXPERIMENT_PLAN.md and .checkpoints/PHASE4_PROGRESS_RECOVERY.json.

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
