def test_history_requires_authentication(client):
    resp = client.get("/history/some-user-id")
    assert resp.status_code == 401


def test_history_empty_for_new_user(client, make_user):
    headers, user_id, _ = make_user()
    resp = client.get(f"/history/{user_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_cannot_read_another_users_history(client, make_user):
    headers_a, user_id_a, _ = make_user()
    headers_b, _user_id_b, _ = make_user()

    resp = client.get(f"/history/{user_id_a}", headers=headers_b)
    assert resp.status_code == 403


def test_history_limit_query_param_is_bounded(client, make_user):
    headers, user_id, _ = make_user()

    # Above the allowed max (50) should be rejected by validation.
    resp = client.get(f"/history/{user_id}?limit=999", headers=headers)
    assert resp.status_code == 422

    # Below 1 should also be rejected.
    resp = client.get(f"/history/{user_id}?limit=0", headers=headers)
    assert resp.status_code == 422
