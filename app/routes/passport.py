"""
/passport routes - HTTP layer for the Health Passport feature.

Storage is in-memory (see app/storage/passport_store.py) - data resets
whenever the server restarts. This is a deliberate hackathon-scope
choice; swapping to a real database later only requires changing the
storage module, not these routes.

SECURITY NOTE: There is no authentication in this MVP. `user_id` is a
caller-supplied path parameter, not a verified identity - anyone who
knows or guesses a user_id can read/write/delete that passport. This
is acceptable for a hackathon demo but must NOT be treated as secure
multi-user storage. It's structured so real auth could be added later
(e.g. deriving user_id from a verified token instead of the URL)
without changing these route signatures much.
"""

import logging

from fastapi import APIRouter, HTTPException

from app.models.passport import HealthPassport
from app.storage.passport_store import delete_passport, get_passport, save_passport

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/passport", tags=["Health Passport"])


@router.put("/{user_id}", response_model=HealthPassport)
def upsert_passport(user_id: str, passport: HealthPassport) -> HealthPassport:
    """
    Create or update the Health Passport for a given user_id.

    PUT is used (not POST) because this is idempotent: calling it
    multiple times with the same user_id overwrites the previous
    record rather than creating duplicates.
    """
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id cannot be blank")
    return save_passport(user_id, passport)


@router.get("/{user_id}", response_model=HealthPassport)
def read_passport(user_id: str) -> HealthPassport:
    """Retrieve the Health Passport for a given user_id."""
    passport = get_passport(user_id)
    if passport is None:
        raise HTTPException(
            status_code=404, detail="Health Passport not found for this user_id"
        )
    return passport


@router.delete("/{user_id}")
def remove_passport(user_id: str) -> dict:
    """Delete the Health Passport for a given user_id."""
    deleted = delete_passport(user_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail="Health Passport not found for this user_id"
        )
    return {"status": "deleted", "user_id": user_id}
