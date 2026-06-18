"""
Health check & system status endpoints.
"""

from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Basic health check — confirms the API is alive."""
    return {
        "status": "healthy",
        "service": "RecruitBot API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/detailed")
async def detailed_health():
    """
    Detailed health check — will report DB, Redis, LLM connectivity
    once those are wired in (Phase 0.2–0.3).
    """
    return {
        "status": "healthy",
        "service": "RecruitBot API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "database": {"status": "not_configured"},
            "llm_gateway": {"status": "not_configured"},
            "redis": {"status": "not_configured"},
        },
    }
