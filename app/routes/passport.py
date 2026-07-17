"""
/passport routes - HTTP layer for the Health Passport feature.

Storage is Postgres-backed (see app/storage/passport_store.py) - data
persists across restarts.

AUTHENTICATION: every route requires a valid bearer token (see
app/auth/dependencies.py). The user_id in the URL must match the
user_id embedded in the caller's token - a valid token for one account
cannot be used to read/write/delete another account's passport. Get a
token via POST /auth/signup or POST /auth/login.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user_id
from app.models.passport import HealthPassport
from app.storage.passport_store import delete_passport, get_passport, save_passport

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/passport", tags=["Health Passport"])


def _ensure_self(user_id: str, current_user_id: str) -> None:
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this passport.",
        )


@router.put("/{user_id}", response_model=HealthPassport)
def upsert_passport(
    user_id: str,
    passport: HealthPassport,
    current_user_id: str = Depends(get_current_user_id),
) -> HealthPassport:
    """
    Create or update the Health Passport for a given user_id.

    PUT is used (not POST) because this is idempotent: calling it
    multiple times with the same user_id overwrites the previous
    record rather than creating duplicates.
    """
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id cannot be blank")
    _ensure_self(user_id, current_user_id)
    return save_passport(user_id, passport)


@router.get("/{user_id}", response_model=HealthPassport)
def read_passport(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
) -> HealthPassport:
    """Retrieve the Health Passport for a given user_id."""
    _ensure_self(user_id, current_user_id)
    passport = get_passport(user_id)
    if passport is None:
        raise HTTPException(
            status_code=404, detail="Health Passport not found for this user_id"
        )
    return passport


@router.delete("/{user_id}")
def remove_passport(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
) -> dict:
    """Delete the Health Passport for a given user_id."""
    _ensure_self(user_id, current_user_id)
    deleted = delete_passport(user_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail="Health Passport not found for this user_id"
        )
    return {"status": "deleted", "user_id": user_id}
