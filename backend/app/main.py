"""
SYNCHROFLOW AI — FastAPI Main Application Entry Point
Phase A: Foundation, Wire Protocol v1.2.0, WebSocket Telemetry Stream, REST APIs.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.services.simulation_service import simulation_service
from app.api.websocket import router as ws_router, manager as ws_manager
from app.api.routes.health import router as health_router
from app.api.routes.simulation import router as simulation_router
from app.api.routes.scenarios import router as scenarios_router
from app.api.routes.controllers import router as controllers_router
from app.api.routes.emergencies import router as emergencies_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.benchmarks import router as benchmarks_router
from app.api.routes.configuration import router as config_router

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan task to run authoritative background simulation loop & broadcast"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} (Protocol {settings.PROTOCOL_VERSION})")
    tick_task = asyncio.create_task(_simulation_tick_loop())
    yield
    tick_task.cancel()
    try:
        await tick_task
    except asyncio.CancelledError:
        pass
    logger.info("Simulation background loop stopped.")


async def _simulation_tick_loop():
    """Background 10Hz authoritative simulation loop"""
    dt = 0.1
    broadcast_accumulator = 0.0
    while True:
        try:
            await asyncio.sleep(dt)
            if simulation_service.is_running:
                simulation_service.step(dt)

            # Broadcast WebSocket updates at ~10Hz
            broadcast_accumulator += dt
            if broadcast_accumulator >= 0.1:
                broadcast_accumulator = 0.0
                await ws_manager.broadcast_state()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in simulation tick loop: {e}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Authoritative Intelligent Adaptive Traffic Signal Control Backend for SYNCHROFLOW AI",
    lifespan=lifespan,
)

# CORS middleware for seamless local React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(health_router)
app.include_router(simulation_router)
app.include_router(scenarios_router)
app.include_router(controllers_router)
app.include_router(emergencies_router)
app.include_router(incidents_router)
app.include_router(benchmarks_router)
app.include_router(config_router)
app.include_router(ws_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "protocolVersion": settings.PROTOCOL_VERSION,
        "status": "online",
        "docs": "/docs",
        "wsEndpoint": "/api/v1/ws/traffic",
    }
