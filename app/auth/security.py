"""
Password hashing and JWT issuing/verification.

Isolated here so app/routes/auth.py and app/routes/passport.py stay
focused on HTTP concerns rather than crypto details.

Uses the `bcrypt` library directly (not passlib) - passlib's last
release predates current bcrypt versions and throws on import in
newer environments.
"""

import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days - simple session length for this app

# bcrypt has a hard 72-byte input limit; enforced here rather than
# silently truncating, since silent truncation can mask a mismatched
# password bug later.
_MAX_PASSWORD_BYTES = 72


def hash_password(plain_password: str) -> str:
    if len(plain_password.encode("utf-8")) > _MAX_PASSWORD_BYTES:
        raise ValueError("Password is too long")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except ValueError:
        # Malformed hash in storage - treat as verification failure, not a crash.
        return False


def create_access_token(user_id: str) -> str:
    """Issue a signed JWT whose subject (`sub`) is the user's user_id."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """
    Verify a JWT and return the user_id (`sub`) it was issued for.
    Raises JWTError if the token is invalid, tampered with, or expired.
    """
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    user_id = payload.get("sub")
    if not user_id:
        raise JWTError("Token missing subject")
    return user_id
