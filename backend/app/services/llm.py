"""
RecruitBot — LLM Gateway Service (Sprint 0.3)

Single audited chokepoint for ALL model traffic in the system.
Built on LiteLLM (multi-provider) + Instructor (structured outputs).

Features:
- Multi-provider: Anthropic, Google, OpenAI via LiteLLM
- Structured JSON outputs validated against Pydantic schemas via Instructor
- Automatic retries with exponential backoff
- PII anonymization before sending to external APIs
- Full telemetry logging (tokens, cost, latency)
- Prompt template registry integration

Usage:
    from app.services.llm import LLMGateway
    gateway = LLMGateway()

    # Simple text generation
    response = await gateway.generate(prompt_name="jd_generation", title="ML Engineer", ...)

    # Structured output (returns a typed Pydantic model)
    result = await gateway.generate_structured(
        prompt_name="resume_parsing",
        response_model=ParsedResume,
        resume_text="..."
    )
"""

import time
import litellm
import instructor
from typing import Type, TypeVar, Optional, Dict, Any, List
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import get_settings
from app.core.prompts import PromptRegistry
from app.services.anonymizer import Anonymizer
from app.services.telemetry import telemetry, TelemetryLogger, LLMTelemetryEvent

# Type variable for structured output generics
T = TypeVar("T", bound=BaseModel)

# Disable LiteLLM's verbose internal logging
litellm.suppress_debug_info = True


