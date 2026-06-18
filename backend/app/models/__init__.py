"""
RecruitBot — Database Models (Sprint 0.2)

Canonical schema for the recruitment orchestrator.
Tables: employees, candidates, job_requisitions, applications,
        resumes, interviews, fit_scores, consent, audit_log

All vector columns use pgvector with 1024 dimensions (Voyage AI standard).
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base

# ── Constants ──
VECTOR_DIMENSIONS = 1024  # Voyage AI embedding dimension


def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return uuid.uuid4()


# ══════════════════════════════════════════════════════════════
# 1. EMPLOYEES — Internal staff + performance data
#    Used to build the High-Performer Archetype (Module A)
# ══════════════════════════════════════════════════════════════
class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    role = Column(String(150), nullable=False)
    hire_date = Column(DateTime(timezone=True), nullable=False)
    tenure_months = Column(Integer, default=0)

    # Performance data (for Success Vectors)
    performance_rating = Column(Float, default=3.0)  # 1.0 - 5.0
    promotion_count = Column(Integer, default=0)
    previous_companies = Column(JSONB, default=list)  # ["Company A", "Company B"]
    education = Column(String(255), nullable=True)
    professional_summary = Column(Text, nullable=True)

    # Career DNA embedding (for look-alike search)
    embedding = Column(Vector(VECTOR_DIMENSIONS), nullable=True)

    # Flags
    is_top_performer = Column(Boolean, default=False)  # Top 10%
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("idx_employees_department", "department"),
        Index("idx_employees_top_performer", "is_top_performer"),
    )


# ══════════════════════════════════════════════════════════════
# 2. CANDIDATES — External people applying or being sourced
# ══════════════════════════════════════════════════════════════
class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    current_company = Column(String(200), nullable=True)
    current_role = Column(String(200), nullable=True)
    years_experience = Column(Integer, default=0)
    location = Column(String(200), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    source = Column(String(50), default="direct")  # direct, referral, sourced, silver_medalist

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    resumes = relationship("Resume", back_populates="candidate", lazy="selectin")
    applications = relationship("Application", back_populates="candidate", lazy="selectin")
    consents = relationship("Consent", back_populates="candidate", lazy="selectin")


# ══════════════════════════════════════════════════════════════
# 3. JOB REQUISITIONS — Job openings created by hiring managers
# ══════════════════════════════════════════════════════════════
class JobRequisition(Base):
    __tablename__ = "job_requisitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    title = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False)
    hiring_manager_id = Column(UUID(as_uuid=True), nullable=True)  # Links to auth user

    # Content
    raw_brief = Column(Text, nullable=True)  # What the manager typed
    generated_jd = Column(Text, nullable=True)  # AI-generated inclusive JD
    requirements_json = Column(JSONB, default=dict)  # Structured requirements
    skills_required = Column(JSONB, default=list)  # ["Python", "ML", "Leadership"]

    # Archetype anchor vector (from top-performer analysis)
    archetype_embedding = Column(Vector(VECTOR_DIMENSIONS), nullable=True)

    # Distribution tracking
    posting_channels = Column(JSONB, default=list)  # [{"channel": "Naukri", "status": "live"}]

    # Status
    status = Column(String(20), default="draft")  # draft, active, paused, closed, filled
    location = Column(String(200), nullable=True)
    salary_range = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    applications = relationship("Application", back_populates="requisition", lazy="selectin")

    __table_args__ = (
        Index("idx_requisitions_status", "status"),
        Index("idx_requisitions_department", "department"),
    )


# ══════════════════════════════════════════════════════════════
# 4. APPLICATIONS — Links candidates to job requisitions
# ══════════════════════════════════════════════════════════════
class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False, index=True)
    requisition_id = Column(UUID(as_uuid=True), ForeignKey("job_requisitions.id"), nullable=False, index=True)

    # Pipeline status
    status = Column(
        String(30),
        default="applied",
    )  # applied, screening, interviewing, shortlisted, rejected, hired, withdrawn

    # Sourcing metadata
    source = Column(String(50), default="direct")  # direct, referral, sourced, silver_medalist
    is_silver_medalist = Column(Boolean, default=False)

    applied_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    candidate = relationship("Candidate", back_populates="applications")
    requisition = relationship("JobRequisition", back_populates="applications")
    interviews = relationship("Interview", back_populates="application", lazy="selectin")
    fit_score = relationship("FitScore", back_populates="application", uselist=False, lazy="selectin")

    __table_args__ = (
        Index("idx_applications_status", "status"),
        Index("idx_applications_candidate_req", "candidate_id", "requisition_id", unique=True),
    )


# ══════════════════════════════════════════════════════════════
# 5. RESUMES — Parsed resume data + embedding vectors
# ══════════════════════════════════════════════════════════════
class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False, index=True)

    # Raw content
    raw_text = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)  # Object storage path
    file_format = Column(String(20), nullable=True)  # pdf, docx, image, text

    # Parsed structure (Claude multimodal extraction)
    parsed_json = Column(JSONB, default=dict)
    # Example: { "skills": [...], "roles": [...], "education": [...], "certifications": [...] }

    # Confidence & quality
    parse_confidence = Column(Float, nullable=True)  # 0.0 - 1.0

    # Embedding for semantic matching
    embedding = Column(Vector(VECTOR_DIMENSIONS), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    candidate = relationship("Candidate", back_populates="resumes")


# ══════════════════════════════════════════════════════════════
# 6. INTERVIEWS — AI interview sessions (chat + voice)
# ══════════════════════════════════════════════════════════════
class Interview(Base):
    __tablename__ = "interviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True)

    # Interview configuration
    mode = Column(String(10), default="chat")  # chat, voice
    status = Column(String(20), default="scheduled")  # scheduled, in_progress, completed, abandoned

    # Content
    transcript_json = Column(JSONB, default=list)
    # Example: [{"role": "ai", "content": "...", "timestamp": "..."}, {"role": "candidate", ...}]

    # AI analysis
    soft_skill_markers = Column(JSONB, default=dict)
    # Example: {"communication_clarity": 0.85, "energy": 0.72, "professionalism": 0.91}
    anomalies_detected = Column(JSONB, default=list)
    # Example: [{"type": "employment_gap", "details": "18 months between 2022-2024"}]

    # Candidate Snapshot (generated after interview)
    vibe_check = Column(Text, nullable=True)
    red_flags = Column(JSONB, default=list)
    top_reasons_to_hire = Column(JSONB, default=list)

    # Timing
    duration_seconds = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    application = relationship("Application", back_populates="interviews")


# ══════════════════════════════════════════════════════════════
# 7. FIT SCORES — Weighted 30/40/30 scoring (bias-blind)
# ══════════════════════════════════════════════════════════════
class FitScore(Base):
    __tablename__ = "fit_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, unique=True, index=True)

    # SOW-defined weights: Hard Skills 30 / Experience Quality 40 / Behavioral Intent 30
    hard_skills_score = Column(Float, default=0.0)       # 0-100, weighted at 30%
    experience_quality_score = Column(Float, default=0.0)  # 0-100, weighted at 40%
    behavioral_intent_score = Column(Float, default=0.0)   # 0-100, weighted at 30%
    total_score = Column(Float, default=0.0)  # Weighted composite

    # Explainability
    rationale_json = Column(JSONB, default=dict)
    # Example: {"hard_skills": "Strong Python + ML certs...", "experience": "Relevant prior roles..."}

    # Bias-blind flag
    is_anonymized = Column(Boolean, default=True)  # Scoring was done without protected attributes

    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    application = relationship("Application", back_populates="fit_score")


# ══════════════════════════════════════════════════════════════
# 8. CONSENT — DPDP compliance tracking
# ══════════════════════════════════════════════════════════════
class Consent(Base):
    __tablename__ = "consent"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False, index=True)

    consent_type = Column(
        String(30),
        nullable=False,
    )  # data_storage, sourcing_matching, ai_interviewing, onboarding

    status = Column(Boolean, default=False)  # True = granted, False = revoked
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    granted_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    candidate = relationship("Candidate", back_populates="consents")


# ══════════════════════════════════════════════════════════════
# 9. AUDIT LOG — Tracks all AI + human decisions
# ══════════════════════════════════════════════════════════════
class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)

    # Who acted
    actor_id = Column(UUID(as_uuid=True), nullable=True)  # User or system
    actor_role = Column(String(30), nullable=True)  # hiring_manager, recruiter, system, candidate

    # What happened
    action = Column(
        String(50),
        nullable=False,
    )  # ai_recommendation, human_approval, human_rejection, human_override, consent_change

    # On what
    entity_type = Column(String(50), nullable=False)  # application, score, interview, requisition, consent
    entity_id = Column(UUID(as_uuid=True), nullable=False)

    # Details
    details_json = Column(JSONB, default=dict)
    # Example: {"previous_status": "screening", "new_status": "shortlisted", "reason": "..."}

    created_at = Column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_actor", "actor_id"),
        Index("idx_audit_created", "created_at"),
    )
