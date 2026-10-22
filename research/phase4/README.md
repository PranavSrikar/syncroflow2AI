# Primary Phase 4 study — completed, policy not qualified

This directory contains the corrected-demand experiment: three model seeds trained for1024 joint decisions each; selection on2801–2803;30 final matched trials on2901–2903 at demand0.75/1.75; and separate safety validation on2951–2953. Route/config/controller fingerprints and actual inserted/pending demand are recorded. All six seed/load blocks had matched observed insertion demand across modes.

The selected seed41 candidate remains **unqualified and operationally disabled**. Mean delay was0.79% worse than MPC at the lower load and1.30% better at the higher load; required improvement was2% in each stratum. Individual-delay and comparative service-age screens also failed. No simulation safety fault or adaptive supervisor rejection was recorded. These are limited three-seed,cold-start,one-network results,not statistical significance or road certification.

Read the four root research reports. `trials.csv`, `trials.json`, `benchmark-summary.json`, `training-summary.json` and `policy-qualification.json` provide machine-readable evidence; PNG/SVG plots are in `plots`. Raw tripinfo,all48 current checkpoints,logs and exact environment information are in `.checkpoints/phase4-demand-corrected`,included in the final recovery archive.

Earlier incomplete pre-expiry research is separate in `../phase4-pre-fix`; the complete legacy oversaturated study is in `../phase4-saturated`. Neither is mixed into these primary results. The main demo keeps supervised Max-Pressure +MPC operational with no learned policy enabled.
