"""
API Router — aggregates all route modules.

New feature routers (requisitions, sourcing, screening, etc.)
are registered here as they are built in each sprint.
"""

from fastapi import APIRouter
from app.api.health import router as health_router

api_router = APIRouter()

# ── Core ──
api_router.include_router(health_router)

# ── Phase 1: Sourcing & Job Distribution ──
# api_router.include_router(requisition_router, prefix="/requisitions")
# api_router.include_router(sourcing_router, prefix="/sourcing")

# ── Phase 2: Screening & Assessments ──
# api_router.include_router(screening_router, prefix="/screening")
# api_router.include_router(interview_router, prefix="/interviews")

# ── Phase 3: Scheduling ──
# api_router.include_router(scheduling_router, prefix="/scheduling")

# ── Phase 4: Pre-boarding ──
# api_router.include_router(preboarding_router, prefix="/preboarding")
