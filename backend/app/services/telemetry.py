"""
RecruitBot — LLM Telemetry Service (Sprint 0.3)

Logs every LLM call with: model, prompt metadata, tokens, cost, latency.
Supports both in-memory buffering (for dev) and database persistence (for prod).

Usage:
    from app.services.telemetry import TelemetryLogger
    logger = TelemetryLogger()
    logger.log(event)
"""

import uuid
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
from collections import deque


@dataclass
class LLMTelemetryEvent:
    """A single LLM call telemetry record."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Request metadata
    model: str = ""
    provider: str = ""  # anthropic, google, openai
    prompt_name: str = ""
    prompt_version: str = ""

    # Token usage
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    # Cost (estimated, in USD)
    estimated_cost_usd: float = 0.0

    # Performance
    latency_ms: float = 0.0
    status: str = "success"  # success, error, timeout, retry

    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = 0

    # Audit context
    caller_service: str = ""  # e.g., "jd_generation", "resume_parsing"
    anonymization_applied: bool = False
    pii_redactions: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Pricing table (per million tokens, USD) ──
# Updated for current model pricing
MODEL_PRICING = {
    # Anthropic
    "anthropic/claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "anthropic/claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
    "anthropic/claude-opus-4-20250512": {"input": 15.0, "output": 75.0},
    # Google
    "gemini/gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini/gemini-2.5-pro": {"input": 1.25, "output": 10.0},
    # OpenAI
    "openai/gpt-4o": {"input": 2.50, "output": 10.0},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
}


class TelemetryLogger:
    """
    Centralized telemetry logger for all LLM calls.
    Stores events in-memory (ring buffer) and optionally to the database audit_log table.
    """

    def __init__(self, max_buffer_size: int = 1000):
        self._buffer: deque = deque(maxlen=max_buffer_size)
        self._total_calls: int = 0
        self._total_tokens: int = 0
        self._total_cost_usd: float = 0.0

    def log(self, event: LLMTelemetryEvent) -> None:
        """Record a telemetry event."""
        self._buffer.append(event)
        self._total_calls += 1
        self._total_tokens += event.total_tokens
        self._total_cost_usd += event.estimated_cost_usd

    def get_recent(self, n: int = 20) -> List[dict]:
        """Get the N most recent telemetry events."""
        events = list(self._buffer)[-n:]
        return [e.to_dict() for e in events]

    def get_stats(self) -> dict:
        """Get aggregate telemetry statistics."""
        return {
            "total_calls": self._total_calls,
            "total_tokens": self._total_tokens,
            "total_cost_usd": round(self._total_cost_usd, 6),
            "buffer_size": len(self._buffer),
            "avg_tokens_per_call": round(self._total_tokens / max(self._total_calls, 1), 1),
            "avg_cost_per_call_usd": round(self._total_cost_usd / max(self._total_calls, 1), 6),
        }

    @staticmethod
    def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a given model and token counts."""
        pricing = MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})
        cost = (input_tokens * pricing["input"] / 1_000_000) + \
               (output_tokens * pricing["output"] / 1_000_000)
        return round(cost, 8)


# ── Singleton instance ──
telemetry = TelemetryLogger()
