import pytest
from jose import JWTError

from app.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_roundtrip():
    hashed = hash_password("correct-horse-battery-staple")
    assert hashed != "correct-horse-battery-staple"
    assert verify_password("correct-horse-battery-staple", hashed)


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("correct-horse-battery-staple")
    assert not verify_password("wrong-password", hashed)


def test_verify_password_rejects_malformed_hash_without_raising():
    # Storage corruption or bad data should fail closed, not crash.
    assert not verify_password("anything", "not-a-real-bcrypt-hash")


def test_hash_password_rejects_overlong_password():
    # bcrypt has a hard 72-byte input limit.
    with pytest.raises(ValueError):
        hash_password("x" * 100)


def test_access_token_roundtrip():
    token = create_access_token(user_id="abc123")
    assert decode_access_token(token) == "abc123"


def test_decode_rejects_tampered_token():
    token = create_access_token(user_id="abc123")
    tampered = token[:-2] + ("aa" if token[-2:] != "aa" else "bb")
    with pytest.raises(JWTError):
        decode_access_token(tampered)
