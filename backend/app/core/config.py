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

    # ── LLM / AI (Phase 0.3) ──
    ANTHROPIC_API_KEY: Optional[str] = None
    LLM_MODEL_REASONING: str = "claude-opus-4-8"
    LLM_MODEL_GENERAL: str = "claude-sonnet-4-6"
    LLM_MODEL_FAST: str = "claude-haiku-4-5-20251001"

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
