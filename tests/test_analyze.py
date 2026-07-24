import json

from app.ai.gemini_client import GeminiClientError

VALID_PAYLOAD = {
    "age": 28,
    "gender": "Male",
    "symptoms": "Mild headache since this morning",
    "duration": "3 hours",
    "existing_conditions": None,
}


def _mock_gemini_success(monkeypatch, response_dict):
    monkeypatch.setattr(
        "app.ai.triage_service.gemini_client.generate",
        lambda system_prompt, user_prompt: json.dumps(response_dict),
    )


def _mock_gemini_failure(monkeypatch):
    def _raise(*args, **kwargs):
        raise GeminiClientError("simulated Gemini outage")

    monkeypatch.setattr("app.ai.triage_service.gemini_client.generate", _raise)


def test_analyze_rejects_invalid_payload(client):
    bad_payload = {**VALID_PAYLOAD, "age": -5}
    resp = client.post("/analyze", json=bad_payload)
    assert resp.status_code == 422


def test_analyze_rejects_blank_symptoms(client):
    bad_payload = {**VALID_PAYLOAD, "symptoms": "   "}
    resp = client.post("/analyze", json=bad_payload)
    assert resp.status_code == 422


def test_analyze_works_without_authentication(client, monkeypatch):
    _mock_gemini_success(
        monkeypatch,
        {
            "possible_conditions": ["Tension headache"],
            "severity": "LOW",
            "recommended_action": "Rest and stay hydrated. See a doctor if it worsens.",
            "sos_recommended": False,
            "disclaimer": "This is not a medical diagnosis.",
        },
    )
    resp = client.post("/analyze", json=VALID_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["severity"] == "LOW"
    assert body["possible_conditions"] == ["Tension headache"]
    assert body["disclaimer"]


def test_analyze_falls_back_when_gemini_unavailable(client, monkeypatch):
    _mock_gemini_failure(monkeypatch)
    resp = client.post("/analyze", json=VALID_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    # Fallback responses never claim a diagnosis - possible_conditions is
    # always empty so the frontend/reviewer can tell it apart from a real
    # AI analysis.
    assert body["possible_conditions"] == []
    assert "unavailable" in body["disclaimer"].lower() or "unavailable" in body["recommended_action"].lower()


def test_analyze_fallback_escalates_on_red_flag_symptoms(client, monkeypatch):
    _mock_gemini_failure(monkeypatch)
    payload = {**VALID_PAYLOAD, "symptoms": "Sudden chest pain and shortness of breath"}
    resp = client.post("/analyze", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["severity"] == "EMERGENCY"
    assert body["sos_recommended"] is True


def test_analyze_never_returns_wrong_country_emergency_number(client, monkeypatch):
    _mock_gemini_success(
        monkeypatch,
        {
            "possible_conditions": ["Possible cardiac event"],
            "severity": "EMERGENCY",
            "recommended_action": "This is serious - call 911 immediately.",
            "sos_recommended": True,
            "disclaimer": "This is not a medical diagnosis.",
        },
    )
    resp = client.post("/analyze", json=VALID_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert "911" not in body["recommended_action"]
    assert "local emergency number" in body["recommended_action"].lower()


def test_analyze_saves_history_when_logged_in(client, monkeypatch, make_user):
    _mock_gemini_success(
        monkeypatch,
        {
            "possible_conditions": ["Tension headache"],
            "severity": "LOW",
            "recommended_action": "Rest and stay hydrated.",
            "sos_recommended": False,
            "disclaimer": "This is not a medical diagnosis.",
        },
    )
    headers, user_id, _ = make_user()
    resp = client.post("/analyze", json=VALID_PAYLOAD, headers=headers)
    assert resp.status_code == 200

    history_resp = client.get(f"/history/{user_id}", headers=headers)
    assert history_resp.status_code == 200
    entries = history_resp.json()
    assert len(entries) == 1
    assert entries[0]["symptoms"] == VALID_PAYLOAD["symptoms"]
    assert entries[0]["severity"] == "LOW"


def test_analyze_logged_out_saves_no_history(client, monkeypatch, make_user):
    _mock_gemini_success(
        monkeypatch,
        {
            "possible_conditions": ["Tension headache"],
            "severity": "LOW",
            "recommended_action": "Rest and stay hydrated.",
            "sos_recommended": False,
            "disclaimer": "This is not a medical diagnosis.",
        },
    )
    headers, user_id, _ = make_user()
    # Analyze WITHOUT the auth header this time.
    client.post("/analyze", json=VALID_PAYLOAD)

    history_resp = client.get(f"/history/{user_id}", headers=headers)
    assert history_resp.status_code == 200
    assert history_resp.json() == []
