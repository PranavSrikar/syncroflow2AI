# Policy qualification report — Phase 4

**Not qualified. Keep operational MAPPO disabled.** The functioning Max-Pressure +constrained MPC fallback is preserved. No environment variables were set to activate a candidate, and no candidate controlled signals directly.

Selected checkpoint `.checkpoints\phase4-demand-corrected\train-41\update-0016.pt`; SHA-256 `a013e764890ebb8d9367f56909a93fdedd29c61a5efeb1057babfd58df66ea47`. Selection details and the pre-test freeze are recorded in [benchmark-summary.json](research/phase4/benchmark-summary.json).

Numerical inference checks: True. Trained joint decisions: 1024. Separate supervised safety checks: True, seeds2951/2952/2953,240s each. A minimum step count and finite inference are prerequisites, not evidence of useful learning. Full [qualification evidence](research/phase4/policy-qualification.json).

Mean delay reduction versus MPC was-0.79% at scale0.75 and1.30% at1.75 (negative means regression). Neither met the required2% improvement. The candidate's worst measured service age was57s,below the supervisor's120s bound. Increased service age relative to MPC fails the conservative fairness screen; it is not a recorded120s safety-bound violation. No benchmark or safety-validation fault,or adaptive supervisor rejection,was observed in the recorded trials.

Failed or incomplete qualification conditions:

- no_delay_regression_over_5pct_d0.75_s2901: screening condition failed
- no_service_age_increase_d0.75_s2901: screening condition failed
- no_service_age_increase_d0.75_s2902: screening condition failed
- no_delay_regression_over_5pct_d0.75_s2903: screening condition failed
- no_service_age_increase_d0.75_s2903: screening condition failed
- at_least_2pct_mean_delay_reduction_d0.75: -0.790% mean delay reduction
- no_service_age_increase_d1.75_s2901: screening condition failed
- no_service_age_increase_d1.75_s2902: screening condition failed
- no_service_age_increase_d1.75_s2903: screening condition failed
- at_least_2pct_mean_delay_reduction_d1.75: 1.299% mean delay reduction
- candidate_combined_pedestrian_emergency_validation: Corridor has neither pedestrians nor emergency arrivals; baseline regressions are separate

The recorded screening protocol requires2% lower mean completed-trip timeLoss in each held-out demand stratum, no paired delay regression over5%, no throughput loss over2%, no increased maximum service age, no safety faults/rejections, disjoint provenance and current checkpoint/architecture hashes. These thresholds are research screens, not statistical certification. Combined candidate pedestrian/emergency validation is missing, so unrestricted activation is refused even if corridor comparisons improve.

The runtime gate now requires positive performance/usefulness evidence in addition to the existing numerical,1024-decision,architecture-hash and three-seed closed-loop conditions. A safety-only report cannot activate a model; a regression test covers rejection. `scripts/qualify_mappo.py` deliberately leaves eligibility false after safety-only trials. No passing evidence was fabricated and the gate was not bypassed. Offline research uses the training recommendation interface while retaining MPC and supervisors; that interface is not exposed as an operational policy switch.

Future qualification requires new, independently held-out data after any training or model selection changes. Do not reuse the present final-test seeds for model selection and then describe them as unseen. A future qualified configuration must explicitly set both `SYNCHROFLOW_MAPPO_CHECKPOINT` and `SYNCHROFLOW_MAPPO_VALIDATION`; removing both reverses activation. This phase leaves both unset. Positive qualified-policy API/browser inference remains unverified.
