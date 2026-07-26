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
from fastapi.responses import Response

from app.auth.dependencies import get_current_user_id
from app.config import settings
from app.models.passport import HealthPassport, PassportAuditLogItem
from app.reports.passport_report import generate_passport_report_pdf
from app.storage.history_store import get_history
from app.storage.passport_store import (
    delete_passport,
    get_passport,
    get_passport_audit_log,
    save_passport,
)

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


@router.get("/{user_id}/audit-log", response_model=list[PassportAuditLogItem])
def read_passport_audit_log(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
) -> list[PassportAuditLogItem]:
    """
    Retrieve the audit trail (who changed what, when) for a user's
    Health Passport - every create/update/delete, most recent first.
    Returns [] if the passport has never been touched (or never
    existed) - never an error.
    """
    _ensure_self(user_id, current_user_id)
    return get_passport_audit_log(user_id)


@router.get("/{user_id}/report")
def download_passport_report(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
) -> Response:
    """
    Generate a one-page, doctor-facing PDF summary of this user's
    Health Passport plus their 5 most recent symptom analyses (if any).

    Requires a saved passport (404 if none exists yet - there's nothing
    meaningful to put in a report). History is best-effort: if fetching
    it fails for some reason, the report is still generated with just
    the passport info rather than failing the whole request over a
    nice-to-have section.
    """
    _ensure_self(user_id, current_user_id)
    passport = get_passport(user_id)
    if passport is None:
        raise HTTPException(
            status_code=404,
            detail="Health Passport not found for this user_id - nothing to put in a report yet.",
        )

    try:
        history = get_history(user_id, limit=5)
    except Exception as e:
        logger.exception("Failed to load history for report generation (%s): %s", user_id, e)
        history = []

    pdf_bytes = generate_passport_report_pdf(passport, history, settings.APP_NAME)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="health-summary-{user_id}.pdf"'
        },
    )
