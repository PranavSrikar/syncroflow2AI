"""
SYNCHROFLOW AI — Health, Readiness & Capabilities Routes
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from app.schemas.benchmarks import BackendHealthResponse, ActiveEnginesStatus
from app.core.config import settings

router = APIRouter()


@router.get("/health", response_model=BackendHealthResponse)
@router.get("/api/v1/health", response_model=BackendHealthResponse)
async def get_health():
    return BackendHealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        protocolVersion=settings.PROTOCOL_VERSION,
        serverTime=datetime.now(timezone.utc).isoformat(),
        activeEngines=ActiveEnginesStatus(
            sumoConnected=False,  # Will be True in Phase B
            cvxpyMpcReady=False,  # Will be True in Phase D
            mappoModelLoaded=False,  # Will be True in Phase E
            yoloPerceptionOnline=False,  # Will be True in Phase G
        ),
    )


@router.get("/api/v1/capabilities")
async def get_capabilities():
    return {
        "protocolVersion": settings.PROTOCOL_VERSION,
        "platform": "SynchroFlow AI Authoritative Python Backend",
        "phase": "Phase A (FastAPI Foundation & Wire Contracts)",
        "supportedControllers": [
            "fixed",
            "actuated",
            "queue_adaptive",
            "max_pressure",
            "mpc_only",
            "mappo_assisted_mpc",
            "synchroflow_hybrid",
        ],
        "supportedScenarios": 25,
        "features": {
            "webSocketStreaming": True,
            "deterministicSeedPRNG": True,
            "safetyClearanceTransitions": True,
            "conflictMatrixInterlocks": True,
            "emergencyPreemption": True,
            "pedestrianActuation": True,
            "empiricalTripMetrics": True,
            "benchmarksRunner": True,
        },
    }
