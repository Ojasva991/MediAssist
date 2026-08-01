from datetime import datetime, timedelta, timezone


def _future_iso(days=1):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def test_invite_requires_authentication(client):
    resp = client.post("/caregivers/invite")
    assert resp.status_code == 401


def test_patient_can_create_invite(client, make_user):
    headers, _, _ = make_user()
    resp = client.post("/caregivers/invite", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["code"]) == 8


def test_caregiver_can_accept_invite(client, make_user):
    patient_headers, _, _ = make_user()
    caregiver_headers, _, _ = make_user()

    invite = client.post("/caregivers/invite", headers=patient_headers).json()
    resp = client.post(
        "/caregivers/accept", headers=caregiver_headers, json={"code": invite["code"]}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


def test_cannot_accept_own_invite(client, make_user):
    headers, _, _ = make_user()
    invite = client.post("/caregivers/invite", headers=headers).json()
    resp = client.post("/caregivers/accept", headers=headers, json={"code": invite["code"]})
    assert resp.status_code == 400
    assert "own invite" in resp.json()["detail"].lower()


def test_cannot_reuse_an_already_accepted_code(client, make_user):
    patient_headers, _, _ = make_user()
    caregiver_headers, _, _ = make_user()
    other_headers, _, _ = make_user()

    invite = client.post("/caregivers/invite", headers=patient_headers).json()
    client.post("/caregivers/accept", headers=caregiver_headers, json={"code": invite["code"]})

    resp = client.post("/caregivers/accept", headers=other_headers, json={"code": invite["code"]})
    assert resp.status_code == 400
    assert "already been used" in resp.json()["detail"].lower()


def test_unknown_code_returns_400(client, make_user):
    headers, _, _ = make_user()
    resp = client.post("/caregivers/accept", headers=headers, json={"code": "NOTREAL1"})
    assert resp.status_code == 400


def _link_patient_and_caregiver(client, make_user):
    patient_headers, patient_user_id, _ = make_user()
    caregiver_headers, caregiver_user_id, _ = make_user()
    invite = client.post("/caregivers/invite", headers=patient_headers).json()
    client.post("/caregivers/accept", headers=caregiver_headers, json={"code": invite["code"]})
    return patient_headers, patient_user_id, caregiver_headers, caregiver_user_id


def test_patient_sees_linked_caregiver_in_list(client, make_user):
    patient_headers, _, caregiver_headers, _ = _link_patient_and_caregiver(client, make_user)
    resp = client.get("/caregivers/my-caregivers", headers=patient_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["status"] == "active"


def test_caregiver_sees_linked_patient_in_list(client, make_user):
    _, patient_user_id, caregiver_headers, _ = _link_patient_and_caregiver(client, make_user)
    resp = client.get("/caregivers/my-patients", headers=caregiver_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    # The caregiver needs the patient's actual user_id to call the
    # patient-scoped endpoints - must not be null/omitted.
    assert resp.json()[0]["other_party_user_id"] == patient_user_id


def test_unlinked_user_cannot_view_patient_passport(client, make_user):
    headers, _, _ = make_user()
    other_headers, other_user_id, _ = make_user()
    resp = client.get(f"/caregivers/{other_user_id}/passport", headers=headers)
    assert resp.status_code == 403


def test_linked_caregiver_can_view_patient_passport(client, make_user):
    patient_headers, patient_user_id, caregiver_headers, _ = _link_patient_and_caregiver(
        client, make_user
    )
    # Patient sets up their passport first
    client.put(
        f"/passport/{patient_user_id}",
        headers=patient_headers,
        json={
            "name": "Test Patient",
            "age": 40,
            "gender": "Female",
            "blood_group": "O+",
            "emergency_contact_name": "Someone",
            "emergency_contact_phone": "1234567890",
        },
    )
    resp = client.get(f"/caregivers/{patient_user_id}/passport", headers=caregiver_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test Patient"


def test_linked_caregiver_can_view_patient_history(client, make_user):
    _, patient_user_id, caregiver_headers, _ = _link_patient_and_caregiver(client, make_user)
    resp = client.get(f"/caregivers/{patient_user_id}/history", headers=caregiver_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_linked_caregiver_can_create_and_complete_patient_reminder(client, make_user):
    _, patient_user_id, caregiver_headers, _ = _link_patient_and_caregiver(client, make_user)

    create_resp = client.post(
        f"/caregivers/{patient_user_id}/reminders",
        headers=caregiver_headers,
        json={"title": "Take medicine", "remind_at": _future_iso()},
    )
    assert create_resp.status_code == 201
    reminder_id = create_resp.json()["id"]

    complete_resp = client.post(
        f"/caregivers/{patient_user_id}/reminders/{reminder_id}/complete",
        headers=caregiver_headers,
    )
    assert complete_resp.status_code == 200
    assert complete_resp.json()["is_active"] is False


def test_unlinked_user_cannot_manage_patient_reminders(client, make_user):
    headers, _, _ = make_user()
    other_headers, other_user_id, _ = make_user()
    resp = client.post(
        f"/caregivers/{other_user_id}/reminders",
        headers=headers,
        json={"title": "Take medicine", "remind_at": _future_iso()},
    )
    assert resp.status_code == 403


def test_patient_can_revoke_caregiver_access(client, make_user):
    patient_headers, patient_user_id, caregiver_headers, _ = _link_patient_and_caregiver(
        client, make_user
    )
    link_id = client.get("/caregivers/my-caregivers", headers=patient_headers).json()[0]["id"]

    revoke_resp = client.post(f"/caregivers/{link_id}/revoke", headers=patient_headers)
    assert revoke_resp.status_code == 204

    # Access should now be denied
    resp = client.get(f"/caregivers/{patient_user_id}/history", headers=caregiver_headers)
    assert resp.status_code == 403


def test_caregiver_cannot_revoke_a_link_they_dont_own(client, make_user):
    patient_headers, _, caregiver_headers, _ = _link_patient_and_caregiver(client, make_user)
    link_id = client.get("/caregivers/my-caregivers", headers=patient_headers).json()[0]["id"]

    # The caregiver (not the patient) tries to revoke - should fail, since
    # only the patient owns/can revoke this link.
    resp = client.post(f"/caregivers/{link_id}/revoke", headers=caregiver_headers)
    assert resp.status_code == 404
