"""Endpoints de estado para Railway y monitoreo."""

from fastapi import APIRouter

from .....config import get_settings

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Blinka PayAgent API",
        "status": "online",
        "environment": get_settings().environment,
    }


@router.get("/api/health")
async def health_check():
    """Endpoint de estado para Railway y monitoreo."""
    return {"status": "ok"}
