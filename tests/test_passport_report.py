import json

PASSPORT_PAYLOAD = {
    "name": "Priya Sharma",
    "age": 24,
    "gender": "Female",
    "blood_group": "O+",
    "allergies": "Penicillin",
    "medications": "None",
    "chronic_diseases": "Asthma",
    "emergency_contact_name": "Raj Sharma",
    "emergency_contact_phone": "+91-9876543210",
}


def _mock_gemini_success(monkeypatch, response_dict):
    monkeypatch.setattr(
        "app.ai.triage_service.gemini_client.generate",
        lambda system_prompt, user_prompt: json.dumps(response_dict),
    )


def test_report_requires_authentication(client):
    resp = client.get("/passport/some-user-id/report")
    assert resp.status_code == 401


def test_report_404s_without_a_saved_passport(client, make_user):
    headers, user_id, _ = make_user()
    resp = client.get(f"/passport/{user_id}/report", headers=headers)
    assert resp.status_code == 404


def test_cannot_download_another_users_report(client, make_user):
    headers_a, user_id_a, _ = make_user()
    headers_b, _user_id_b, _ = make_user()
    client.put(f"/passport/{user_id_a}", json=PASSPORT_PAYLOAD, headers=headers_a)

    resp = client.get(f"/passport/{user_id_a}/report", headers=headers_b)
    assert resp.status_code == 403


def test_report_generates_a_valid_pdf(client, make_user):
    headers, user_id, _ = make_user()
    client.put(f"/passport/{user_id}", json=PASSPORT_PAYLOAD, headers=headers)

    resp = client.get(f"/passport/{user_id}/report", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "attachment" in resp.headers["content-disposition"]
    # A real PDF starts with this magic header - confirms fpdf2 actually
    # produced a valid file, not just some bytes.
    assert resp.content[:5] == b"%PDF-"


def test_report_includes_recent_analysis_when_present(client, monkeypatch, make_user):
    headers, user_id, _ = make_user()
    client.put(f"/passport/{user_id}", json=PASSPORT_PAYLOAD, headers=headers)

    _mock_gemini_success(
        monkeypatch,
        {
            "possible_conditions": ["Tension headache"],
            "severity": "LOW",
            "recommended_action": "Rest and hydrate.",
            "sos_recommended": False,
            "disclaimer": "This is not a medical diagnosis.",
        },
    )
    analyze_payload = {"symptoms": "Mild headache", "duration": "3 hours"}
    client.post("/analyze", json=analyze_payload, headers=headers)

    resp = client.get(f"/passport/{user_id}/report", headers=headers)
    assert resp.status_code == 200
    assert resp.content[:5] == b"%PDF-"
    # A rough sanity check that the report isn't trivially tiny (i.e.
    # the history section actually rendered something).
    assert len(resp.content) > 1000
