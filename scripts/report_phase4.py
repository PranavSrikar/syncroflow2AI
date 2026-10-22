"""Write Phase 4 reports from completed machine-readable experiment evidence."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'research/phase4'
RAW=ROOT/'.checkpoints/phase4-final'


def write(name,text):
    (ROOT/name).write_text(text,encoding='utf-8')


def main():
    training=json.loads((DATA/'training-summary.json').read_text())
    benchmark=json.loads((DATA/'benchmark-summary.json').read_text())
    qualification=json.loads((DATA/'policy-qualification.json').read_text())
    replay=json.loads((RAW/'reproducibility.json').read_text())
    resource=json.loads((RAW/'neural-update-resource-probe.json').read_text())
    test=ET.parse(RAW/'backend-final.xml').getroot().find('testsuite')
    tests=f"{test.get('tests')} tests, {test.get('failures')} failures, {test.get('errors')} errors, {test.get('skipped')} skipped, {float(test.get('time')):.2f} s"
    emergency=json.loads((RAW/'emergency-demo.json').read_text())['results'][0]['emergency']
    table='| Model seed | Episode seeds | Decisions | Wall seconds | First / last critic loss | Final checkpoint |\n|---|---|---:|---:|---|---|\n'
    for r in training:
        table+=f"| {r['modelSeed']} | {r['updates'][0]['episodeSeed']}-{r['updates'][-1]['episodeSeed']} | {r['trainedDecisionSteps']} | {r['elapsedSeconds']:.2f} | {r['updates'][0]['valueLoss']:.2f} / {r['updates'][-1]['valueLoss']:.2f} | update-0016.pt |\n"
    total=sum(r['elapsedSeconds'] for r in training)
    selected=benchmark['selection']['selectedCheckpoint']
    write('MAPPO_TRAINING_REPORT.md',f'''# MAPPO training report — Phase 4

Three independent CPU training runs completed using corrected SUMO occupancy observations and corrected phase-expiry execution. They are **unvalidated candidate policies**, not evidence of convergence or a useful operational controller. Operational MAPPO remains disabled.

{table}
Total measured update wall durations: {total:.2f} seconds; processes ran concurrently, so this sum is not elapsed calendar time. Each run has 16 episodes of 320 simulated seconds, 64 five-second decisions per episode: 1024 joint decisions /2048 agent samples per model. The 64-decision seed-11 pilot is excluded from selection. No earlier pre-correction weights were resumed.

## Architecture and update audit

Shared actor: 8 local inputs →32 tanh →32 tanh →2 categorical actions. Central critic: 16 joint inputs →32 tanh →32 tanh →2 values. Local observations are four queues /20, two green indicators, remaining signal time /45, and mean downstream occupancy fraction. Actions are release/hold preferences; MPC may override and the independent supervisor checks timing writes. There is no actor-to-TraCI actuation.

PPO: Adam 0.0003, four full-batch epochs/update, clip 0.2, clipped value loss coefficient 0.5, entropy 0.01, gradient norm clip 0.5, gamma 0.99, GAE lambda 0.95. GAE true-terminal masking and time-limit bootstrapping match hand calculations. Actor and critic both change in real SUMO integration tests. Checkpoint restoration covers weights, optimizer, training count and Torch RNG; a separate test verifies sampled-action replay. No minibatch shuffling, value normalization, learning-rate decay or convergence claim. Large critic losses and shared gradient clipping remain a learning-quality concern.

Reward is unchanged: per-second -(0.1 queue +0.01 sum current waiting time +2 spillback indicators +maximum service age /120 +100 incompatible permissions), plus arrivals divided among two agents. Collision/permission faults abort. These weights are research assumptions, not a validated utility model.

## Reproducibility and evidence

Replay model seed 21 /episode 21000 for64 joint decisions: bit-identical parameters = **{replay['bitIdenticalParameters']}**; maximum parameter difference {replay['maxParameterDifference']}. This single replay does not establish determinism across hardware or timing-dependent solver timeouts. Per-update checkpoints and progress/configuration logs: `.checkpoints/phase4-final/train-21`, `train-31`, `train-41`. Each update is preserved without overwriting older weights. Training source hashes are recorded at process start. Corrected runs used a frozen controller/training driver. Resume requires the exact recorded source configuration; otherwise start a new run.

An earlier three-seed1024-decision cohort is preserved under `.checkpoints/phase4`. Development evaluation exposed a phase-expiry defect: resetting remaining=1 at an already-due phase postponed release. The controlled seed701 probe observed the first phase change at46s before correction and12s afterward. The fix lets the independently approved cyclic program execute an already-due transition, with timing bounds and clearance unchanged. Its regression covers all six stages. Earlier final benchmarking was interrupted; those weights were invalidated by the changed controller fingerprint. No pre-fix policy was activated or qualified. Current reports use only fresh corrected runs and fresh development/final seeds; pre-fix evidence remains separate.

Hardware: AMD Ryzen 7 7445HS, 6 cores/12 logical CPUs, about16GB RAM; CPU-only Torch. Exact Python/Torch/NumPy versions and source hashes: [training-summary.json](research/phase4/training-summary.json); complete installed freeze `.checkpoints/phase4-final/environment-freeze.txt`. SUMO1.28.0; Python3.11.9. Measured update durations include SUMO initialization, TraCI, control, telemetry, PPO update and checkpoint saving. They exclude Python imports, model construction and between-update reporting/cleanup. Torch intra-op threads=1 per model process.

Hardware also includes an NVIDIA GeForce RTX4050 Laptop GPU,6141MiB reported by nvidia-smi,driver573.05. Installed Torch2.14.1+cpu has no CUDA training support. A separately labeled synthetic64-decision/four-epoch neural-update resource probe took{resource['wallSeconds']:.4f}s on CPU and saved no checkpoint. Compared with the corrected115.10s SUMO pilot, this supports retaining the working CPU environment for this small network; no GPU speed comparison was run. Device details and the resource probe are preserved with raw artifacts. GPU acceleration of larger learners/perception remains separate work.

![Training curves](research/phase4/plots/training.png)

Changing episode seeds make the reward curve unsuitable as a controlled performance comparison. Selection used seeds1801-1803, demand1.0,300s; final held-out tests used1901-1903, demand0.75/1.75,300s. Safety qualification used1951-1953,240s. Selected checkpoint: `{selected}`. Selection was frozen before final testing. All seeds, parameters, metrics and checkpoint SHA-256 are preserved in machine evidence.

## Reproduce

```powershell
$env:DEBUG='false'
./backend/.venv/Scripts/python.exe scripts/research_phase4.py train --seeds 51 61 71 --updates 16 --rollout 64
```

Use new seeds/output directories for a new experiment; existing run folders are protected. `--resume` requires the original configuration/source hashes and matching saved progress. `scripts/run_phase4_experiments.py` reproduces this specific21/31/41 protocol and caches already-completed matching trials; it does not launch training. Existing artifacts remain intact. Read PHASE4_EXPERIMENT_PLAN.md before changing partitions.
''')
    results='| Demand | Controller | Completed timeLoss s | Mean / max queue | Throughput veh/h | Unfinished trips |\n|---|---|---|---|---|---|\n'
    for g in benchmark['groups']:
        m=g['metrics']
        fmt=lambda key:f"{m[key]['mean']:.2f} ±{m[key]['sampleSD']:.2f}"
        results+=f"| {g['demandScale']} | {g['mode']} | {fmt('meanCompletedTimeLossSeconds')} | {fmt('meanNetworkQueue')} /{fmt('maxNetworkQueue')} | {fmt('throughputVehiclesPerHour')} | {fmt('unfinishedTrips')} |\n"
    paired='| Demand | Seed | Candidate −MPC timeLoss s | Throughput difference vehicles |\n|---|---|---:|---:|\n'
    for r in benchmark['pairedComparisons']:
        paired+=f"| {r['demandScale']} | {r['seed']} | {r['delayDifferenceSeconds']:.4f} | {r['throughputDifference']} |\n"
    write('CONTROLLER_BENCHMARK_REPORT.md',f'''# Controller benchmark report — Phase 4

Thirty matched final trials completed: five modes ×two demand scales ×three held-out seeds. The learned candidate ran **offline through MPC and the independent supervisors**; it was never installed in the operational coordinator. There is no qualified-policy operational result.

{results}
Entries are mean ±sample standard deviation across seeds1901,1902,1903. Horizon300 simulated seconds, one-second simulation step, five-second candidate recommendations, demand scales0.75 and1.75. Same network/route inputs, SUMO1.28.0, seeds and horizon in each mode. No warm-up exclusion. Hint-free hybrid is the existing MPC executable path with no learned recommendation; equivalent outcomes are expected. Baselines are native fixed-time, supervised Max-Pressure and constrained MPC. Actual control timing is not tuned after seeing final results.

Native SUMO fixed-time uses42s green /3s yellow /42s green /3s yellow, without explicit all-red stages. Adaptive modes use the independently supervised10–45s green,3s yellow and2s all-red ring. Thus this is a comparison of installed research modes, not a pure algorithm ablation with identical clearance budgets. Candidate-versus-MPC qualification uses the same adaptive program/constraints in both arms. A future fixed-time baseline with matched clearance rules would isolate algorithm effects more closely.

{paired}
Three seeds support descriptive variability, not a claim of statistical significance or general traffic superiority. Seed/demand partitions were recorded before testing; the selected checkpoint was frozen using separate selection seeds1801-1803 at demand1.0. Other candidates were not selected using final test data.

![Benchmarks](research/phase4/plots/benchmarks.png)

## Measurement definitions and limitations

Vehicle delay is completed-trip SUMO `timeLoss`, distinct from waiting time and insertion delay. Unfinished trips are right-censored and listed separately. `meanObservedTimeLossIncludingUnfinished` records partial observed timeLoss, not eventual full-trip delay. `meanDepartDelaySeconds` reports insertion delay for recorded trips; vehicles still waiting to depart may be absent. Different controllers can change insertion capacity even with matched configured demand. No demand-normalized superiority inference is made.

Queues are halted approach vehicles summed over both junctions, sampled every second; report time mean and maximum. Throughput is actual arrivals ×3600/300. Waiting fairness is reported as completed-trip mean/p95/max waiting, maximum approach mean wait, maximum service age, and descriptive waiting Gini including unfinished recorded trips. Spillback is downstream-edge indicator seconds. These proxies are not proof of fairness or network stability.

Control latency is `HybridNetwork.before_step` for both junctions, excluding simulator stepping, telemetry reads and policy inference. Mean/p95/max are available per trial; they are not full end-to-end latency. Separate policy-inference mean/p95 and total control-compute mean/p95 per five-second decision are also recorded. The latter sums inference and five before_step calls, excluding simulation and telemetry. Fallback controller-seconds measure time showing fallback diagnostics, not a count of solver timeout events. Up to three experiment processes shared the machine; CPU timings reflect that environment, not isolated real-time guarantees. Solver timeouts and supervisor rejections retain safe behavior. Detailed supervisor accepted/rejected counts and safety faults are preserved.

Corridor pedestrian constraints and emergency response are **not applicable/not measured** because these demand files contain neither. Separate baseline pedestrian/emergency API demonstrations passed; emergency request-to-approach-completion was {emergency['approachResponseSec']:.1f}s at seed95. This is not a candidate-policy emergency comparison. Protected slow-walker, clearance, emergency-stage and fault fallback regressions are included in the backend suite.

## Machine-readable evidence

[Trial CSV](research/phase4/trials.csv), [full trials JSON](research/phase4/trials.json), [aggregated results](research/phase4/benchmark-summary.json), [qualification](research/phase4/policy-qualification.json). Raw SUMO tripinfo is in `.checkpoints/phase4-final/trips`; individual trials and source/version provenance in `.checkpoints/phase4-final/trials`. SVG plots accompany PNG exports. The recovery artifact archive includes these raw data.

Reproduce cached matching experiments after training: `./backend/.venv/Scripts/python.exe scripts/run_phase4_experiments.py`. Rebuild plots/reports: `./backend/.venv/Scripts/python.exe scripts/summarize_phase4.py`, then `./backend/.venv/Scripts/python.exe scripts/report_phase4.py`. Use a new output location for a changed protocol; cache mismatches are rejected.
''')
    failed=[c for c in qualification['performanceValidation']['checks'] if not c['passed']]
    failures='\n'.join('- '+c['name']+(f": {c['measuredReductionPercent']:.3f}% mean delay reduction" if 'measuredReductionPercent' in c else ': '+c.get('reason','screening condition failed')) for c in failed)
    write('POLICY_QUALIFICATION_REPORT.md',f'''# Policy qualification report — Phase 4

**Not qualified. Keep operational MAPPO disabled.** The functioning Max-Pressure +constrained MPC fallback is preserved. No environment variables were set to activate a candidate, and no candidate controlled signals directly.

Selected checkpoint `{selected}`; SHA-256 `{qualification['checkpointSha256']}`. Selection details and the pre-test freeze are recorded in [benchmark-summary.json](research/phase4/benchmark-summary.json).

Numerical inference checks: {qualification['numericalChecksPassed']}. Trained joint decisions: {qualification['trainedDecisionSteps']}. Separate supervised safety checks: {qualification.get('safetyValidationPassed')}, seeds1951/1952/1953,240s each. A minimum step count and finite inference are prerequisites, not evidence of useful learning. Full [qualification evidence](research/phase4/policy-qualification.json).

Failed or incomplete qualification conditions:

{failures}

The recorded screening protocol requires2% lower mean completed-trip timeLoss in each held-out demand stratum, no paired delay regression over5%, no throughput loss over2%, no increased maximum service age, no safety faults/rejections, disjoint provenance and current checkpoint/architecture hashes. These thresholds are research screens, not statistical certification. Combined candidate pedestrian/emergency validation is missing, so unrestricted activation is refused even if corridor comparisons improve.

The runtime gate now requires positive performance/usefulness evidence in addition to the existing numerical,1024-decision,architecture-hash and three-seed closed-loop conditions. A safety-only report cannot activate a model; a regression test covers rejection. `scripts/qualify_mappo.py` deliberately leaves eligibility false after safety-only trials. No passing evidence was fabricated and the gate was not bypassed. Offline research uses the training recommendation interface while retaining MPC and supervisors; that interface is not exposed as an operational policy switch.

Future qualification requires new, independently held-out data after any training or model selection changes. Do not reuse the present final-test seeds for model selection and then describe them as unseen. A future qualified configuration must explicitly set both `SYNCHROFLOW_MAPPO_CHECKPOINT` and `SYNCHROFLOW_MAPPO_VALIDATION`; removing both reverses activation. This phase leaves both unset. Positive qualified-policy API/browser inference remains unverified.
''')
    write('RESEARCH_NEXT_STEPS.md',f'''# Research next steps — Phase 4

Operationally retain supervised Max-Pressure +constrained MPC and the existing demo. The completed experiment is a bounded reproducible CPU pilot, not a converged MAPPO result or proof of controller superiority.

1. Diagnose critic fit and actor gradient magnitude. Compare reward scaling/value normalization and separate actor/critic optimization on training/selection data, with controlled ablations. Large raw targets and shared gradient clipping may suppress actor updates; this is a hypothesis, not an established cause. Preserve the current runs before changing reward or optimization.
2. Extend episode duration, training coverage and decision budget according to measured learning progress. Compare multiple independent model seeds and select only using designated development data.1024 decisions per model is limited experience. Do not treat it as a universal sufficient-training threshold.
3. Revisit the release/hold hint interface only through controlled experiments. Quantify how often MPC accepts or overrides each hint; a weak hint penalty may yield behavior indistinguishable from MPC. Never strengthen hints by weakening safety/fairness/emergency constraints.
4. Build candidate evaluation coverage for combined corridor pedestrians/emergencies, sustained spillback, sensor faults and solver timeouts. Current separate baseline regressions do not qualify a learned policy for these cases.
5. Allocate fresh final-test seeds/scenarios before the next model selection. Expand horizons, demand families and topologies; evaluate warm-up and right-censoring sensitivity, insertion backlog and per-vehicle/movement fairness. Use more repeats and a predeclared statistical analysis before significance claims.
6. Calibrate arrival/saturation/receiving models, PCU weights and forecast uncertainty with genuine data. Camera field accuracy, metric calibration, live hardware, historical forecast accuracy and adverse-weather generalization remain outside this experiment.
7. Maintain local Git checkpoints, verified archives and independent copies. Current separate recovery copies are on the same machine, not off-device backup. Review credentials before any publication; no push or remote was configured.

Regression evidence: {tests}; four real-browser tests passed in34.0s; build,TypeScript,eight frontend groups,pip check,startup smoke and all eight fresh A-H external demos passed. Existing one Starlette warning and Vite warnings remain. Read the training,benchmark and qualification reports for actual numbers and limitations. No production safety certification, real-road superiority or guaranteed camera accuracy is claimed.
''')
    summary=f'''# Phase 4 research update

This section supersedes Stage3 research/Git status below; Stage3 demonstration results remain historical evidence. Fixed repeated postponement of an already-due signal expiry: the controlled release probe observed its first phase change at12s rather than46s, without weakening timing or clearance checks. Earlier research weights were invalidated and preserved separately. Three corrected-architecture MAPPO runs completed,1024 joint decisions each;30 matched final corridor trials and separate held-out safety trials are recorded. **MAPPO remains unqualified and operationally disabled.** Read [MAPPO_TRAINING_REPORT.md](MAPPO_TRAINING_REPORT.md), [CONTROLLER_BENCHMARK_REPORT.md](CONTROLLER_BENCHMARK_REPORT.md), [POLICY_QUALIFICATION_REPORT.md](POLICY_QUALIFICATION_REPORT.md) and [RESEARCH_NEXT_STEPS.md](RESEARCH_NEXT_STEPS.md).

Final backend: {tests}. Four Edge/browser tests passed in34.0s; frontend build,TypeScript,eight frontend groups,pip check,startup smoke and all eight fresh A-H external demos passed. Git2.55.0.windows.5 is installed; exact Stage3 archive preserved as local tag `stage3-verified-demo`, with new local research history. No earlier Git history existed in this export; no remote or push. Recovery pointer: `.checkpoints/PHASE4_RECOVERY.json` (created after final reporting).

Startup remains `./backend/.venv/Scripts/python.exe scripts/run_dev.py`; operational fallback and original network files are preserved. Research evidence/plots: `research/phase4`; raw data/checkpoints `.checkpoints/phase4-final`. Current limitations include limited training, no qualified learned policy, one benchmark topology, short cold-start/censored experiments, and no candidate pedestrian/emergency qualification.

---

'''
    for name in ('PROJECT_STATUS.md','PROTOTYPE_STATUS.md','IMPLEMENTATION_PLAN.md','TEST_RESULTS.md','FINAL_DEMO_REPORT.md','PROJECT_PROGRESS.md'):
        p=ROOT/name
        old=p.read_text(encoding='utf-8')
        if old.startswith('# Phase 4 research update'):
            old=old.split('\n---\n\n',1)[1]
        p.write_text(summary+old,encoding='utf-8')
    recovery='''# Phase 4 recovery and Git update

Git for Windows2.55.0.windows.5 is installed at `C:/Program Files/Git/cmd/git.exe`. New shells inherit its installed machine PATH; existing shells may need restarting or the absolute path. The original export had no Git history. Local tag `stage3-verified-demo` preserves all167 manifest files byte-for-byte in its initial commit; later commits preserve research changes. No force-push, remote or publication occurred.

Stage3 source/artifact archives, their separate copies, ZIP CRCs and every manifest entry were verified before changes. The final Phase4 recovery pointer `.checkpoints/PHASE4_RECOVERY.json` lists source/artifact archives and a Git bundle, exact hashes and separate copies. Research artifacts include every update checkpoint, raw tripinfo, training/configuration logs, qualification,tests and environment freeze. Original Stage1/2/3 recovery copies remain untouched. Separate copies are on the same machine, not off-device backups.

Restore source into a new empty folder; verify SHA-256 and CHECKPOINT_MANIFEST.json before extracting matching artifacts. Never extract over current work. For Git history use `git clone <bundle-path> <new-folder>`; do not initialize over another repository. Install dependencies and rerun checks using RUN_INSTRUCTIONS.md. Templates/Dockerfile/extensionless public assets are now included by the source archiver; personal.env credentials remain excluded. Never enable unqualified saved weights. Keep checkpoint/architecture hashes intact; Git line-ending conversion or controller edits can invalidate byte-based qualification fingerprints, requiring fresh validation.

---

'''
    p=ROOT/'RECOVERY_GUIDE.md'; old=p.read_text()
    if old.startswith('# Phase 4 recovery and Git update'): old=old.split('\n---\n\n',1)[1]
    p.write_text(recovery+old,encoding='utf-8')
    p=ROOT/'RUN_INSTRUCTIONS.md'; old=p.read_text()
    if not old.startswith('# Phase 4 research commands'):
        p.write_text('''# Phase 4 research commands

Set `$env:DEBUG='false'` before research commands in PowerShell. The existing demo startup is unchanged: `./backend/.venv/Scripts/python.exe scripts/run_dev.py`. MAPPO remains disabled; do not configure unqualified candidate weights. Git is installed; restart older terminals to refresh PATH, or use `C:/Program Files/Git/cmd/git.exe`.

Read PHASE4_EXPERIMENT_PLAN.md and the four research reports before new experiments. Training: `./backend/.venv/Scripts/python.exe scripts/research_phase4.py train --seeds 51 61 71 --updates 16 --rollout 64`. Use fresh model seeds/directories; existing checkpoints are protected. Resume only with matching original code/configuration. Offline trials accept `benchmark --seconds 300 --seeds 1001 1002 1003 --scales .75 1.75 --modes fixed_time max_pressure mpc hybrid --split test`; candidate weights require `--checkpoints <path>`, matching training provenance and disjoint seeds. These research trials retain all existing supervisor checks.

Rebuild this completed experiment's charts and reports with `scripts/summarize_phase4.py` followed by `scripts/report_phase4.py`, using the project Python. Artifacts are restored from the Phase4 recovery archive. Do not overwrite frozen selection/test evidence for a new experiment. Install optional training/plotting dependencies with `./backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-research.txt`; the run's environment-freeze.txt records exact installed versions. Use `--output-dir <new-folder>` before the training/benchmark subcommand for separate research data. The three-seed protocol driver `scripts/run_phase4_experiments.py` waits for the recorded21/31/41 runs and reuses matching cached trials; it is not a generic experiment partition generator.

---

'''+old,encoding='utf-8')
    print(tests)


if __name__=='__main__': main()
