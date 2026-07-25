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


def test_passport_requires_authentication(client):
    resp = client.put("/passport/some-user-id", json=PASSPORT_PAYLOAD)
    assert resp.status_code == 401


def test_upsert_then_read_passport(client, make_user):
    headers, user_id, _ = make_user()

    put_resp = client.put(f"/passport/{user_id}", json=PASSPORT_PAYLOAD, headers=headers)
    assert put_resp.status_code == 200
    assert put_resp.json()["name"] == "Priya Sharma"

    get_resp = client.get(f"/passport/{user_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["blood_group"] == "O+"


def test_upsert_overwrites_previous_passport(client, make_user):
    headers, user_id, _ = make_user()
    client.put(f"/passport/{user_id}", json=PASSPORT_PAYLOAD, headers=headers)

    updated = {**PASSPORT_PAYLOAD, "age": 30, "allergies": "None"}
    resp = client.put(f"/passport/{user_id}", json=updated, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["age"] == 30
    assert resp.json()["allergies"] == "None"


def test_read_passport_not_found_returns_404(client, make_user):
    headers, user_id, _ = make_user()
    resp = client.get(f"/passport/{user_id}", headers=headers)
    assert resp.status_code == 404


def test_cannot_read_another_users_passport(client, make_user):
    headers_a, user_id_a, _ = make_user()
    headers_b, _user_id_b, _ = make_user()
    client.put(f"/passport/{user_id_a}", json=PASSPORT_PAYLOAD, headers=headers_a)

    resp = client.get(f"/passport/{user_id_a}", headers=headers_b)
    assert resp.status_code == 403


def test_cannot_write_another_users_passport(client, make_user):
    headers_a, user_id_a, _ = make_user()
    headers_b, _user_id_b, _ = make_user()

    resp = client.put(f"/passport/{user_id_a}", json=PASSPORT_PAYLOAD, headers=headers_b)
    assert resp.status_code == 403


def test_delete_passport(client, make_user):
    headers, user_id, _ = make_user()
    client.put(f"/passport/{user_id}", json=PASSPORT_PAYLOAD, headers=headers)

    delete_resp = client.delete(f"/passport/{user_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "deleted"

    get_resp = client.get(f"/passport/{user_id}", headers=headers)
    assert get_resp.status_code == 404


def test_delete_nonexistent_passport_returns_404(client, make_user):
    headers, user_id, _ = make_user()
    resp = client.delete(f"/passport/{user_id}", headers=headers)
    assert resp.status_code == 404


def test_passport_rejects_invalid_blood_group(client, make_user):
    headers, user_id, _ = make_user()
    bad_payload = {**PASSPORT_PAYLOAD, "blood_group": "Z+"}
    resp = client.put(f"/passport/{user_id}", json=bad_payload, headers=headers)
    assert resp.status_code == 422


def test_passport_requires_gender(client, make_user):
    headers, user_id, _ = make_user()
    bad_payload = {k: v for k, v in PASSPORT_PAYLOAD.items() if k != "gender"}
    resp = client.put(f"/passport/{user_id}", json=bad_payload, headers=headers)
    assert resp.status_code == 422
