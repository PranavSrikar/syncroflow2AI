"""
SYNCHROFLOW AI — Security, RBAC & Token Verification
"""

from typing import Optional
from fastapi import Header, HTTPException, status
from app.core.config import settings


def verify_api_token(x_api_token: Optional[str] = Header(None)) -> bool:
    """
    Validate that incoming administrative requests supply a valid Bearer/API token.
    Allows demo bypass when running in local development mode without security enforced.
    """
    if settings.ENVIRONMENT == "development" and not x_api_token:
        return True

    if x_api_token != settings.API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing edge RSU authorization token",
        )
    return True
