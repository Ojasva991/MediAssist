"""
Generic client for any OpenAI-compatible chat-completions API.

Groq, Cerebras, Mistral, OpenRouter, Cloudflare Workers AI and a
self-hosted server (Ollama / llama.cpp / vLLM all expose the same
`/v1/chat/completions` shape) are all reached through this one class,
so adding a provider is a config entry, not a new client module.

Plain urllib on purpose (same "no new dependency" rule as the rest of
this project). Every provider's settings are read from `settings` at
CALL time, not import time, so env changes and test monkeypatching work.
"""

import base64
import json
import logging
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    """Any failure talking to an OpenAI-compatible provider."""

    def __init__(self, message: str, *, rate_limited: bool = False, retry_after: float | None = None):
        super().__init__(message)
        self.rate_limited = rate_limited
        self.retry_after = retry_after


@dataclass(frozen=True)
class CompatProvider:
    name: str
    base_url: Callable[[], str]
    api_key: Callable[[], str]
    model: Callable[[], str]
    vision_model: Callable[[], str]
    # Some local servers (Ollama) need no key; hosted ones always do.
    key_required: bool = True

    def configured(self) -> bool:
        if not self.base_url() or not self.model():
            return False
        return bool(self.api_key()) or not self.key_required

    def vision_configured(self) -> bool:
        return self.configured() and bool(self.vision_model())

    # -----------------------------------------------------------------
    def _post(self, payload: dict) -> str:
        headers = {"Content-Type": "application/json", "User-Agent": "vaeda-ai/1.0"}
        if self.api_key():
            headers["Authorization"] = f"Bearer {self.api_key()}"
        if self.name == "openrouter":
            headers["X-Title"] = settings.APP_NAME
        url = self.base_url().rstrip("/") + "/chat/completions"
        request = Request(url, data=json.dumps(payload).encode(), headers=headers)
        try:
            with urlopen(request, timeout=settings.AI_TIMEOUT_SECONDS) as response:
                data = json.loads(response.read())
        except HTTPError as e:
            retry_after = None
            try:
                retry_after = float(e.headers.get("Retry-After", ""))
            except (TypeError, ValueError):
                pass
            raise ProviderError(
                f"{self.name} HTTP {e.code}",
                rate_limited=e.code == 429,
                retry_after=retry_after,
            ) from e
        except (URLError, OSError, TimeoutError, json.JSONDecodeError) as e:
            raise ProviderError(f"{self.name} network/parse error: {e}") from e

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderError(f"{self.name} unexpected response shape") from e
        if not content:
            raise ProviderError(f"{self.name} returned an empty response")
        return content

    def _chat(self, model: str, messages: list[dict]) -> str:
        payload = {"model": model, "messages": messages, "temperature": 0.2}
        # JSON mode is requested first, but not every model/provider
        # supports it - on a 400/422 retry once without it. The caller
        # parses defensively either way (see triage_service).
        try:
            return self._post({**payload, "response_format": {"type": "json_object"}})
        except ProviderError as e:
            if "HTTP 400" in str(e) or "HTTP 422" in str(e):
                return self._post(payload)
            raise

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return self._chat(
            self.model(),
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

    def generate_with_image(
        self, system_prompt: str, user_prompt: str, image_bytes: bytes, mime_type: str
    ) -> str:
        data_uri = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode()}"
        return self._chat(
            self.vision_model(),
            [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                },
            ],
        )


def _cloudflare_base() -> str:
    if not settings.CLOUDFLARE_ACCOUNT_ID:
        return ""
    return f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/ai/v1"


# Registry. Keys are the names usable in AI_PROVIDER_ORDER.
COMPAT_PROVIDERS: dict[str, CompatProvider] = {
    "groq": CompatProvider(
        "groq",
        lambda: "https://api.groq.com/openai/v1",
        lambda: settings.GROQ_API_KEY,
        lambda: settings.GROQ_MODEL,
        lambda: settings.GROQ_VISION_MODEL,
    ),
    "cerebras": CompatProvider(
        "cerebras",
        lambda: "https://api.cerebras.ai/v1",
        lambda: settings.CEREBRAS_API_KEY,
        lambda: settings.CEREBRAS_MODEL,
        lambda: "",  # no vision on this provider
    ),
    "mistral": CompatProvider(
        "mistral",
        lambda: "https://api.mistral.ai/v1",
        lambda: settings.MISTRAL_API_KEY,
        lambda: settings.MISTRAL_MODEL,
        lambda: settings.MISTRAL_VISION_MODEL,
    ),
    "openrouter": CompatProvider(
        "openrouter",
        lambda: "https://openrouter.ai/api/v1",
        lambda: settings.OPENROUTER_API_KEY,
        lambda: settings.OPENROUTER_MODEL,
        lambda: settings.OPENROUTER_VISION_MODEL,
    ),
    "cloudflare": CompatProvider(
        "cloudflare",
        _cloudflare_base,
        lambda: settings.CLOUDFLARE_API_TOKEN,
        lambda: settings.CLOUDFLARE_MODEL,
        lambda: "",
    ),
    # Self-hosted / local model (Ollama, llama.cpp server, vLLM, LM Studio).
    "local": CompatProvider(
        "local",
        lambda: settings.LOCAL_LLM_BASE_URL,
        lambda: settings.LOCAL_LLM_API_KEY,
        lambda: settings.LOCAL_LLM_MODEL,
        lambda: settings.LOCAL_LLM_VISION_MODEL,
        key_required=False,
    ),
}
