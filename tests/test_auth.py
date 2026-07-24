import uuid


def _unique_email():
    return f"user-{uuid.uuid4().hex[:10]}@example.com"


def test_signup_creates_account_and_returns_token(client):
    email = _unique_email()
    resp = client.post(
        "/auth/signup",
        json={"name": "Ada Lovelace", "email": email, "password": "password123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == email
    assert body["name"] == "Ada Lovelace"
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert len(body["user_id"]) == 24


def test_signup_same_email_twice_returns_409(client):
    email = _unique_email()
    payload = {"name": "Ada Lovelace", "email": email, "password": "password123"}
    first = client.post("/auth/signup", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/signup", json=payload)
    assert second.status_code == 409


def test_signup_rejects_invalid_email(client):
    resp = client.post(
        "/auth/signup",
        json={"name": "Ada", "email": "not-an-email", "password": "password123"},
    )
    assert resp.status_code == 422


def test_signup_rejects_short_password(client):
    resp = client.post(
        "/auth/signup",
        json={"name": "Ada", "email": _unique_email(), "password": "short"},
    )
    assert resp.status_code == 422


def test_same_email_always_derives_same_user_id(client):
    # Deterministic user_id (sha256 of lowercased/trimmed email) - same
    # email must always map to the same user_id.
    email = _unique_email()
    resp = client.post(
        "/auth/signup",
        json={"name": "Ada", "email": email, "password": "password123"},
    )
    signup_user_id = resp.json()["user_id"]

    login = client.post("/auth/login", json={"email": email.upper(), "password": "password123"})
    assert login.status_code == 200
    assert login.json()["user_id"] == signup_user_id


def test_login_with_correct_credentials_succeeds(client):
    email = _unique_email()
    client.post(
        "/auth/signup",
        json={"name": "Grace Hopper", "email": email, "password": "password123"},
    )
    resp = client.post("/auth/login", json={"email": email, "password": "password123"})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_with_wrong_password_returns_401(client):
    email = _unique_email()
    client.post(
        "/auth/signup",
        json={"name": "Grace Hopper", "email": email, "password": "password123"},
    )
    resp = client.post("/auth/login", json={"email": email, "password": "wrong-password"})
    assert resp.status_code == 401


def test_login_with_unknown_email_returns_401(client):
    resp = client.post(
        "/auth/login", json={"email": _unique_email(), "password": "password123"}
    )
    assert resp.status_code == 401
