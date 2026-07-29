import app.ai.gateway as gateway
from app.ai.gateway import AIGatewayError, generate
from app.ai.gemini_client import GeminiClientError
from app.ai.groq_client import GroqClientError
from app.config import settings


def test_uses_gemini_when_it_succeeds(monkeypatch):
    monkeypatch.setattr(
        gateway.gemini_client, "generate", lambda sp, up: "gemini response"
    )
    assert generate("system", "user") == "gemini response"


def test_falls_back_to_groq_when_gemini_fails_and_groq_is_configured(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-groq-key")

    def gemini_fails(sp, up):
        raise GeminiClientError("Gemini is down")

    monkeypatch.setattr(gateway.gemini_client, "generate", gemini_fails)
    monkeypatch.setattr(gateway.groq_client, "generate", lambda sp, up: "groq response")

    assert generate("system", "user") == "groq response"


def test_skips_groq_entirely_when_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")

    def gemini_fails(sp, up):
        raise GeminiClientError("Gemini is down")

    def groq_should_not_be_called(sp, up):
        raise AssertionError("Groq should not have been called when GROQ_API_KEY is unset")

    monkeypatch.setattr(gateway.gemini_client, "generate", gemini_fails)
    monkeypatch.setattr(gateway.groq_client, "generate", groq_should_not_be_called)

    try:
        generate("system", "user")
        assert False, "expected AIGatewayError"
    except AIGatewayError as e:
        assert "Gemini" in str(e)


def test_raises_gateway_error_when_all_configured_providers_fail(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-groq-key")

    def gemini_fails(sp, up):
        raise GeminiClientError("Gemini is down")

    def groq_fails(sp, up):
        raise GroqClientError("Groq is down")

    monkeypatch.setattr(gateway.gemini_client, "generate", gemini_fails)
    monkeypatch.setattr(gateway.groq_client, "generate", groq_fails)

    try:
        generate("system", "user")
        assert False, "expected AIGatewayError"
    except AIGatewayError as e:
        assert "Gemini" in str(e)
        assert "Groq" in str(e)


def test_gemini_success_means_groq_is_never_called(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-groq-key")

    def groq_should_not_be_called(sp, up):
        raise AssertionError("Groq should not have been called - Gemini already succeeded")

    monkeypatch.setattr(gateway.gemini_client, "generate", lambda sp, up: "gemini response")
    monkeypatch.setattr(gateway.groq_client, "generate", groq_should_not_be_called)

    assert generate("system", "user") == "gemini response"
