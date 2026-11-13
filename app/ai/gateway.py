"""
AI Gateway - an ordered cascade across several FREE LLM providers, then
(in the callers) the deterministic rule-engine fallback.

Why this exists: no single free tier is reliable (limits change without
notice, daily caps, model IDs retire). So the app never depends on one
vendor: it walks AI_PROVIDER_ORDER, skips providers with no key, skips
providers that just rate-limited us (cooldown), and returns the first
success. Gemini is just one optional entry in the list now, not a
requirement. Self-hosted models (`local`) are first-class too.

Every attempt is logged (app/storage/ai_usage_store.py) - that log is
also the raw data for the research paper's reliability/latency tables.
"""

import logging
import threading
import time
from typing import Callable

from app.ai.gemini_client import GeminiClientError, gemini_client
from app.ai.providers import COMPAT_PROVIDERS, ProviderError
from app.config import settings
from app.storage.ai_usage_store import log_attempt

logger = logging.getLogger(__name__)

_DEFAULT_COOLDOWN_SECONDS = 60.0
_cooldown_until: dict[str, float] = {}
_lock = threading.Lock()


class AIGatewayError(Exception):
    """Every configured provider failed (or none are configured)."""


def _cooling(name: str) -> bool:
    with _lock:
        return _cooldown_until.get(name, 0.0) > time.monotonic()


def _start_cooldown(name: str, seconds: float | None) -> None:
    with _lock:
        _cooldown_until[name] = time.monotonic() + min(seconds or _DEFAULT_COOLDOWN_SECONDS, 600.0)


def reset_cooldowns() -> None:
    """Used by tests."""
    with _lock:
        _cooldown_until.clear()


def configured_providers(vision: bool = False) -> list[str]:
    """Provider names, in order, that are usable right now."""
    names = []
    for name in settings.AI_PROVIDER_ORDER:
        if name == "gemini":
            if settings.GEMINI_API_KEY:
                names.append(name)
        elif name in COMPAT_PROVIDERS:
            p = COMPAT_PROVIDERS[name]
            if (p.vision_configured() if vision else p.configured()):
                names.append(name)
    return names


def _call(name: str, text_fn: Callable, image_args: tuple | None, system_prompt: str, user_prompt: str) -> str:
    if name == "gemini":
        if image_args:
            return gemini_client.generate_with_image(system_prompt, user_prompt, *image_args)
        return gemini_client.generate(system_prompt, user_prompt)
    provider = COMPAT_PROVIDERS[name]
    if image_args:
        return provider.generate_with_image(system_prompt, user_prompt, *image_args)
    return provider.generate(system_prompt, user_prompt)


def _run(system_prompt: str, user_prompt: str, image_args: tuple | None) -> str:
    errors: list[str] = []
    for name in configured_providers(vision=image_args is not None):
        if _cooling(name):
            errors.append(f"{name}: cooling down")
            continue
        start = time.monotonic()
        try:
            result = _call(name, None, image_args, system_prompt, user_prompt)
            log_attempt(name, True, int((time.monotonic() - start) * 1000))
            return result
        except (ProviderError, GeminiClientError) as e:
            log_attempt(name, False, int((time.monotonic() - start) * 1000))
            msg = str(e)
            limited = getattr(e, "rate_limited", False) or "429" in msg or "RESOURCE_EXHAUSTED" in msg
            if limited:
                _start_cooldown(name, getattr(e, "retry_after", None))
            logger.warning("AI gateway: %s failed (%s), trying next provider", name, msg[:200])
            errors.append(f"{name}: {msg[:120]}")
    log_attempt("all_failed", False, None)
    raise AIGatewayError(
        "All AI providers failed: " + ("; ".join(errors) if errors else "none configured")
    )


def generate(system_prompt: str, user_prompt: str) -> str:
    return _run(system_prompt, user_prompt, None)


def generate_with_image(
    system_prompt: str, user_prompt: str, image_bytes: bytes, mime_type: str
) -> str:
    return _run(system_prompt, user_prompt, (image_bytes, mime_type))
