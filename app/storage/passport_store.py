"""
Google Sheets-backed storage for Health Passport records.

Replaces the original in-memory dict (see git history) with a real
persistent store: a Google Sheet, accessed via a service account.
Data now survives backend restarts, redeploys, and Render free-tier
cold starts.

Storage is still isolated behind these three functions, so route code
(app/routes/passport.py) required ZERO changes to pick this up.

Sheet layout (row 1 = header, one row per user_id):
user_id | name | age | blood_group | allergies | medications |
chronic_diseases | emergency_contact_name | emergency_contact_phone

Notes:
- gspread client + worksheet handle are created once per process and
  reused (cheaper than reconnecting on every request).
- Optional passport fields are stored as empty strings in the sheet
  (Sheets has no concept of `null`) and converted back to None on read.
- This is intentionally simple (fetch-all-rows, scan for user_id) which
  is fine at hackathon/demo traffic. It will not scale to large numbers
  of rows or high request volume - Postgres remains the recommended
  upgrade path for real production use (see HANDOFF.md Section 2.4).
"""

import json
import logging
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from app.config import settings
from app.models.passport import HealthPassport

logger = logging.getLogger(__name__)

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_COLUMNS = [
    "user_id",
    "name",
    "age",
    "blood_group",
    "allergies",
    "medications",
    "chronic_diseases",
    "emergency_contact_name",
    "emergency_contact_phone",
]

_worksheet = None  # lazily initialized, reused across requests


def _get_worksheet():
    """Return a cached worksheet handle, creating the connection on first use."""
    global _worksheet
    if _worksheet is not None:
        return _worksheet

    if not settings.GOOGLE_SHEET_ID or not settings.GOOGLE_SHEETS_CREDENTIALS:
        raise RuntimeError(
            "GOOGLE_SHEET_ID and GOOGLE_SHEETS_CREDENTIALS must be set to use "
            "Health Passport storage."
        )

    creds_dict = json.loads(settings.GOOGLE_SHEETS_CREDENTIALS)
    credentials = Credentials.from_service_account_info(creds_dict, scopes=_SCOPES)
    client = gspread.authorize(credentials)

    sheet = client.open_by_key(settings.GOOGLE_SHEET_ID)
    _worksheet = sheet.sheet1

    # Make sure the header row exists and matches what we expect, so a
    # freshly created blank sheet still works without manual setup.
    existing_header = _worksheet.row_values(1)
    if existing_header != _COLUMNS:
        _worksheet.update("A1", [_COLUMNS])

    return _worksheet


def _find_row(worksheet, user_id: str) -> Optional[int]:
    """Return the 1-indexed row number for user_id, or None if not found."""
    user_ids = worksheet.col_values(1)  # column A = user_id, includes header
    for idx, value in enumerate(user_ids, start=1):
        if idx == 1:
            continue  # skip header row
        if value == user_id:
            return idx
    return None


def _passport_to_row(user_id: str, passport: HealthPassport) -> list:
    return [
        user_id,
        passport.name,
        passport.age,
        passport.blood_group.value,
        passport.allergies or "",
        passport.medications or "",
        passport.chronic_diseases or "",
        passport.emergency_contact_name,
        passport.emergency_contact_phone,
    ]


def _row_to_passport(row: list) -> HealthPassport:
    # row follows _COLUMNS order; pad defensively in case a row is short
    padded = row + [""] * (len(_COLUMNS) - len(row))
    (
        _user_id,
        name,
        age,
        blood_group,
        allergies,
        medications,
        chronic_diseases,
        emergency_contact_name,
        emergency_contact_phone,
    ) = padded[: len(_COLUMNS)]

    return HealthPassport(
        name=name,
        age=int(age),
        blood_group=blood_group or "UNKNOWN",
        allergies=allergies or None,
        medications=medications or None,
        chronic_diseases=chronic_diseases or None,
        emergency_contact_name=emergency_contact_name,
        emergency_contact_phone=emergency_contact_phone,
    )


def save_passport(user_id: str, passport: HealthPassport) -> HealthPassport:
    """Create or update (upsert) a passport for the given user_id."""
    worksheet = _get_worksheet()
    row_values = _passport_to_row(user_id, passport)

    row_num = _find_row(worksheet, user_id)
    if row_num is not None:
        worksheet.update(f"A{row_num}:I{row_num}", [row_values])
    else:
        worksheet.append_row(row_values)

    return passport


def get_passport(user_id: str) -> Optional[HealthPassport]:
    """Retrieve a passport, or None if no passport exists for this user_id."""
    worksheet = _get_worksheet()
    row_num = _find_row(worksheet, user_id)
    if row_num is None:
        return None

    row = worksheet.row_values(row_num)
    return _row_to_passport(row)


def delete_passport(user_id: str) -> bool:
    """Delete a passport. Returns True if it existed and was removed."""
    worksheet = _get_worksheet()
    row_num = _find_row(worksheet, user_id)
    if row_num is None:
        return False

    worksheet.delete_rows(row_num)
    return True
