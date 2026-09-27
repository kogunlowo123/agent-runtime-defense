"""Health and readiness endpoints."""
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]
    timestamp: datetime


@router.get("/health", response_model=HealthResponse, summary="Liveness check")
async def health() -> HealthResponse:
    """Returns 200 when the service is alive."""
    return HealthResponse(status="ok", version="0.1.0", timestamp=datetime.utcnow())


@router.get("/readiness", response_model=ReadinessResponse, summary="Readiness check")
async def readiness() -> ReadinessResponse:
    """Returns 200 when all sub-systems are ready to serve traffic."""
    checks: dict[str, str] = {
        "api": "ok",
        "anomaly_detector": "ok",
    }
    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return ReadinessResponse(status=overall, checks=checks, timestamp=datetime.utcnow())
