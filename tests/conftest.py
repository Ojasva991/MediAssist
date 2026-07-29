"""
Shared pytest fixtures.

Sets required env vars and points DATABASE_URL at a throwaway SQLite
file *before* any `app.*` module is imported, since app/config.py and
app/storage/db.py both read settings/create the engine at import time.
This keeps tests fully isolated from the real Postgres database - no
tests ever touch production data, and CI needs no database service.
"""

import os
from pathlib import Path

_TEST_DB_PATH = Path(__file__).parent / "_test.db"

os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-tests-only")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TEST_DB_PATH}")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
# High enough that the /analyze rate-limit tests don't interfere with
# every other test hitting the same endpoint in the same test run.
os.environ.setdefault("RATE_LIMIT_ANALYZE", "1000/minute")
os.environ.setdefault("RATE_LIMIT_ANALYZE_IMAGE", "1000/minute")
os.environ.setdefault("RATE_LIMIT_DRUG_INTERACTIONS", "1000/minute")

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage.db import Base, engine


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    """Create all tables once per test session, drop + delete the file after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if _TEST_DB_PATH.exists():
        _TEST_DB_PATH.unlink()


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def make_user(client):
    """Factory fixture: sign up a fresh user, return (auth_headers, user_id, email)."""

    def _make(name="Test User", email=None, password="password123"):
        import uuid

        email = email or f"user-{uuid.uuid4().hex[:10]}@example.com"
        resp = client.post(
            "/auth/signup",
            json={"name": name, "email": email, "password": password},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        headers = {"Authorization": f"Bearer {body['access_token']}"}
        return headers, body["user_id"], email

    return _make
