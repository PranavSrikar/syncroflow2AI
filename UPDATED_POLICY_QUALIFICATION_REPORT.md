# Updated policy qualification — Phase5

**Not qualified; MAPPO remains operationally disabled.** Supervised MPC with Max-Pressure fallback is preserved. Actual MAPPOCoordinator refused the selected candidate with the published report. The Phase4 report remains unchanged and its failed policy was not reused as new training weights.

Selected SHA256 `780f9bc2b55dc9cfef39097616a1413f9ff9524043388652661db82debf44173`; source/controller fingerprint `282bde4934a3e5eaa61e7758f956aad190b28dfd7a16b12cb486e0bfdf3f2492`. Trained1024 decisions; numerical checks:True; separate safety validation:True; separate safety supervisor rejections:0. Mean delay reductions versus MPC: load0.75: -5.076%, load1.0: -1.585%, load1.75: -0.889%.

The original gate requires≥2% mean delay reduction in every demand stratum,no paired delay regression>5%,no throughput loss>2%,no increased maximum service age,no faults/rejections,current provenance and independent protected-user evidence. These are conservative research screens,not road certification. No criterion was relaxed.

Failed performance conditions:

- at_least_2pct_mean_delay_reduction_d0.75
- no_delay_regression_over_5pct_d0.75_s6303
- at_least_2pct_mean_delay_reduction_d1.0
- at_least_2pct_mean_delay_reduction_d1.75
- no_delay_regression_over_5pct_d1.75_s6303
- no_throughput_loss_over_2pct_d1.75_s6303
- no_service_age_increase_d1.75_s6303

Candidate single-junction transfer challenge checks passed:True. Combined pedestrian/emergency operation on the original two-junction policy topology remains unverified. A positive qualified-policy API/browser test was not attempted. These missing requirements are not reported as safety failures or successful tests. Full machine evidence: [policy-qualification.json](research/phase5/policy-qualification.json).

No policy environment variables were set. No learned actor writes TraCI signals directly; all offline preferences pass through MPC and the existing independent supervisor. Keep both SYNCHROFLOW_MAPPO_CHECKPOINT and SYNCHROFLOW_MAPPO_VALIDATION unset. Future selection/tuning requires new held-out seeds,not reusing6301–6303. No improvement,convergence,statistical significance,real-road superiority or safety certification is inferred beyond the measured results.