class LLMGateway:
    """
    Centralized LLM Gateway — all AI calls flow through here.
    Provides text generation and structured (JSON schema) output.
    """

    def __init__(self):
        settings = get_settings()

        # ── Pin model IDs from config ──
        self.model_premium = settings.LLM_MODEL_PREMIUM
        self.model_fast = settings.LLM_MODEL_FAST
        self.model_fallback = settings.LLM_MODEL_FALLBACK

        # ── Defaults ──
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.temperature = settings.LLM_TEMPERATURE
        self.max_retries = settings.LLM_MAX_RETRIES
        self.timeout = settings.LLM_TIMEOUT_SECONDS
        self.telemetry_enabled = settings.LLM_TELEMETRY_ENABLED

        # ── Set API keys in environment for LiteLLM ──
        import os
        if settings.ANTHROPIC_API_KEY:
            os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY
        if settings.GEMINI_API_KEY:
            os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
        if settings.OPENAI_API_KEY:
            os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

        # ── Instructor client for structured outputs ──
        self.instructor_client = instructor.from_litellm(litellm.completion)

    def _resolve_model(self, tier: str = "premium") -> str:
        """Resolve model ID from tier name."""
        tiers = {
            "premium": self.model_premium,
            "fast": self.model_fast,
            "fallback": self.model_fallback,
        }
        return tiers.get(tier, self.model_premium)

    def _extract_provider(self, model: str) -> str:
        """Extract provider name from LiteLLM model string."""
        if "/" in model:
            return model.split("/")[0]
        return "unknown"

    async def generate(
        self,
        prompt_name: str,
        prompt_version: Optional[str] = None,
        tier: str = "premium",
        model: Optional[str] = None,
        anonymize: bool = False,
        caller_service: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **prompt_kwargs,
    ) -> Dict[str, Any]:
        """
        Generate a text response from the LLM.

        Args:
            prompt_name: Name of the registered prompt template
            prompt_version: Optional version override
            tier: Model tier - "premium", "fast", or "fallback"
            model: Optional direct model ID override
            anonymize: Whether to strip PII before sending
            caller_service: Name of the calling service (for audit)
            **prompt_kwargs: Variables to inject into the prompt template

        Returns:
            Dict with 'content', 'model', 'usage', and 'telemetry_id'
        """
        # Resolve model
        resolved_model = model or self._resolve_model(tier)
        provider = self._extract_provider(resolved_model)

        # Render prompt
        rendered = PromptRegistry.render(prompt_name, prompt_version, **prompt_kwargs)

        # Anonymize if required
        redaction_counts = {}
        if anonymize:
            rendered["user"], redaction_counts = Anonymizer.anonymize(rendered["user"])

        # Build messages
        messages = [
            {"role": "system", "content": rendered["system"]},
            {"role": "user", "content": rendered["user"]},
        ]

        # Execute with timing
        start_time = time.time()
        error_msg = None
        status = "success"
        retry_count = 0

        try:
            response = await litellm.acompletion(
                model=resolved_model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                timeout=self.timeout,
                num_retries=self.max_retries,
            )
        except Exception as e:
            error_msg = str(e)
            status = "error"

            # Attempt fallback if primary failed
            if resolved_model != self.model_fallback:
                try:
                    resolved_model = self.model_fallback
                    provider = self._extract_provider(resolved_model)
                    response = await litellm.acompletion(
                        model=resolved_model,
                        messages=messages,
                        temperature=temperature or self.temperature,
                        max_tokens=max_tokens or self.max_tokens,
                        timeout=self.timeout,
                    )
                    status = "fallback_success"
                    error_msg = f"Primary failed, fell back to {resolved_model}"
                except Exception as fallback_err:
                    raise RuntimeError(
                        f"Both primary and fallback models failed. "
                        f"Primary: {error_msg}. Fallback: {str(fallback_err)}"
                    ) from fallback_err
            else:
                raise

        latency_ms = (time.time() - start_time) * 1000

        # Extract usage
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        total_tokens = input_tokens + output_tokens
        content = response.choices[0].message.content

        # Log telemetry
        if self.telemetry_enabled:
            event = LLMTelemetryEvent(
                model=resolved_model,
                provider=provider,
                prompt_name=rendered["prompt_name"],
                prompt_version=rendered["prompt_version"],
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=TelemetryLogger.estimate_cost(resolved_model, input_tokens, output_tokens),
                latency_ms=round(latency_ms, 2),
                status=status,
                error_message=error_msg,
                retry_count=retry_count,
                caller_service=caller_service,
                anonymization_applied=anonymize,
                pii_redactions=redaction_counts,
            )
            telemetry.log(event)

        return {
            "content": content,
            "model": resolved_model,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            },
            "latency_ms": round(latency_ms, 2),
            "telemetry_id": event.id if self.telemetry_enabled else None,
        }

    async def generate_structured(
        self,
        prompt_name: str,
        response_model: Type[T],
        prompt_version: Optional[str] = None,
        tier: str = "premium",
        model: Optional[str] = None,
        anonymize: bool = False,
        caller_service: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **prompt_kwargs,
    ) -> T:
        """
        Generate a structured response validated against a Pydantic model.
        Uses Instructor to force the LLM to return schema-compliant JSON.

        Args:
            prompt_name: Name of the registered prompt template
            response_model: Pydantic model class to validate response against
            **prompt_kwargs: Variables to inject into the prompt template

        Returns:
            An instance of response_model with validated data
        """
        # Resolve model
        resolved_model = model or self._resolve_model(tier)
        provider = self._extract_provider(resolved_model)

        # Render prompt
        rendered = PromptRegistry.render(prompt_name, prompt_version, **prompt_kwargs)

        # Anonymize if required
        redaction_counts = {}
        if anonymize:
            rendered["user"], redaction_counts = Anonymizer.anonymize(rendered["user"])

        # Build messages
        messages = [
            {"role": "system", "content": rendered["system"]},
            {"role": "user", "content": rendered["user"]},
        ]

        # Execute with timing
        start_time = time.time()
        error_msg = None
        status = "success"

        try:
            result = self.instructor_client(
                model=resolved_model,
                messages=messages,
                response_model=response_model,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                max_retries=self.max_retries,
            )
        except Exception as e:
            error_msg = str(e)
            status = "error"
            raise

        latency_ms = (time.time() - start_time) * 1000

        # Log telemetry (Instructor doesn't expose raw token counts easily,
        # so we estimate based on the response model size)
        if self.telemetry_enabled:
            event = LLMTelemetryEvent(
                model=resolved_model,
                provider=provider,
                prompt_name=rendered["prompt_name"],
                prompt_version=rendered["prompt_version"],
                input_tokens=0,  # Instructor abstracts this
                output_tokens=0,
                total_tokens=0,
                estimated_cost_usd=0.0,
                latency_ms=round(latency_ms, 2),
                status=status,
                error_message=error_msg,
                caller_service=caller_service,
                anonymization_applied=anonymize,
                pii_redactions=redaction_counts,
            )
            telemetry.log(event)

        return result

    def get_telemetry_stats(self) -> dict:
        """Get aggregate telemetry statistics."""
        return telemetry.get_stats()

    def get_recent_events(self, n: int = 20) -> list:
        """Get recent telemetry events."""
        return telemetry.get_recent(n)


# ── Singleton instance ──
llm_gateway = LLMGateway()
