import json
from contextlib import contextmanager
from urllib.error import URLError

import app.ai.groq_client as groq_client_module
from app.ai.groq_client import GroqClient, GroqClientError
from app.config import settings


def test_raises_when_api_key_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    client = GroqClient()
    try:
        client.generate("system", "user")
        assert False, "expected GroqClientError"
    except GroqClientError as e:
        assert "not configured" in str(e)


def _fake_urlopen_returning(payload_dict):
    @contextmanager
    def _fake(request, timeout=30):
        class FakeResponse:
            def read(self):
                return json.dumps(payload_dict).encode()

        yield FakeResponse()

    return _fake


def test_success_returns_message_content(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        groq_client_module,
        "urlopen",
        _fake_urlopen_returning({"choices": [{"message": {"content": '{"result": "ok"}'}}]}),
    )
    client = GroqClient()
    assert client.generate("system", "user") == '{"result": "ok"}'


def test_raises_on_network_error(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")

    def raise_network_error(request, timeout=30):
        raise URLError("connection refused")

    monkeypatch.setattr(groq_client_module, "urlopen", raise_network_error)
    client = GroqClient()
    try:
        client.generate("system", "user")
        assert False, "expected GroqClientError"
    except GroqClientError as e:
        assert "Groq API error" in str(e)


def test_raises_on_unexpected_response_shape(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        groq_client_module, "urlopen", _fake_urlopen_returning({"unexpected": "shape"})
    )
    client = GroqClient()
    try:
        client.generate("system", "user")
        assert False, "expected GroqClientError"
    except GroqClientError as e:
        assert "Unexpected Groq response shape" in str(e)


def test_raises_on_empty_content(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        groq_client_module,
        "urlopen",
        _fake_urlopen_returning({"choices": [{"message": {"content": ""}}]}),
    )
    client = GroqClient()
    try:
        client.generate("system", "user")
        assert False, "expected GroqClientError"
    except GroqClientError as e:
        assert "empty response" in str(e)
