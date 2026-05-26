from datetime import datetime
from typing import Any

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Overall health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "sales-agent-platform",
        "version": "1.0.0"
    }

@router.get("/health/ready")
async def readiness_check() -> dict[str, str]:
    """
    Readiness check - used for container orchestration
    """
    return {"status": "ready"}

@router.get("/health/live")
async def liveness_check() -> dict[str, str]:
    """
    Liveness check - indicates if the service is alive
    """
    return {"status": "alive"}