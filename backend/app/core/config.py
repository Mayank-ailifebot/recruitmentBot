"""
RecruitBot — Application Configuration

Central config using Pydantic Settings for environment variable management.
All secrets and environment-specific values are loaded from .env files.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── App ──
    APP_NAME: str = "RecruitBot"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # ── CORS ──
    FRONTEND_URL: str = "http://localhost:5173"

    # ── Database (Phase 0.2) ──
    DATABASE_URL: Optional[str] = None

    # ══════════════════════════════════════════════════
    # LLM Gateway Configuration (Sprint 0.3)
    # All model IDs use LiteLLM's provider/model format
    # Swap providers by changing the prefix only
    # ══════════════════════════════════════════════════

    # ── API Keys (set via .env) ──
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # ── Model Tier Configuration (pinned in config) ──
    # Premium: complex reasoning — JD generation, candidate snapshots, interview analysis
    LLM_MODEL_PREMIUM: str = "anthropic/claude-sonnet-4-20250514"
    # Fast: quick classification — parsing validation, consent checks, simple extraction
    LLM_MODEL_FAST: str = "anthropic/claude-haiku-4-5-20251001"
    # Fallback: used when primary provider is down
    LLM_MODEL_FALLBACK: str = "gemini/gemini-2.0-flash"

    # ── LLM Defaults ──
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.3  # Low for structured/deterministic outputs
    LLM_MAX_RETRIES: int = 3
    LLM_TIMEOUT_SECONDS: int = 60

    # ── Telemetry ──
    LLM_TELEMETRY_ENABLED: bool = True

    # ── Auth (Phase 0.4) ──
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    class Config:
        env_file = "../../.env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
