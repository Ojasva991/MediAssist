"""
Low-level Gemini API client.

This module's only job is: send a system prompt + user prompt to Gemini,
return the raw text response. It knows nothing about triage, symptoms,
or JSON parsing - that logic belongs in triage_service.py. This keeps
the boundary clean: if we ever swap Gemini for another model provider,
only this file changes.
"""

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import settings

# Retry only on TRANSIENT failures - things likely to succeed a moment
# later without any change on our end:
#   500/502/504 - generic/gateway server errors
#   503         - "high demand, try again" (we hit this for real in testing)
# Network-level timeouts/connection errors are retried automatically too
# (built into the SDK's retry mechanism, not configured here).
#
# Deliberately NOT retrying 429: in testing, our 429s were a genuine
# "0 free-tier quota for this model" situation, not a brief rate limit.
# Retrying that just delays reaching the fallback for no benefit. If a
# real quota-based rate limit becomes a problem later, 429 can be added
# back to this list.
_RETRYABLE_STATUS_CODES = [500, 502, 503, 504]

_RETRY_OPTIONS = types.HttpRetryOptions(
    attempts=3,  # 1 initial attempt + up to 2 retries
    initial_delay=1.0,  # seconds before the first retry
    max_delay=8.0,  # cap on delay between retries
    exp_base=2,  # exponential backoff: ~1s, ~2s
    http_status_codes=_RETRYABLE_STATUS_CODES,
)


class GeminiClientError(Exception):
    """Raised when the Gemini API call fails for any reason."""


class GeminiClient:
    def __init__(self) -> None:
        self._client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(retry_options=_RETRY_OPTIONS),
        )
        self._model = settings.GEMINI_MODEL

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a prompt to Gemini and return the raw text response.

        Automatically retries up to 2 times (with exponential backoff)
        on transient server errors or network issues before giving up.
        Raises GeminiClientError only after retries are exhausted, or
        immediately for non-retryable errors (bad key, invalid model,
        quota exhausted, etc.) - callers only need to handle one
        exception type either way.
        """
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    # Lower temperature = more consistent, less "creative"
                    # output. Important for a triage tool - we want
                    # predictable, cautious responses, not variety.
                    temperature=0.2,
                    response_mime_type="application/json",
                ),
            )
        except APIError as e:
            raise GeminiClientError(f"Gemini API error: {e}") from e
        except Exception as e:
            # Catches network errors, timeouts, etc. that aren't APIError
            raise GeminiClientError(f"Unexpected error calling Gemini: {e}") from e

        if not response.text:
            raise GeminiClientError("Gemini returned an empty response")

        return response.text


# Module-level singleton - one client instance reused across requests,
# rather than creating a new one per request.
gemini_client = GeminiClient()
