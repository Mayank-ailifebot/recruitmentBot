"""
RecruitBot — Prompt Template Registry (Sprint 0.3)

Centralized, versioned prompt management.
All LLM prompts live here — never inline in route handlers or services.

Usage:
    from app.core.prompts import PromptRegistry
    prompt = PromptRegistry.render("jd_generation", title="ML Engineer", brief="...")
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime, timezone


@dataclass
class PromptTemplate:
    """A single versioned prompt template."""
    name: str
    version: str
    system_message: str
    user_template: str
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PromptRegistry:
    """
    Central registry for all LLM prompt templates.
    Supports versioning and safe rendering with variable substitution.
    """

    _templates: Dict[str, PromptTemplate] = {}

    @classmethod
    def register(cls, template: PromptTemplate) -> None:
        """Register a prompt template by name."""
        key = f"{template.name}:{template.version}"
        cls._templates[key] = template
        # Also store as the "latest" for this name
        cls._templates[template.name] = template

    @classmethod
    def get(cls, name: str, version: Optional[str] = None) -> PromptTemplate:
        """Retrieve a prompt template. Falls back to latest if no version specified."""
        key = f"{name}:{version}" if version else name
        if key not in cls._templates:
            raise KeyError(f"Prompt template '{key}' not found. Available: {list(cls._templates.keys())}")
        return cls._templates[key]

    @classmethod
    def render(cls, name: str, version: Optional[str] = None, **kwargs) -> Dict[str, str]:
        """
        Render a prompt template with variable substitution.
        Returns a dict with 'system' and 'user' messages ready for LLM consumption.
        """
        template = cls.get(name, version)
        return {
            "system": template.system_message.format(**kwargs) if kwargs else template.system_message,
            "user": template.user_template.format(**kwargs) if kwargs else template.user_template,
            "prompt_name": template.name,
            "prompt_version": template.version,
        }

    @classmethod
    def list_all(cls) -> list:
        """List all registered prompt names and versions."""
        return [
            {"name": t.name, "version": t.version, "description": t.description}
            for key, t in cls._templates.items()
            if ":" in key  # Only versioned entries (skip "latest" aliases)
        ]


# ══════════════════════════════════════════════════════════════
# REGISTERED PROMPTS — Add new prompts here
# ══════════════════════════════════════════════════════════════

# ── Module A: JD Generation ──
PromptRegistry.register(PromptTemplate(
    name="jd_generation",
    version="v1",
    description="Generate an inclusive, high-converting job description from a hiring manager's brief.",
    system_message=(
        "You are an expert HR content strategist specializing in writing inclusive, high-converting "
        "job descriptions for the Indian tech market. You write in a professional yet warm tone. "
        "You always use gender-neutral language and avoid jargon that could discourage qualified "
        "candidates from applying. You structure JDs for maximum clarity and readability."
    ),
    user_template=(
        "Generate a professional job description based on this brief from the Hiring Manager.\n\n"
        "Job Title: {title}\n"
        "Department: {department}\n"
        "Location: {location}\n"
        "Hiring Manager's Brief:\n{brief}\n\n"
        "Required Skills: {skills}\n\n"
        "Generate a complete JD with: Summary, Key Responsibilities (5-7 bullets), "
        "Required Qualifications, Preferred Qualifications, What We Offer, "
        "and an inclusive Equal Opportunity statement."
    ),
))

# ── Module B: Resume Parsing ──
PromptRegistry.register(PromptTemplate(
    name="resume_parsing",
    version="v1",
    description="Extract structured data from raw resume text.",
    system_message=(
        "You are an expert resume parser. Extract structured information from resumes accurately. "
        "Handle various formats including Indian resume styles. Be precise with dates, company names, "
        "and skill categorization. If information is ambiguous or missing, indicate it clearly."
    ),
    user_template=(
        "Parse the following resume text and extract structured information.\n\n"
        "Resume Text:\n{resume_text}\n\n"
        "Extract: full_name, email, phone, current_company, current_role, total_years_experience, "
        "location, education (list of degrees with institution and year), "
        "work_experience (list of roles with company, title, duration, and key achievements), "
        "skills (categorized into technical and soft), certifications, and languages_spoken."
    ),
))

# ── Module B: Fit Score Evaluation ──
PromptRegistry.register(PromptTemplate(
    name="fit_score_evaluation",
    version="v1",
    description="Evaluate candidate fit using the 30/40/30 weighted scoring model.",
    system_message=(
        "You are a senior talent acquisition analyst. You evaluate candidate-job fit using a "
        "structured, bias-blind scoring methodology. You NEVER consider gender, age, ethnicity, "
        "or any protected characteristic. You focus exclusively on skills, experience quality, "
        "and behavioral intent signals from the candidate's career narrative."
    ),
    user_template=(
        "Evaluate the candidate's fit for the following role.\n\n"
        "Job Requirements:\n{job_requirements}\n\n"
        "Candidate Profile:\n{candidate_profile}\n\n"
        "Score across three dimensions (each 0-100):\n"
        "1. Hard Skills (30% weight): Technical proficiency and certifications.\n"
        "2. Experience Quality (40% weight): Relevance of companies and roles held.\n"
        "3. Behavioral Intent (30% weight): Career narrative — growth, stability, or pivot signals.\n\n"
        "Provide the scores and a brief rationale for each dimension."
    ),
))

# ── Module B: Interview Question Generation ──
PromptRegistry.register(PromptTemplate(
    name="interview_followup",
    version="v1",
    description="Generate dynamic interview follow-up questions based on candidate responses.",
    system_message=(
        "You are an empathetic and professional AI interviewer conducting a 10-15 minute initial "
        "screening. You ask insightful, open-ended follow-up questions based on what the candidate "
        "just shared. You probe for specifics — team size, conflict resolution, measurable impact. "
        "You maintain a warm, conversational tone."
    ),
    user_template=(
        "Context about the role:\n{role_context}\n\n"
        "Interview transcript so far:\n{transcript}\n\n"
        "The candidate just said:\n\"{last_answer}\"\n\n"
        "Generate the next follow-up question. Make it specific to what they mentioned. "
        "If they mentioned managing a team, ask about a specific challenge. "
        "If they mentioned a project, ask about their individual contribution and impact."
    ),
))

# ── Module B: Candidate Snapshot ──
PromptRegistry.register(PromptTemplate(
    name="candidate_snapshot",
    version="v1",
    description="Generate the Candidate Snapshot summary for the Hiring Manager.",
    system_message=(
        "You are a senior recruiter generating a concise executive summary for a Hiring Manager. "
        "Be direct, data-driven, and actionable. Avoid fluff. Highlight both strengths and concerns."
    ),
    user_template=(
        "Based on the following screening data, generate a Candidate Snapshot.\n\n"
        "Candidate Profile:\n{candidate_profile}\n\n"
        "Fit Score Breakdown:\n{fit_score}\n\n"
        "Interview Transcript:\n{transcript}\n\n"
        "Generate:\n"
        "1. Vibe Check: 2-3 sentence summary of soft skills and communication style.\n"
        "2. Red Flags: Any mismatched expectations (salary, notice period, career direction).\n"
        "3. Top 3 Reasons to Hire: Specific, evidence-based reasons from the data.\n"
        "4. One-Line Verdict: A single sentence recommendation."
    ),
))
