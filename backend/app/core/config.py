"""
SYNCHROFLOW AI — Core Configuration Settings
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    APP_NAME: str = "SYNCHROFLOW AI Backend"
    APP_VERSION: str = "1.2.0"
    PROTOCOL_VERSION: str = "v1.2.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*",
    ]

    # Simulation engine parameters
    DEFAULT_SEED: int = 42
    SIMULATION_STEP_DT: float = 0.1
    AUTOPLAY_ON_STARTUP: bool = True

    # SUMO & Environment variables
    SUMO_HOME: str = "/usr/share/sumo"
    SUMO_HEADLESS: bool = True

    # Security demonstration token
    API_SECRET_KEY: str = "synchroflow-edge-rsu-secret-token"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
