# Phase 4 experiment protocol

Protocol recorded before model selection or final benchmark results.

The immutable local `stage3-verified-demo` tag preserves the release archive. Git was absent, not merely off PATH; winget installed Git for Windows after verifying its installer hash. No previous repository metadata existed, so this is new local history, not recovered upstream history. Source and artifact archives and their separate copies passed SHA-256, CRC and entry manifests before research changes.

## Audit and training

Shared decentralized actor: 8 inputs, two 32-unit tanh layers, two categorical actions. Centralized critic: concatenated 16 inputs, two 32-unit tanh layers, two value outputs. Each local actor receives only its junction observation. Actions are release/hold preferences passed to constrained MPC, which writes only through the independent supervisor.

Observations: four approach queues divided by 20; two green indicators; remaining phase time divided by 45; mean downstream occupancy fraction. Current SUMO occupancy normalization is retained. Reward per junction per simulated second: arrival count divided by two minus 0.1 queue, 0.01 sum of current waiting times, 2 per downstream spillback indicator, maximum service age /120 and 100 per incompatible permission. A collision or permission fault aborts. The corridor contains no pedestrians or emergency arrivals; its reward cannot validate those capabilities.

PPO uses four full-rollout epochs, Adam 0.0003, clipping 0.2, entropy coefficient 0.01, value coefficient 0.5, gradient norm clipping 0.5, gamma 0.99 and GAE lambda 0.95. Value clipping uses the old critic predictions. Advantages are standardized jointly across time and agents. True terminals cut GAE; time-limit truncations bootstrap. Hand-calculated tests cover this distinction. No reward/value normalization or convergence guarantee is claimed.

CPU: Ryzen 7 7445HS, 6 physical/12 logical cores, about 16 GB RAM; PyTorch CPU only. Pilot model seed 11, episode seed 11000, 64 decisions /320 simulated seconds took 160.82 wall seconds. Pilot weights are not selected. Main model seeds 21,31,41 each receive 16 independent 320-second episodes of 64 five-second decisions, totaling 1024 joint decisions (2048 agent samples). Episode seeds are model seed *1000 + update index, starting at zero. Every update preserves a distinct checkpoint and atomically updates its progress/configuration report. Three separate training processes use independent SUMO instances. Numerical determinism does not imply identical timing-dependent solver fallback under all machine loads.

## Selection and final test

Selection seeds: 801,802,803 at demand scale 1.0, horizon 300 seconds. Evaluate all three final checkpoints plus MPC. Select the checkpoint with lowest mean completed-trip SUMO timeLoss; break ties by model seed. Freeze the selected checkpoint and selection record before final testing.

Final held-out seeds: 901,902,903 at demand scales 0.75 and 1.75, horizon 300 seconds. These seeds and demand scales are absent from training and selection. The road geometry and route families are shared, so this tests stochastic/demand generalization, not unseen networks. Compare native SUMO fixed-time, Max-Pressure, MPC, hint-free hybrid, and the frozen candidate through offline supervised MPC. The candidate remains disabled in the operational API/dashboard. A qualified operational hybrid is included only if the policy meets the gate. Native fixed-time uses the original SUMO program and issues no adaptive writes.

All modes use identical SUMO version, route inputs, demand scaling, seeds, horizon and measurement definitions. No warm-up exclusion; these are explicitly finite cold-start experiments. Record demand insertion effects and unfinished trips. Mean vehicle delay is SUMO tripinfo timeLoss for completed trips, not current waiting time. Report unfinished trips separately because completed-trip delay is censored. Queue mean/max aggregate halted approach vehicles across both junctions, sampled every second. Spillback is the sum of downstream edge indicators each second; an internal edge may be counted at each receiving junction if represented twice. Waiting fairness uses completed-trip waiting mean/p95/max, maximum approach mean waiting, and maximum time since either green group was served. These are descriptive proxies, not a formal fairness guarantee.

Compute control latency for both junctions from before_step, excluding TraCI simulation stepping, telemetry reads and policy inference; report mean/p95/max. This is a scoped CPU timing measurement, not full inference/communication latency. Record supervisor accepted/rejected actions and aborts. Preserve raw tripinfo and trial JSON, exact source hashes, versions and durations. Aggregate three seeds with sample standard deviations; publish paired candidate-versus-MPC differences. Do not infer significance from three seeds.

Pedestrian and emergency regressions run separately on supplied protected scenarios. They are not present in these matched corridor experiments, so candidate pedestrian/emergency performance remains unvalidated. Never describe absent corridor pedestrians as a passed pedestrian constraint test.

## Conservative qualification decision

Retain the 1024-decision, finite inference, architecture hash and three-seed /240-second closed-loop safety prerequisites. Additionally require disjoint training/selection/test provenance and held-out performance evidence. A candidate needs at least 2% lower mean completed-trip timeLoss than MPC in **each** demand stratum, no paired delay regression over 5%, no throughput loss over 2%, no increased maximum service age, no safety faults, and no supervisor rejections. These are research screening thresholds, not statistical or road-safety certification. Missing candidate validation in pedestrian/emergency scenarios prevents unrestricted operational activation even if corridor performance improves. Safety-only qualification explicitly leaves eligibility false. Any failed or incomplete condition keeps operational MAPPO disabled.

Raw progress and experiment artifacts reside in `.checkpoints/phase4`. Existing demo code, network files, camera assets and unqualified historical checkpoints are preserved. Restarting training requires `--resume` with unchanged recorded source/configuration; changing code requires a new run/seed directory.
