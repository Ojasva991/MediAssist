"""
AI Gateway - tries multiple AI providers in priority order before the
caller falls through to the deterministic rule-engine-only fallback
(app/ai/fallback.py's build_fallback_response).

Same "try several, then a guaranteed fallback" shape already used for
the Overpass nearby-hospitals lookup
(app/emergency/hospital_lookup.py's multi-mirror fallback) - applied
here to the AI triage call so a single provider's outage or rate limit
doesn't force a degraded rule-engine-only response when another
provider could have answered instead.

SCOPE: this gateway is used for the TEXT /analyze path only (see
app/ai/triage_service.py's analyze_symptoms). POST /analyze/image
still calls Gemini's vision capability directly, not through this
gateway - Groq's vision-model lineup wasn't verified as a safe
drop-in replacement for the same conservative image-analysis prompt
(app/ai/prompts.py's IMAGE_SYSTEM_PROMPT), so extending multi-provider
fallback to image analysis is a deliberately separate, not-yet-done
decision, not an oversight.

Provider order:
1. Gemini - the original, still primary, always attempted.
2. Groq - free, no credit card, OpenAI-compatible. Attempted only if
   GROQ_API_KEY is configured; skipped (not treated as a failure) if
   it isn't, since this project must keep working with just Gemini
   configured, same as before this gateway existed.

Providers considered but NOT included here, and why (see
PROJECT_STATE.md for the full research):
- OpenAI: free credits were discontinued mid-2025; real use needs
  prepaid billing (credit card). A new paid-infra decision, not made.
- Ollama (local): needs a dedicated server actually running the model
  - multiple GB of RAM/disk just for weights. Render's free tier
  can't host this at all - a different infrastructure category
  entirely, not just a decision to make.
Both can be added here later following the exact same pattern as Groq
below, once/if those decisions are actually made.
"""

import logging

from app.ai.gemini_client import gemini_client, GeminiClientError
from app.ai.groq_client import groq_client, GroqClientError
from app.config import settings

logger = logging.getLogger(__name__)


class AIGatewayError(Exception):
    """Raised only when every configured provider failed. Callers (see
    app/ai/triage_service.py) treat this exactly like a single-provider
    failure did before this gateway existed: fall through to the
    rule-engine-only response."""


def generate(system_prompt: str, user_prompt: str) -> str:
    """
    Try each available provider in priority order, returning the first
    success. Raises AIGatewayError only if every configured provider
    failed (or none are configured beyond Gemini, and Gemini failed).
    """
    errors: list[str] = []

    try:
        return gemini_client.generate(system_prompt, user_prompt)
    except GeminiClientError as e:
        logger.warning("AI gateway: Gemini failed, trying next provider: %s", e)
        errors.append(f"Gemini: {e}")

    if settings.GROQ_API_KEY:
        try:
            result = groq_client.generate(system_prompt, user_prompt)
            logger.info("AI gateway: Gemini failed but Groq succeeded as fallback")
            return result
        except GroqClientError as e:
            logger.warning("AI gateway: Groq also failed: %s", e)
            errors.append(f"Groq: {e}")
    else:
        logger.debug("AI gateway: GROQ_API_KEY not configured, skipping Groq")

    raise AIGatewayError(
        "All configured AI providers failed: " + ("; ".join(errors) if errors else "none configured")
    )
