"""HIMSETU — Health & System Diagnostics Endpoints."""

from __future__ import annotations

import time
from fastapi import APIRouter, Request
from himsetu.api.schemas import HealthResponse, SystemStatusResponse

router = APIRouter(tags=["Health & Diagnostics"])

_START_TIME = time.time()


@router.get("/health", response_model=HealthResponse)
@router.get("/api/v1/health", response_model=HealthResponse)
async def get_health(request: Request) -> HealthResponse:
    """Return health status, engine state, and active dataset count."""
    engine = getattr(request.app.state, "engine", None)
    registry = getattr(request.app.state, "registry", None)

    engine_state = engine.state.value if engine else "UNKNOWN"
    count = registry.count() if registry else 0
    uptime = time.time() - _START_TIME

    return HealthResponse(
        status="ok",
        version="0.3.0",
        engine_state=engine_state,
        datasets_count=count,
        uptime_seconds=round(uptime, 2),
    )


@router.get("/api/v1/system/status", response_model=SystemStatusResponse)
async def get_system_status(request: Request) -> SystemStatusResponse:
    """Return detailed system runtime status."""
    engine = getattr(request.app.state, "engine", None)
    registry = getattr(request.app.state, "registry", None)

    engine_state = engine.state.value if engine else "UNKNOWN"
    perm_tier = engine.permissions.active_tier.value if (engine and hasattr(engine, "permissions")) else "READ_ONLY"
    count = registry.count() if registry else 0

    return SystemStatusResponse(
        status="operational",
        engine_state=engine_state,
        active_permissions=perm_tier,
        version="0.3.0",
        registered_datasets=count,
    )
