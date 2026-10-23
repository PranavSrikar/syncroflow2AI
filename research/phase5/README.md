# Phase5 completed research evidence

MAPPO did not qualify. Retain supervised MPC/Max-Pressure with learned hints disabled.

- 54 diagnostic ablations, seeds5101–5103.
- Three independent-clipping training seeds61/71/81, 1024 decisions each; 48 checkpoints archived.
- 12 selection trials; seed61 checkpoint frozen before final testing.
- 45 matched600s corridor trials: five modes, three loads, seeds6301–6303.
- Three240s safety trials, seeds6501–6503.
- 42 matched240s challenges, seeds6401–6403: five modes for asymmetric/blocked-exit demand; protected MPC/candidate pairs for pedestrian/emergency.

Candidate delay regressions versus MPC: 5.0756%, 1.5854%, 0.8892% at loads0.75/1.0/1.75. No useful learned coordination or statistical superiority established.

Read [experiment results](../../PHASE5_EXPERIMENT_RESULTS.md), [diagnostics](../../MAPPO_DIAGNOSTIC_REPORT.md) and [qualification](../../UPDATED_POLICY_QUALIFICATION_REPORT.md). `results.json` contains aggregate metrics, influence and gate checks; `trials.csv/json` contain corridor rows; `challenge-results.csv/json` contain single-junction comparisons; `plots` contains PNG/SVG exports.

Raw SUMO tripinfo, all update checkpoints, logs and tests are in `.checkpoints/phase5` within the verified recovery artifact archive. Earlier cohorts remain separate. Rebuild reports with the project Python and `scripts/report_phase5.py`. Do not restart completed training. Read the Phase5 protocol before a new study; frozen final seeds cannot later be reused for tuning and called unseen.
