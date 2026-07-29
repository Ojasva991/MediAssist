"""
Groq API client - a free (no credit card required), fast-inference
provider used as the second link in the AI gateway's fallback chain
(see app/ai/gateway.py) when Gemini is unavailable or rate-limited.

Groq's API is OpenAI-compatible (same request/response shape as
OpenAI's chat completions endpoint). Implemented here with plain
urllib rather than adding the `openai` SDK as a new dependency for a
single provider - same "no new dependency unless it earns it"
reasoning already used elsewhere in this project (see
app/emergency/hospital_lookup.py's Overpass client).

Free tier as of when this was added: 30 requests/minute, 14,400
requests/day, no credit card required, every model included. If
GROQ_API_KEY isn't set, this provider is simply unavailable and the
gateway skips it - that's an expected, normal state (e.g. anyone who
hasn't signed up for a Groq key yet), not an error condition.
"""

import json
import logging
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.config import settings

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqClientError(Exception):
    """Raised when the Groq API call fails for any reason, including
    when GROQ_API_KEY isn't configured at all."""


class GroqClient:
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not settings.GROQ_API_KEY:
            raise GroqClientError("GROQ_API_KEY is not configured")

        payload = {
            "model": settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            # Same reasoning as Gemini's config: low temperature for
            # predictable, cautious triage output rather than variety.
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        request = Request(
            GROQ_API_URL,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                data = json.loads(response.read())
        except (URLError, OSError, TimeoutError, json.JSONDecodeError) as e:
            raise GroqClientError(f"Groq API error: {e}") from e

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise GroqClientError(f"Unexpected Groq response shape: {data}") from e

        if not content:
            raise GroqClientError("Groq returned an empty response")

        return content


# Module-level singleton, same pattern as gemini_client.
groq_client = GroqClient()
