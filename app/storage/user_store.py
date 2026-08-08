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


VALID_ROLES = {"user", "admin"}


def create_user(name: str, email: str, password_hash: str) -> dict:
    """Create a new user account. Caller must check email_exists() first.
    Every new account starts as role="user" - promotion to admin is a
    separate, deliberate action (see grant_admin/set_role below), never
    something signup itself can grant."""
    session = get_session()
    try:
        user_id = _derive_user_id(email)
        record = UserRecord(
            user_id=user_id,
            name=name,
            email=email.strip().lower(),
            password_hash=password_hash,
            role="user",
        )
        session.add(record)
        session.commit()
        return {"user_id": user_id, "name": name, "email": email, "role": "user"}
    finally:
        session.close()


def get_user_by_email(email: str) -> Optional[dict]:
    """Return {user_id, name, email, password_hash, role} or None if not found."""
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
            "role": record.role or "user",
        }
    finally:
        session.close()


def get_user_by_id(user_id: str) -> Optional[dict]:
    """
    Return {user_id, name, email, role} (no password_hash - callers of
    this one are display-purpose lookups, e.g. showing a linked
    caregiver's or patient's name in app/routes/caregivers.py, plus the
    admin-gate role check in app/auth/admin.py) or None if not found.
    """
    session = get_session()
    try:
        record = session.query(UserRecord).filter(UserRecord.user_id == user_id).first()
        if record is None:
            return None
        return {
            "user_id": record.user_id,
            "name": record.name,
            "email": record.email,
            "role": record.role or "user",
        }
    finally:
        session.close()


def get_role(user_id: str) -> Optional[str]:
    user = get_user_by_id(user_id)
    return user["role"] if user else None


def set_role(user_id: str, role: str) -> bool:
    """Sets a user's role. Returns False if the user doesn't exist or
    the role isn't recognized - callers (see app/routes/admin_users.py,
    app/scripts/grant_admin.py) turn that into a clear error, not a
    silent no-op."""
    if role not in VALID_ROLES:
        return False
    session = get_session()
    try:
        record = session.query(UserRecord).filter(UserRecord.user_id == user_id).first()
        if record is None:
            return False
        record.role = role
        session.commit()
        return True
    finally:
        session.close()


def list_users(limit: int = 50, offset: int = 0) -> list[dict]:
    """For admin self-service user management (see
    app/routes/admin_users.py) - never returns password_hash."""
    session = get_session()
    try:
        records = (
            session.query(UserRecord)
            .order_by(UserRecord.user_id)
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [
            {
                "user_id": r.user_id,
                "name": r.name,
                "email": r.email,
                "role": r.role or "user",
            }
            for r in records
        ]
    finally:
        session.close()
