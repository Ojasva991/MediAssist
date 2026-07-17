"""
Google Sheets-backed storage for Health Passport records.

Data lives in the "Passports" tab of the shared spreadsheet (see
sheets_client.py). Survives backend restarts, redeploys, and Render
free-tier cold starts.

Storage is still isolated behind these three functions, so route code
(app/routes/passport.py) requires no changes to swap implementations
in the future.

Sheet layout (row 1 = header, one row per user_id):
user_id | name | age | blood_group | allergies | medications |
chronic_diseases | emergency_contact_name | emergency_contact_phone

Notes:
- Optional passport fields are stored as empty strings in the sheet
  (Sheets has no concept of `null`) and converted back to None on read.
- This is intentionally simple (fetch-all-rows, scan for user_id) which
  is fine at hackathon/demo traffic. It will not scale to large numbers
  of rows or high request volume - Postgres remains the recommended
  upgrade path for real production use (see HANDOFF.md Section 2.4).
"""

import logging
from typing import Optional

from app.models.passport import HealthPassport
from app.storage.sheets_client import get_or_create_worksheet

logger = logging.getLogger(__name__)

_TAB_NAME = "Passports"
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

_worksheet = None  # cached across requests within a process


def _get_worksheet():
    global _worksheet
    if _worksheet is None:
        _worksheet = get_or_create_worksheet(_TAB_NAME, _COLUMNS)
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
