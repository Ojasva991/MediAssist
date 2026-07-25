import json


def _mock_gemini_success(monkeypatch, response_dict):
    monkeypatch.setattr(
        "app.ai.triage_service.gemini_client.generate",
        lambda system_prompt, user_prompt: json.dumps(response_dict),
    )


_SUCCESS_RESPONSE = {
    "possible_conditions": ["Tension headache"],
    "severity": "LOW",
    "recommended_action": "Rest and hydrate.",
    "sos_recommended": False,
    "disclaimer": "This is not a medical diagnosis.",
}

_ANALYZE_PAYLOAD = {"age": 28, "gender": "Male", "symptoms": "Mild headache", "duration": "3 hours"}


def _run_analysis(client, headers, monkeypatch):
    _mock_gemini_success(monkeypatch, _SUCCESS_RESPONSE)
    resp = client.post("/analyze", json=_ANALYZE_PAYLOAD, headers=headers)
    assert resp.status_code == 200
    return resp.json()


def test_analyze_response_includes_history_id_when_logged_in(client, monkeypatch, make_user):
    headers, _user_id, _ = make_user()
    body = _run_analysis(client, headers, monkeypatch)
    assert isinstance(body["history_id"], int)


def test_analyze_response_has_no_history_id_when_anonymous(client, monkeypatch):
    _mock_gemini_success(monkeypatch, _SUCCESS_RESPONSE)
    resp = client.post("/analyze", json=_ANALYZE_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["history_id"] is None


def test_submit_feedback_requires_authentication(client):
    resp = client.post("/history/some-user-id/1/feedback", json={"is_helpful": True})
    assert resp.status_code == 401


def test_submit_feedback_success_and_reflected_in_history(client, monkeypatch, make_user):
    headers, user_id, _ = make_user()
    body = _run_analysis(client, headers, monkeypatch)
    history_id = body["history_id"]

    resp = client.post(
        f"/history/{user_id}/{history_id}/feedback",
        json={"is_helpful": True},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "recorded", "history_id": history_id, "is_helpful": True}

    history_resp = client.get(f"/history/{user_id}", headers=headers)
    entry = history_resp.json()[0]
    assert entry["id"] == history_id
    assert entry["feedback"] is True


def test_submit_feedback_can_be_changed(client, monkeypatch, make_user):
    headers, user_id, _ = make_user()
    body = _run_analysis(client, headers, monkeypatch)
    history_id = body["history_id"]

    client.post(f"/history/{user_id}/{history_id}/feedback", json={"is_helpful": True}, headers=headers)
    client.post(f"/history/{user_id}/{history_id}/feedback", json={"is_helpful": False}, headers=headers)

    history_resp = client.get(f"/history/{user_id}", headers=headers)
    entry = history_resp.json()[0]
    assert entry["feedback"] is False


def test_feedback_on_nonexistent_analysis_returns_404(client, make_user):
    headers, user_id, _ = make_user()
    resp = client.post(
        f"/history/{user_id}/999999/feedback", json={"is_helpful": True}, headers=headers
    )
    assert resp.status_code == 404


def test_cannot_submit_feedback_on_another_users_analysis(client, monkeypatch, make_user):
    headers_a, user_id_a, _ = make_user()
    headers_b, user_id_b, _ = make_user()
    body = _run_analysis(client, headers_a, monkeypatch)
    history_id = body["history_id"]

    # user B tries to leave feedback using their own user_id in the URL,
    # but referencing user A's history_id.
    resp = client.post(
        f"/history/{user_id_b}/{history_id}/feedback",
        json={"is_helpful": True},
        headers=headers_b,
    )
    assert resp.status_code == 403

    # Also try the URL-mismatch path directly (user_id in URL doesn't
    # match the caller's own token).
    resp2 = client.post(
        f"/history/{user_id_a}/{history_id}/feedback",
        json={"is_helpful": True},
        headers=headers_b,
    )
    assert resp2.status_code == 403


def test_history_entries_without_feedback_show_null(client, monkeypatch, make_user):
    headers, user_id, _ = make_user()
    _run_analysis(client, headers, monkeypatch)

    history_resp = client.get(f"/history/{user_id}", headers=headers)
    assert history_resp.json()[0]["feedback"] is None


def test_trends_route_requires_authentication(client):
    resp = client.get("/history/some-user-id/trends")
    assert resp.status_code == 401


def test_trends_route_returns_empty_for_new_user(client, make_user):
    headers, user_id, _ = make_user()
    resp = client.get(f"/history/{user_id}/trends", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_trends_route_detects_recurring_symptom(client, monkeypatch, make_user):
    headers, user_id, _ = make_user()
    for _ in range(3):
        _mock_gemini_success(monkeypatch, _SUCCESS_RESPONSE)
        payload = {**_ANALYZE_PAYLOAD, "symptoms": "Persistent headache again"}
        resp = client.post("/analyze", json=payload, headers=headers)
        assert resp.status_code == 200

    resp = client.get(f"/history/{user_id}/trends", headers=headers)
    assert resp.status_code == 200
    keywords = {f["keyword"] for f in resp.json()}
    assert "headache" in keywords


def test_cannot_view_another_users_trends(client, make_user):
    headers_a, user_id_a, _ = make_user()
    headers_b, _user_id_b, _ = make_user()
    resp = client.get(f"/history/{user_id_a}/trends", headers=headers_b)
    assert resp.status_code == 403
