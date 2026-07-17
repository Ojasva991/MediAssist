"""
Postgres-backed storage for user accounts (auth).

Replaces the previous Google Sheets version. Same function signatures
as before (email_exists, create_user, get_user_by_email), so
app/routes/auth.py needs no changes.
"""

import hashlib
import logging
from typing import Optional

from app.storage.db import get_session
from app.storage.models import UserRecord

logger = logging.getLogger(__name__)


def _derive_user_id(email: str) -> str:
    """
    Deterministic, URL-safe user_id from email - same scheme as before,
    so existing passport rows keyed by that pattern keep working.
    """
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()[:24]


def email_exists(email: str) -> bool:
    session = get_session()
    try:
        return (
            session.query(UserRecord)
            .filter(UserRecord.email == email.strip().lower())
            .first()
            is not None
        )
    finally:
        session.close()


def create_user(name: str, email: str, password_hash: str) -> dict:
    """Create a new user account. Caller must check email_exists() first."""
    session = get_session()
    try:
        user_id = _derive_user_id(email)
        record = UserRecord(
            user_id=user_id,
            name=name,
            email=email.strip().lower(),
            password_hash=password_hash,
        )
        session.add(record)
        session.commit()
        return {"user_id": user_id, "name": name, "email": email}
    finally:
        session.close()


def get_user_by_email(email: str) -> Optional[dict]:
    """Return {user_id, name, email, password_hash} or None if not found."""
    session = get_session()
    try:
        record = (
            session.query(UserRecord)
            .filter(UserRecord.email == email.strip().lower())
            .first()
        )
        if record is None:
            return None
        return {
            "user_id": record.user_id,
            "name": record.name,
            "email": record.email,
            "password_hash": record.password_hash,
        }
    finally:
        session.close()
