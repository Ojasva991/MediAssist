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


PASSPORT_PAYLOAD = {
    "name": "Priya Sharma",
    "age": 41,
    "gender": "Female",
    "blood_group": "O+",
    "allergies": "Penicillin",
    "medications": "None",
    "chronic_diseases": "Asthma",
    "emergency_contact_name": "Raj Sharma",
    "emergency_contact_phone": "+91-9876543210",
}


def test_analyze_uses_saved_passport_when_age_gender_omitted(client, monkeypatch, make_user):
    """The whole point of the passport-first flow: a logged-in user with a
    saved passport shouldn't have to send age/gender/existing_conditions at
    all - they should be pulled from the passport automatically."""
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
    client.put(f"/passport/{user_id}", json=PASSPORT_PAYLOAD, headers=headers)

    minimal_payload = {"symptoms": "Mild headache", "duration": "3 hours"}
    resp = client.post("/analyze", json=minimal_payload, headers=headers)
    assert resp.status_code == 200

    history_resp = client.get(f"/history/{user_id}", headers=headers)
    entry = history_resp.json()[0]
    assert entry["age"] == 41
    assert entry["gender"] == "Female"
    assert entry["existing_conditions"] == "Asthma"


def test_analyze_request_values_override_saved_passport(client, monkeypatch, make_user):
    """Explicit values in the request (e.g. checking symptoms on behalf of
    someone else) should win over whatever's saved in the caller's own
    passport."""
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
    client.put(f"/passport/{user_id}", json=PASSPORT_PAYLOAD, headers=headers)

    override_payload = {**VALID_PAYLOAD, "age": 5, "gender": "Male"}
    client.post("/analyze", json=override_payload, headers=headers)

    history_resp = client.get(f"/history/{user_id}", headers=headers)
    entry = history_resp.json()[0]
    assert entry["age"] == 5
    assert entry["gender"] == "Male"


def test_analyze_requires_age_gender_without_a_saved_passport(client, monkeypatch, make_user):
    """A logged-in user with no passport yet, and an anonymous caller, are
    the same case here: with nowhere to pull age/gender from, they must be
    provided directly or the request is rejected with a clear message."""
    _mock_gemini_success(
        monkeypatch,
        {
            "possible_conditions": [],
            "severity": "LOW",
            "recommended_action": "n/a",
            "sos_recommended": False,
            "disclaimer": "n/a",
        },
    )
    headers, _user_id, _ = make_user()  # no passport saved for this user
    minimal_payload = {"symptoms": "Mild headache", "duration": "3 hours"}

    resp = client.post("/analyze", json=minimal_payload, headers=headers)
    assert resp.status_code == 400
    assert "health passport" in resp.json()["detail"].lower()

    anon_resp = client.post("/analyze", json=minimal_payload)
    assert anon_resp.status_code == 400
