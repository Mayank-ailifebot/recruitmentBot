"""
RecruitBot — Requisition API Routes (Sprint 0.4)

The FIRST real wiring: replaces the fake setTimeout log feed
with a real POST /requisitions round-trip.

Endpoints:
- POST /requisitions — create a new requisition (hiring_manager / recruiter only)
- GET  /requisitions — list requisitions (authenticated)
- GET  /requisitions/{id} — get a single requisition (authenticated)
"""

import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.database import SYNC_DATABASE_URL
from app.core.dependencies import get_current_user, require_role

router = APIRouter(prefix="/requisitions", tags=["Requisitions"])

# ── Sync DB session ──
_engine = create_engine(SYNC_DATABASE_URL, echo=False)
_Session = sessionmaker(bind=_engine)


# ── Request / Response Schemas ──

class CreateRequisitionRequest(BaseModel):
    """Hiring Manager submits a job brief."""
    title: str = Field(..., min_length=3, description="Job title")
    department: str = Field(..., min_length=2, description="Department name")
    raw_brief: str = Field(..., min_length=10, description="Hiring manager's brief describing the ideal candidate")
    skills_required: List[str] = Field(default_factory=list, description="List of required skills")
    location: Optional[str] = Field(None, description="Job location")
    salary_range: Optional[str] = Field(None, description="Salary range (e.g., '₹25-40 LPA')")


class RequisitionResponse(BaseModel):
    id: str
    title: str
    department: str
    hiring_manager_id: Optional[str]
    raw_brief: Optional[str]
    generated_jd: Optional[str]
    skills_required: Optional[list]
    status: str
    location: Optional[str]
    salary_range: Optional[str]
    created_at: str


class RequisitionListResponse(BaseModel):
    total: int
    requisitions: List[RequisitionResponse]


# ── Routes ──

@router.post(
    "",
    response_model=RequisitionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_requisition(
    req: CreateRequisitionRequest,
    user: dict = Depends(require_role("hiring_manager", "recruiter")),
):
    """
    Create a new job requisition.
    This is the first real API wiring — replaces the fake setTimeout log feed.
    Only Hiring Managers and Recruiters can create requisitions.
    """
    session = _Session()
    try:
        req_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        # Try to generate JD via LLM Gateway (gracefully falls back to stub)
        generated_jd = None
        try:
            from app.services.llm import llm_gateway
            result = await llm_gateway.generate(
                prompt_name="jd_generation",
                tier="premium",
                caller_service="requisition_create",
                title=req.title,
                department=req.department,
                location=req.location or "Remote",
                brief=req.raw_brief,
                skills=", ".join(req.skills_required) if req.skills_required else "Not specified",
            )
            generated_jd = result["content"]
        except Exception:
            # LLM not configured yet — use stub
            generated_jd = (
                f"[AI-Generated JD Pending — LLM API key not configured]\n\n"
                f"Title: {req.title}\n"
                f"Department: {req.department}\n"
                f"Brief: {req.raw_brief}\n"
                f"Skills: {', '.join(req.skills_required)}"
            )

        # Insert into database
        import json
        session.execute(
            text("""
                INSERT INTO job_requisitions
                    (id, title, department, hiring_manager_id, raw_brief, generated_jd,
                     skills_required, status, location, salary_range, created_at, updated_at)
                VALUES
                    (:id, :title, :department, :hm_id, :brief, :jd,
                     :skills, 'draft', :location, :salary, :now, :now)
            """),
            {
                "id": req_id,
                "title": req.title,
                "department": req.department,
                "hm_id": user["id"],
                "brief": req.raw_brief,
                "jd": generated_jd,
                "skills": json.dumps(req.skills_required),
                "location": req.location,
                "salary": req.salary_range,
                "now": now,
            },
        )
        session.commit()

        # Log to audit
        session.execute(
            text("""
                INSERT INTO audit_log (id, actor_id, actor_role, action, entity_type, entity_id, details_json, created_at)
                VALUES (:id, :actor_id, :role, 'create_requisition', 'requisition', :entity_id, :details, :now)
            """),
            {
                "id": uuid.uuid4(),
                "actor_id": user["id"],
                "role": user["role"],
                "entity_id": req_id,
                "details": json.dumps({"title": req.title, "department": req.department}),
                "now": now,
            },
        )
        session.commit()

        return RequisitionResponse(
            id=str(req_id),
            title=req.title,
            department=req.department,
            hiring_manager_id=user["id"],
            raw_brief=req.raw_brief,
            generated_jd=generated_jd,
            skills_required=req.skills_required,
            status="draft",
            location=req.location,
            salary_range=req.salary_range,
            created_at=now.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create requisition: {str(e)}")
    finally:
        session.close()


@router.get("", response_model=RequisitionListResponse)
async def list_requisitions(
    user: dict = Depends(get_current_user),
):
    """List all requisitions. Accessible to all authenticated users."""
    session = _Session()
    try:
        results = session.execute(
            text("""
                SELECT id, title, department, hiring_manager_id, raw_brief, generated_jd,
                       skills_required, status, location, salary_range, created_at
                FROM job_requisitions
                ORDER BY created_at DESC
            """),
        ).fetchall()

        requisitions = [
            RequisitionResponse(
                id=str(r[0]),
                title=r[1],
                department=r[2],
                hiring_manager_id=str(r[3]) if r[3] else None,
                raw_brief=r[4],
                generated_jd=r[5],
                skills_required=r[6] if r[6] else [],
                status=r[7],
                location=r[8],
                salary_range=r[9],
                created_at=r[10].isoformat() if r[10] else "",
            )
            for r in results
        ]

        return RequisitionListResponse(
            total=len(requisitions),
            requisitions=requisitions,
        )
    finally:
        session.close()


@router.get("/{requisition_id}", response_model=RequisitionResponse)
async def get_requisition(
    requisition_id: str,
    user: dict = Depends(get_current_user),
):
    """Get a single requisition by ID."""
    session = _Session()
    try:
        result = session.execute(
            text("""
                SELECT id, title, department, hiring_manager_id, raw_brief, generated_jd,
                       skills_required, status, location, salary_range, created_at
                FROM job_requisitions WHERE id = :id
            """),
            {"id": requisition_id},
        ).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Requisition not found")

        return RequisitionResponse(
            id=str(result[0]),
            title=result[1],
            department=result[2],
            hiring_manager_id=str(result[3]) if result[3] else None,
            raw_brief=result[4],
            generated_jd=result[5],
            skills_required=result[6] if result[6] else [],
            status=result[7],
            location=result[8],
            salary_range=result[9],
            created_at=result[10].isoformat() if result[10] else "",
        )
    finally:
        session.close()
