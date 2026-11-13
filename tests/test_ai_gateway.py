import pytest

import app.ai.gateway as gateway
from app.ai.gateway import AIGatewayError, generate, generate_with_image
from app.ai.gemini_client import GeminiClientError
from app.ai.providers import COMPAT_PROVIDERS, ProviderError
from app.config import settings


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    gateway.reset_cooldowns()
    # Start every test with NO optional provider keys; each test opts in.
    for key in ("GROQ_API_KEY", "CEREBRAS_API_KEY", "MISTRAL_API_KEY", "OPENROUTER_API_KEY",
                "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID", "LOCAL_LLM_BASE_URL", "LOCAL_LLM_MODEL"):
        monkeypatch.setattr(settings, key, "")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setattr(settings, "AI_PROVIDER_ORDER", ["groq", "cerebras", "gemini"])
    yield
    gateway.reset_cooldowns()


def _fake(monkeypatch, name, fn):
    monkeypatch.setattr(COMPAT_PROVIDERS[name].__class__, "generate",
                        lambda self, sp, up: fn(self.name), raising=True)


def test_gemini_only_still_works(monkeypatch):
    monkeypatch.setattr(gateway.gemini_client, "generate", lambda sp, up: "gemini ok")
    assert generate("s", "u") == "gemini ok"


def test_works_with_no_gemini_key_at_all(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "k")
    _fake(monkeypatch, "groq", lambda n: f"{n} ok")
    assert generate("s", "u") == "groq ok"


def test_falls_through_providers_in_order(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "k")
    monkeypatch.setattr(settings, "CEREBRAS_API_KEY", "k")
    calls = []

    def fn(name):
        calls.append(name)
        if name == "groq":
            raise ProviderError("groq HTTP 500")
        return f"{name} ok"

    _fake(monkeypatch, "groq", fn)
    assert generate("s", "u") == "cerebras ok"
    assert calls == ["groq", "cerebras"]


def test_unconfigured_providers_are_skipped(monkeypatch):
    def boom(name):
        raise AssertionError(f"{name} must not be called without a key")

    _fake(monkeypatch, "groq", boom)
    monkeypatch.setattr(gateway.gemini_client, "generate", lambda sp, up: "gemini ok")
    assert generate("s", "u") == "gemini ok"


def test_rate_limited_provider_enters_cooldown(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "k")
    monkeypatch.setattr(gateway.gemini_client, "generate", lambda sp, up: "gemini ok")
    calls = []

    def fn(name):
        calls.append(name)
        raise ProviderError("groq HTTP 429", rate_limited=True, retry_after=30)

    _fake(monkeypatch, "groq", fn)
    assert generate("s", "u") == "gemini ok"
    assert generate("s", "u") == "gemini ok"
    assert calls == ["groq"]  # second request skipped groq while cooling down


def test_raises_when_everything_fails(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "k")
    _fake(monkeypatch, "groq", lambda n: (_ for _ in ()).throw(ProviderError("groq down")))

    def gemini_fails(sp, up):
        raise GeminiClientError("gemini down")

    monkeypatch.setattr(gateway.gemini_client, "generate", gemini_fails)
    with pytest.raises(AIGatewayError) as e:
        generate("s", "u")
    assert "groq" in str(e.value) and "gemini" in str(e.value)


def test_raises_cleanly_when_nothing_configured(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    with pytest.raises(AIGatewayError):
        generate("s", "u")


def test_image_path_only_uses_vision_capable_providers(monkeypatch):
    monkeypatch.setattr(settings, "CEREBRAS_API_KEY", "k")  # no vision model on cerebras
    monkeypatch.setattr(gateway.gemini_client, "generate_with_image",
                        lambda sp, up, b, m: "gemini vision ok")
    assert generate_with_image("s", "u", b"img", "image/png") == "gemini vision ok"
    assert gateway.configured_providers(vision=True) == ["gemini"]


def test_client_ip_uses_right_side_of_forwarded_for(monkeypatch):
    from app.rate_limit import client_ip

    class Req:
        headers = {"x-forwarded-for": "6.6.6.6, 203.0.113.9"}  # first entry is client-forged
        client = type("C", (), {"host": "10.0.0.1"})()

    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 1)
    assert client_ip(Req()) == "203.0.113.9"
