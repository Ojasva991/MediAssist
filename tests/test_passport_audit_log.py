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


def test_audit_log_requires_authentication(client):
    resp = client.get("/passport/some-user-id/audit-log")
    assert resp.status_code == 401


def test_audit_log_empty_when_passport_never_touched(client, make_user):
    headers, user_id, _ = make_user()
    resp = client.get(f"/passport/{user_id}/audit-log", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_creating_passport_logs_a_created_entry(client, make_user):
    headers, user_id, _ = make_user()
    client.put(f"/passport/{user_id}", json=PASSPORT_PAYLOAD, headers=headers)

    resp = client.get(f"/passport/{user_id}/audit-log", headers=headers)
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) == 1
    assert entries[0]["action"] == "created"
    assert entries[0]["changed_fields"] is None
    assert entries[0]["snapshot"]["name"] == "Priya Sharma"


def test_updating_passport_logs_an_updated_entry_with_changed_fields(client, make_user):
    headers, user_id, _ = make_user()
    client.put(f"/passport/{user_id}", json=PASSPORT_PAYLOAD, headers=headers)

    updated = {**PASSPORT_PAYLOAD, "age": 30, "allergies": "None"}
    client.put(f"/passport/{user_id}", json=updated, headers=headers)

    resp = client.get(f"/passport/{user_id}/audit-log", headers=headers)
    entries = resp.json()
    assert len(entries) == 2
    # Most recent first.
    assert entries[0]["action"] == "updated"
    assert set(entries[0]["changed_fields"]) == {"age", "allergies"}
    assert entries[0]["snapshot"]["age"] == 30
    assert entries[1]["action"] == "created"


def test_resaving_identical_passport_does_not_log_a_pointless_update(client, make_user):
    headers, user_id, _ = make_user()
    client.put(f"/passport/{user_id}", json=PASSPORT_PAYLOAD, headers=headers)
    # Same payload again - nothing actually changed.
    client.put(f"/passport/{user_id}", json=PASSPORT_PAYLOAD, headers=headers)

    resp = client.get(f"/passport/{user_id}/audit-log", headers=headers)
    entries = resp.json()
    assert len(entries) == 1
    assert entries[0]["action"] == "created"


def test_deleting_passport_logs_a_deleted_entry_with_snapshot(client, make_user):
    headers, user_id, _ = make_user()
    client.put(f"/passport/{user_id}", json=PASSPORT_PAYLOAD, headers=headers)
    client.delete(f"/passport/{user_id}", headers=headers)

    resp = client.get(f"/passport/{user_id}/audit-log", headers=headers)
    entries = resp.json()
    assert entries[0]["action"] == "deleted"
    assert entries[0]["snapshot"]["name"] == "Priya Sharma"


def test_cannot_view_another_users_audit_log(client, make_user):
    headers_a, user_id_a, _ = make_user()
    headers_b, _user_id_b, _ = make_user()
    client.put(f"/passport/{user_id_a}", json=PASSPORT_PAYLOAD, headers=headers_a)

    resp = client.get(f"/passport/{user_id_a}/audit-log", headers=headers_b)
    assert resp.status_code == 403
