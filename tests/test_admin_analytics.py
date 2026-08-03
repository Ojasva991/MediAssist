import json

from app.config import settings


def test_requires_authentication(client):
    resp = client.get("/admin/analytics")
    assert resp.status_code == 401


def test_rejects_non_admin_user(client, make_user):
    headers, _, _ = make_user()
    resp = client.get("/admin/analytics", headers=headers)
    assert resp.status_code == 403


def test_admin_can_view_analytics(client, make_user, monkeypatch):
    headers, user_id, _ = make_user()
    monkeypatch.setattr(settings, "ADMIN_USER_IDS", [user_id])

    resp = client.get("/admin/analytics", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "total_users" in body
    assert "severity_breakdown" in body
    assert "ai_provider_stats" in body


def test_total_users_reflects_real_signups(client, make_user, monkeypatch):
    headers, user_id, _ = make_user()
    monkeypatch.setattr(settings, "ADMIN_USER_IDS", [user_id])
    make_user()
    make_user()

    resp = client.get("/admin/analytics", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total_users"] >= 3


def test_analysis_counts_reflect_saved_history(client, make_user, monkeypatch):
    headers, user_id, _ = make_user()
    monkeypatch.setattr(settings, "ADMIN_USER_IDS", [user_id])
    monkeypatch.setattr(
        "app.ai.triage_service.ai_gateway_generate",
        lambda system_prompt, user_prompt: json.dumps(
            {
                "possible_conditions": ["Common cold"],
                "severity": "LOW",
                "recommended_action": "Rest and fluids.",
                "sos_recommended": False,
                "disclaimer": "This is not a medical diagnosis.",
            }
        ),
    )
    client.post(
        "/analyze",
        headers=headers,
        json={"age": 30, "gender": "Female", "symptoms": "mild cough", "duration": "2 days"},
    )

    resp = client.get("/admin/analytics", headers=headers)
    body = resp.json()
    assert body["total_analyses"] >= 1
    assert body["severity_breakdown"]["LOW"] >= 1


def test_ai_provider_stats_shape_and_scope_note(client, make_user, monkeypatch):
    headers, user_id, _ = make_user()
    monkeypatch.setattr(settings, "ADMIN_USER_IDS", [user_id])

    resp = client.get("/admin/analytics", headers=headers)
    body = resp.json()["ai_provider_stats"]
    assert "gemini" in body
    assert "groq" in body
    assert "all_failed" in body
    assert "not included" in body["note"].lower()


def test_document_storage_bytes_reflect_uploads(client, make_user, monkeypatch):
    headers, user_id, _ = make_user()
    monkeypatch.setattr(settings, "ADMIN_USER_IDS", [user_id])

    client.put(
        f"/passport/{user_id}",
        headers=headers,
        json={
            "name": "Test",
            "age": 40,
            "gender": "Female",
            "blood_group": "O+",
            "emergency_contact_name": "Someone",
            "emergency_contact_phone": "1234567890",
        },
    )
    files = {"file": ("test.pdf", b"%PDF-1.4 fake pdf content", "application/pdf")}
    client.post(
        f"/passport/{user_id}/documents",
        headers=headers,
        files=files,
        data={"category": "OTHER"},
    )

    resp = client.get("/admin/analytics", headers=headers)
    body = resp.json()
    assert body["total_passport_documents"] >= 1
    assert body["total_document_storage_bytes"] > 0


def test_window_days_parameter_is_bounded(client, make_user, monkeypatch):
    headers, user_id, _ = make_user()
    monkeypatch.setattr(settings, "ADMIN_USER_IDS", [user_id])

    resp = client.get("/admin/analytics", headers=headers, params={"window_days": 9999})
    assert resp.status_code == 422
