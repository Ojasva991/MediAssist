from datetime import datetime, timedelta, timezone


def _future_iso(days=1):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def test_list_requires_authentication(client):
    resp = client.get("/reminders")
    assert resp.status_code == 401


def test_create_and_list_reminder(client, make_user):
    headers, _, _ = make_user()
    create_resp = client.post(
        "/reminders",
        headers=headers,
        json={"title": "Take medicine", "category": "medication", "remind_at": _future_iso()},
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["title"] == "Take medicine"
    assert body["is_active"] is True

    list_resp = client.get("/reminders", headers=headers)
    assert list_resp.status_code == 200
    ids = [r["id"] for r in list_resp.json()]
    assert body["id"] in ids


def test_create_rejects_invalid_category(client, make_user):
    headers, _, _ = make_user()
    resp = client.post(
        "/reminders",
        headers=headers,
        json={"title": "X", "category": "not-a-real-category", "remind_at": _future_iso()},
    )
    assert resp.status_code == 422


def test_create_rejects_invalid_repeat_value(client, make_user):
    headers, _, _ = make_user()
    resp = client.post(
        "/reminders",
        headers=headers,
        json={"title": "X", "remind_at": _future_iso(), "repeat_every_days": 3},
    )
    assert resp.status_code == 422


def test_cannot_view_another_users_reminder(client, make_user):
    headers_a, _, _ = make_user()
    headers_b, _, _ = make_user()

    create_resp = client.post(
        "/reminders", headers=headers_a, json={"title": "Private", "remind_at": _future_iso()}
    )
    reminder_id = create_resp.json()["id"]

    # user B shouldn't be able to complete/update/delete user A's reminder
    resp = client.post(f"/reminders/{reminder_id}/complete", headers=headers_b)
    assert resp.status_code == 403


def test_update_reminder(client, make_user):
    headers, _, _ = make_user()
    create_resp = client.post(
        "/reminders", headers=headers, json={"title": "Old title", "remind_at": _future_iso()}
    )
    reminder_id = create_resp.json()["id"]

    update_resp = client.patch(
        f"/reminders/{reminder_id}", headers=headers, json={"title": "New title"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "New title"


def test_complete_one_time_reminder_deactivates_it(client, make_user):
    headers, _, _ = make_user()
    create_resp = client.post(
        "/reminders", headers=headers, json={"title": "Follow-up", "remind_at": _future_iso()}
    )
    reminder_id = create_resp.json()["id"]

    complete_resp = client.post(f"/reminders/{reminder_id}/complete", headers=headers)
    assert complete_resp.status_code == 200
    assert complete_resp.json()["is_active"] is False

    # no longer shows in the default (active-only) list
    list_resp = client.get("/reminders", headers=headers)
    ids = [r["id"] for r in list_resp.json()]
    assert reminder_id not in ids


def test_complete_repeating_reminder_advances_remind_at(client, make_user):
    headers, _, _ = make_user()
    original_time = _future_iso()
    create_resp = client.post(
        "/reminders",
        headers=headers,
        json={
            "title": "Daily pill",
            "category": "medication",
            "remind_at": original_time,
            "repeat_every_days": 1,
        },
    )
    reminder_id = create_resp.json()["id"]

    complete_resp = client.post(f"/reminders/{reminder_id}/complete", headers=headers)
    assert complete_resp.status_code == 200
    body = complete_resp.json()
    assert body["is_active"] is True  # stays active - it's recurring
    assert body["remind_at"] != original_time  # advanced forward


def test_delete_reminder(client, make_user):
    headers, _, _ = make_user()
    create_resp = client.post(
        "/reminders", headers=headers, json={"title": "Delete me", "remind_at": _future_iso()}
    )
    reminder_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/reminders/{reminder_id}", headers=headers)
    assert delete_resp.status_code == 204

    get_resp = client.get("/reminders", headers=headers, params={"include_inactive": True})
    ids = [r["id"] for r in get_resp.json()]
    assert reminder_id not in ids


def test_complete_unknown_reminder_returns_404(client, make_user):
    headers, _, _ = make_user()
    resp = client.post("/reminders/999999/complete", headers=headers)
    assert resp.status_code == 404
