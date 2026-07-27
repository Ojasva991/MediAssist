from app.config import settings
from app.storage.staged_guidance_store import create_staged_documents


def _make_staged_row(**overrides):
    row = {
        "source_id": "who_icrc_basic_emergency_care_2018",
        "source_url": "https://example.org/doc.pdf",
        "license": "CC BY-NC-SA 3.0 IGO",
        "attribution": "World Health Organization and ICRC, 2018.",
        "topic_hint": "Airway management",
        "content": "Test staged guidance content.",
    }
    row.update(overrides)
    return create_staged_documents([row])[0]


def test_list_requires_authentication(client):
    resp = client.get("/rag-review")
    assert resp.status_code == 401


def test_list_rejects_non_admin_user(client, make_user):
    headers, _, _ = make_user()
    resp = client.get("/rag-review", headers=headers)
    assert resp.status_code == 403


def test_admin_can_list_pending_documents(client, make_user, monkeypatch):
    headers, user_id, _ = make_user()
    monkeypatch.setattr(settings, "ADMIN_USER_IDS", [user_id])

    doc_id = _make_staged_row()
    resp = client.get("/rag-review", headers=headers)
    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()]
    assert doc_id in ids
    assert all(d["status"] == "pending_review" for d in resp.json())


def test_non_admin_cannot_submit_decision(client, make_user):
    headers, _, _ = make_user()
    doc_id = _make_staged_row()
    resp = client.post(
        f"/rag-review/{doc_id}/decision",
        headers=headers,
        json={"approve": True, "note": "looks fine"},
    )
    assert resp.status_code == 403


def test_admin_can_approve_document(client, make_user, monkeypatch):
    headers, user_id, _ = make_user()
    monkeypatch.setattr(settings, "ADMIN_USER_IDS", [user_id])

    doc_id = _make_staged_row()
    resp = client.post(
        f"/rag-review/{doc_id}/decision",
        headers=headers,
        json={"approve": True, "note": "Still non-commercial, attribution intact."},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "approved"
    assert body["reviewed_by"] == user_id


def test_admin_can_reject_document(client, make_user, monkeypatch):
    headers, user_id, _ = make_user()
    monkeypatch.setattr(settings, "ADMIN_USER_IDS", [user_id])

    doc_id = _make_staged_row()
    resp = client.post(
        f"/rag-review/{doc_id}/decision",
        headers=headers,
        json={"approve": False, "note": "Too close to a direct quote."},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


def test_cannot_re_review_an_already_decided_document(client, make_user, monkeypatch):
    headers, user_id, _ = make_user()
    monkeypatch.setattr(settings, "ADMIN_USER_IDS", [user_id])

    doc_id = _make_staged_row()
    first = client.post(
        f"/rag-review/{doc_id}/decision", headers=headers, json={"approve": True}
    )
    assert first.status_code == 200

    second = client.post(
        f"/rag-review/{doc_id}/decision", headers=headers, json={"approve": False}
    )
    assert second.status_code == 409


def test_decision_on_unknown_document_returns_404(client, make_user, monkeypatch):
    headers, user_id, _ = make_user()
    monkeypatch.setattr(settings, "ADMIN_USER_IDS", [user_id])

    resp = client.post(
        "/rag-review/999999/decision", headers=headers, json={"approve": True}
    )
    assert resp.status_code == 404
