"""Endpoints de estado para Railway y monitoreo."""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.adapters.inbound.dependencies import get_system_status

router = APIRouter(tags=["health"])


@router.get("/")
async def root(status: Dict[str, Any] = Depends(get_system_status)):
    """Health check endpoint."""
    return {"service": "Blinka PayAgent API", "status": "online", "environment": status["environment"]}


@router.get("/api/health")
async def health_check(status: Dict[str, Any] = Depends(get_system_status)):
    """Endpoint de estado para Railway y monitoreo."""
    return {"status": "ok", "database": status["database"]}
