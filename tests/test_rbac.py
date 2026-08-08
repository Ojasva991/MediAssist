from app.config import settings
from app.storage.user_store import get_role, set_role


def test_new_signup_defaults_to_user_role(client):
    resp = client.post(
        "/auth/signup",
        json={"name": "Ada", "email": "rbac-test-1@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "user"


def test_login_response_includes_role(client, make_user):
    headers, user_id, email = make_user()
    set_role(user_id, "admin")
    resp = client.post("/auth/login", json={"email": email, "password": "password123"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


def test_get_role_and_set_role_round_trip(make_user):
    _, user_id, _ = make_user()
    assert get_role(user_id) == "user"
    assert set_role(user_id, "admin") is True
    assert get_role(user_id) == "admin"


def test_set_role_rejects_invalid_role(make_user):
    _, user_id, _ = make_user()
    assert set_role(user_id, "superuser") is False
    assert get_role(user_id) == "user"  # unchanged


def test_set_role_returns_false_for_unknown_user():
    assert set_role("not-a-real-user-id", "admin") is False


def test_admin_gate_grants_access_via_real_role(client, make_user):
    headers, user_id, _ = make_user()
    set_role(user_id, "admin")
    resp = client.get("/admin/analytics", headers=headers)
    assert resp.status_code == 200


def test_admin_gate_still_honors_legacy_env_var_fallback(client, make_user, monkeypatch):
    # Transitional: someone with role="user" but listed in the legacy
    # ADMIN_USER_IDS env var should still get access - this is the
    # "nobody loses access mid-migration" guarantee.
    headers, user_id, _ = make_user()
    monkeypatch.setattr(settings, "ADMIN_USER_IDS", [user_id])
    assert get_role(user_id) == "user"  # confirm NOT admin by role
    resp = client.get("/admin/analytics", headers=headers)
    assert resp.status_code == 200


def test_admin_gate_rejects_user_with_neither(client, make_user):
    headers, _, _ = make_user()
    resp = client.get("/admin/analytics", headers=headers)
    assert resp.status_code == 403


def test_list_users_requires_admin(client, make_user):
    headers, _, _ = make_user()
    resp = client.get("/admin/users", headers=headers)
    assert resp.status_code == 403


def test_admin_can_list_users(client, make_user):
    headers, user_id, _ = make_user()
    set_role(user_id, "admin")
    # limit=200 (the max) rather than relying on the default 50 - this
    # test should hold regardless of how many other users exist in
    # whatever database it's run against, not just a freshly-emptied one.
    resp = client.get("/admin/users", headers=headers, params={"limit": 200})
    assert resp.status_code == 200
    ids = [u["user_id"] for u in resp.json()]
    assert user_id in ids
    # Never leak password hashes through this endpoint.
    assert all("password_hash" not in u for u in resp.json())


def test_admin_can_promote_another_user(client, make_user):
    admin_headers, admin_id, _ = make_user()
    set_role(admin_id, "admin")
    _, target_id, _ = make_user()

    resp = client.post(
        f"/admin/users/{target_id}/role", headers=admin_headers, json={"role": "admin"}
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"
    assert get_role(target_id) == "admin"


def test_admin_cannot_demote_themselves(client, make_user):
    admin_headers, admin_id, _ = make_user()
    set_role(admin_id, "admin")

    resp = client.post(
        f"/admin/users/{admin_id}/role", headers=admin_headers, json={"role": "user"}
    )
    assert resp.status_code == 400
    assert get_role(admin_id) == "admin"  # unchanged


def test_role_change_rejects_invalid_role_value(client, make_user):
    admin_headers, admin_id, _ = make_user()
    set_role(admin_id, "admin")
    _, target_id, _ = make_user()

    resp = client.post(
        f"/admin/users/{target_id}/role", headers=admin_headers, json={"role": "superuser"}
    )
    assert resp.status_code == 422


def test_role_change_on_unknown_user_returns_404(client, make_user):
    admin_headers, admin_id, _ = make_user()
    set_role(admin_id, "admin")

    resp = client.post(
        "/admin/users/not-a-real-user/role", headers=admin_headers, json={"role": "admin"}
    )
    assert resp.status_code == 404


def test_non_admin_cannot_change_roles(client, make_user):
    headers, _, _ = make_user()
    _, target_id, _ = make_user()
    resp = client.post(f"/admin/users/{target_id}/role", headers=headers, json={"role": "admin"})
    assert resp.status_code == 403
