"""
RecruitBot — LLM Gateway API Routes (Sprint 0.3)

Exposes endpoints for:
- Prompt template listing
- LLM telemetry stats and recent events
- Test generation endpoint (dev only)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from app.core.prompts import PromptRegistry
from app.services.llm import llm_gateway
from app.services.telemetry import telemetry

router = APIRouter(prefix="/llm", tags=["LLM Gateway"])


# ── Response Schemas ──
class PromptInfo(BaseModel):
    name: str
    version: str
    description: str


class TelemetryStats(BaseModel):
    total_calls: int
    total_tokens: int
    total_cost_usd: float
    buffer_size: int
    avg_tokens_per_call: float
    avg_cost_per_call_usd: float


class GenerateRequest(BaseModel):
    """Request body for the test generation endpoint."""
    prompt_name: str = Field(..., description="Name of the registered prompt template")
    prompt_version: Optional[str] = Field(None, description="Optional version override")
    tier: str = Field("premium", description="Model tier: premium, fast, or fallback")
    anonymize: bool = Field(False, description="Strip PII before sending to LLM")
    variables: dict = Field(default_factory=dict, description="Variables to inject into prompt template")


# ── Routes ──

@router.get("/prompts", response_model=List[PromptInfo])
async def list_prompts():
    """List all registered prompt templates and their versions."""
    return PromptRegistry.list_all()


@router.get("/telemetry/stats", response_model=TelemetryStats)
async def get_telemetry_stats():
    """Get aggregate LLM usage statistics."""
    return telemetry.get_stats()


@router.get("/telemetry/recent")
async def get_recent_telemetry(limit: int = 20):
    """Get the most recent LLM telemetry events."""
    return telemetry.get_recent(limit)


@router.get("/models")
async def get_configured_models():
    """Show which model IDs are pinned in the current configuration."""
    return {
        "premium": llm_gateway.model_premium,
        "fast": llm_gateway.model_fast,
        "fallback": llm_gateway.model_fallback,
    }


@router.post("/generate")
async def test_generate(req: GenerateRequest):
    """
    Test endpoint: generate a response using a registered prompt template.
    Intended for development and debugging only.
    """
    try:
        result = await llm_gateway.generate(
            prompt_name=req.prompt_name,
            prompt_version=req.prompt_version,
            tier=req.tier,
            anonymize=req.anonymize,
            caller_service="api_test",
            **req.variables,
        )
        return {
            "success": True,
            "data": result,
            "error": None,
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Prompt template not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}")
