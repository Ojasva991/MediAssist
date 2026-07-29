import json

from app.ai.gateway import AIGatewayError


def _mock_gateway_success(monkeypatch, response_dict):
    monkeypatch.setattr(
        "app.ai.triage_service.ai_gateway_generate",
        lambda system_prompt, user_prompt: json.dumps(response_dict),
    )


def _mock_gateway_failure(monkeypatch):
    def _raise(system_prompt, user_prompt):
        raise AIGatewayError("simulated: all providers failed")

    monkeypatch.setattr("app.ai.triage_service.ai_gateway_generate", _raise)


def _payload(**overrides):
    base = {
        "original_symptoms": "mild headache",
        "conversation": [],
        "message": "should I be worried?",
    }
    base.update(overrides)
    return base


def test_requires_at_least_a_message(client):
    resp = client.post(
        "/analyze/follow-up",
        json={"original_symptoms": "headache", "conversation": [], "message": ""},
    )
    assert resp.status_code == 422


def test_returns_ai_reply_on_success(client, monkeypatch):
    _mock_gateway_success(
        monkeypatch,
        {
            "reply": "A mild headache alone is usually not concerning.",
            "severity": "LOW",
            "escalation_detected": False,
            "sos_recommended": False,
            "disclaimer": "This is not a medical diagnosis.",
        },
    )
    resp = client.post("/analyze/follow-up", json=_payload())
    assert resp.status_code == 200
    body = resp.json()
    assert body["severity"] == "LOW"
    assert body["escalation_detected"] is False


def test_rule_engine_floor_overrides_llm_when_new_message_has_red_flags(client, monkeypatch):
    # AI says LOW, but the new message describes something the rule
    # engine treats as an emergency - the floor must win, and
    # escalation_detected must flip to True regardless of what the AI said.
    _mock_gateway_success(
        monkeypatch,
        {
            "reply": "That sounds manageable.",
            "severity": "LOW",
            "escalation_detected": False,
            "sos_recommended": False,
            "disclaimer": "This is not a medical diagnosis.",
        },
    )
    resp = client.post(
        "/analyze/follow-up",
        json=_payload(message="now I also have severe chest pain and difficulty breathing"),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["severity"] == "EMERGENCY"
    assert body["escalation_detected"] is True
    assert body["sos_recommended"] is True


def test_rule_engine_checks_full_conversation_not_just_latest_message(client, monkeypatch):
    # The red flag is in an EARLIER user turn, not the latest message -
    # the floor should still catch it since the whole conversation is
    # re-evaluated every time.
    _mock_gateway_success(
        monkeypatch,
        {
            "reply": "Understood.",
            "severity": "LOW",
            "escalation_detected": False,
            "sos_recommended": False,
            "disclaimer": "This is not a medical diagnosis.",
        },
    )
    resp = client.post(
        "/analyze/follow-up",
        json=_payload(
            conversation=[
                {"role": "user", "content": "I also have crushing chest pain radiating to my arm"},
                {"role": "assistant", "content": "That sounds serious."},
            ],
            message="ok, thanks",
        ),
    )
    assert resp.status_code == 200
    assert resp.json()["severity"] == "EMERGENCY"


def test_falls_back_safely_when_all_ai_providers_fail(client, monkeypatch):
    _mock_gateway_failure(monkeypatch)
    resp = client.post("/analyze/follow-up", json=_payload())
    assert resp.status_code == 200
    body = resp.json()
    assert "trouble processing" in body["reply"].lower()
    assert body["severity"] == "LOW"  # rule engine floor for a mild headache alone


def test_falls_back_with_urgent_wording_when_rule_engine_floor_is_high(client, monkeypatch):
    _mock_gateway_failure(monkeypatch)
    resp = client.post(
        "/analyze/follow-up",
        json=_payload(message="severe chest pain and difficulty breathing"),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["sos_recommended"] is True
    assert "urgent" in body["reply"].lower() or "sos" in body["reply"].lower()


def test_emergency_number_scrubbed_from_reply(client, monkeypatch):
    _mock_gateway_success(
        monkeypatch,
        {
            "reply": "This is serious - call 911 immediately.",
            "severity": "EMERGENCY",
            "escalation_detected": True,
            "sos_recommended": True,
            "disclaimer": "This is not a medical diagnosis.",
        },
    )
    resp = client.post("/analyze/follow-up", json=_payload())
    assert resp.status_code == 200
    assert "911" not in resp.json()["reply"]


def test_works_without_authentication(client, monkeypatch):
    _mock_gateway_success(
        monkeypatch,
        {
            "reply": "Should be fine.",
            "severity": "LOW",
            "escalation_detected": False,
            "sos_recommended": False,
            "disclaimer": "This is not a medical diagnosis.",
        },
    )
    resp = client.post("/analyze/follow-up", json=_payload())
    assert resp.status_code == 200
