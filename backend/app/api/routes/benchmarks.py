"""
SYNCHROFLOW AI — Scientific Benchmark Runner & Comparative Analytics Routes
Runs reproducible evaluations across the 7 canonical controllers using recorded seeds.
"""

import time
from datetime import datetime, timezone
from fastapi import APIRouter
from app.schemas.benchmarks import BenchmarkRequest, BenchmarkSuiteResponse, ControllerBenchmarkResult
from app.services.simulation_service import SimulationService

router = APIRouter(prefix="/api/v1/benchmarks", tags=["benchmarks"])


@router.post("/run", response_model=BenchmarkSuiteResponse)
async def run_benchmark(req: BenchmarkRequest):
    results = []

    controller_names = {
        "fixed": "Fixed-Time Pre-Timed (112s NEMA)",
        "actuated": "Semi-Actuated Gap-Out (NEMA TS2)",
        "queue_adaptive": "Queue-Proportional Dynamic",
        "max_pressure": "Max-Pressure Adaptive (Varaiya)",
        "mpc_only": "Constrained Receding-Horizon MPC",
        "mappo_assisted_mpc": "MAPPO-Assisted MPC Advisor",
        "synchroflow_hybrid": "SynchroFlow Full Autonomous Hybrid",
    }

    # Run deterministic simulation for each requested controller with identical seed
    for ctrl in req.controllers:
        bench_sim = SimulationService(initial_scenario_id=req.scenarioId, seed=req.seed)
        bench_sim.controller_type = ctrl

        # Step simulation for the requested duration
        steps = int(req.durationSec / 0.5)
        for _ in range(steps):
            bench_sim.step(0.5)

        state = bench_sim.get_state_payload()
        results.append(
            ControllerBenchmarkResult(
                controller=ctrl,
                controllerName=controller_names.get(ctrl, ctrl),
                scenarioName=req.scenarioId.replace("_", " ").title(),
                seed=req.seed,
                simDurationSec=float(req.durationSec),
                measuredAvgDelay=state.metrics.avgWaitTime,
                measuredP95Delay=state.metrics.p95WaitTime,
                measuredThroughput=state.metrics.throughputVehPerHour,
                measuredMaxQueue=state.metrics.maxQueueLength,
                executionStatus="Measured (Authoritative Python Engine)",
            )
        )

    return BenchmarkSuiteResponse(
        experimentId=f"exp-{int(time.time()*1000)}",
        timestamp=datetime.now(timezone.utc).isoformat(),
        scenarioId=req.scenarioId,
        seed=req.seed,
        results=results,
    )
