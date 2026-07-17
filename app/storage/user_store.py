"""
Google Sheets-backed storage for user accounts (auth).

Lives in the "Users" tab of the same spreadsheet as passports (see
sheets_client.py). Passwords are stored as bcrypt hashes only - never
plain text (see app/auth/security.py).

Sheet layout (row 1 = header, one row per account):
user_id | name | email | password_hash
"""

import hashlib
import logging
from typing import Optional

from app.storage.sheets_client import get_or_create_worksheet

logger = logging.getLogger(__name__)

_TAB_NAME = "Users"
_COLUMNS = ["user_id", "name", "email", "password_hash"]

_worksheet = None  # cached across requests within a process


def _get_worksheet():
    global _worksheet
    if _worksheet is None:
        _worksheet = get_or_create_worksheet(_TAB_NAME, _COLUMNS)
    return _worksheet


def _derive_user_id(email: str) -> str:
    """
    Deterministic, URL-safe user_id from email - keeps the same scheme
    the frontend's old local-only AuthContext used, so existing
    passport rows keyed by that pattern keep working during transition.
    """
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()[:24]


def _find_row_by_email(worksheet, email: str) -> Optional[int]:
    emails = worksheet.col_values(3)  # column C = email, includes header
    for idx, value in enumerate(emails, start=1):
        if idx == 1:
            continue
        if value.strip().lower() == email.strip().lower():
            return idx
    return None


def email_exists(email: str) -> bool:
    worksheet = _get_worksheet()
    return _find_row_by_email(worksheet, email) is not None


def create_user(name: str, email: str, password_hash: str) -> dict:
    """Create a new user account. Caller must check email_exists() first."""
    worksheet = _get_worksheet()
    user_id = _derive_user_id(email)
    worksheet.append_row([user_id, name, email, password_hash])
    return {"user_id": user_id, "name": name, "email": email}


def get_user_by_email(email: str) -> Optional[dict]:
    """Return {user_id, name, email, password_hash} or None if not found."""
    worksheet = _get_worksheet()
    row_num = _find_row_by_email(worksheet, email)
    if row_num is None:
        return None

    row = worksheet.row_values(row_num)
    padded = row + [""] * (len(_COLUMNS) - len(row))
    user_id, name, email_val, password_hash = padded[: len(_COLUMNS)]
    return {
        "user_id": user_id,
        "name": name,
        "email": email_val,
        "password_hash": password_hash,
    }
