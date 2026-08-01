"""
Storage helpers for CaregiverLinkRecord (see app/storage/models.py for
the full design rationale).
"""

import secrets
import string
from datetime import datetime, timedelta, timezone

from app.storage.db import get_session
from app.storage.models import CaregiverLinkRecord

# Deliberately human-typable: uppercase letters and digits only, minus
# visually-ambiguous characters (0/O, 1/I/L) - a patient reads this code
# aloud or texts it to a caregiver, it needs to survive that.
_CODE_ALPHABET = "".join(c for c in string.ascii_uppercase + string.digits if c not in "0O1IL")
_CODE_LENGTH = 8
_INVITE_EXPIRY_DAYS = 7


class CaregiverError(ValueError):
    """Raised for invite/accept failures that should map to a 4xx, not a 500."""


def _as_aware_utc(dt: datetime) -> datetime:
    """
    SQLite (used in tests/dev) silently strips tzinfo when round-tripping
    a DateTime(timezone=True) column, returning a naive datetime even
    though it was stored as aware - Postgres (production) does not have
    this problem. Comparing a naive value against datetime.now(timezone.utc)
    raises TypeError, so every comparison here normalizes first. A no-op
    if the value is already aware (the real Postgres case).
    """
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _generate_invite_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))


def create_invite(patient_user_id: str) -> CaregiverLinkRecord:
    """
    Creates a new pending invite for `patient_user_id` to share with a
    caregiver. Retries on the (astronomically unlikely) chance of a
    code collision rather than trusting a single attempt blindly.
    """
    session = get_session()
    try:
        for _ in range(5):
            code = _generate_invite_code()
            if (
                session.query(CaregiverLinkRecord)
                .filter(CaregiverLinkRecord.invite_code == code)
                .first()
                is None
            ):
                break
        else:
            raise CaregiverError("Could not generate a unique invite code, please try again.")

        record = CaregiverLinkRecord(
            patient_user_id=patient_user_id,
            caregiver_user_id=None,
            invite_code=code,
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(days=_INVITE_EXPIRY_DAYS),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()


def accept_invite(invite_code: str, caregiver_user_id: str) -> CaregiverLinkRecord:
    """
    Redeems an invite code for the given caregiver. Raises
    CaregiverError (not a generic exception) for every failure mode
    that should be shown to the person as a clear message, not a 500:
    unknown code, expired code, already-used code, or a patient trying
    to accept their own invite.
    """
    session = get_session()
    try:
        record = (
            session.query(CaregiverLinkRecord)
            .filter(CaregiverLinkRecord.invite_code == invite_code.strip().upper())
            .first()
        )
        if record is None:
            raise CaregiverError("That invite code wasn't found. Double-check it and try again.")
        if record.patient_user_id == caregiver_user_id:
            raise CaregiverError("You can't accept your own invite code.")
        if record.status != "pending":
            raise CaregiverError("This invite code has already been used or revoked.")
        if _as_aware_utc(record.expires_at) < datetime.now(timezone.utc):
            raise CaregiverError("This invite code has expired - ask for a new one.")

        record.caregiver_user_id = caregiver_user_id
        record.status = "active"
        record.accepted_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()


def list_caregivers_for_patient(patient_user_id: str) -> list[CaregiverLinkRecord]:
    """Pending + active links (not revoked) where this user is the patient."""
    session = get_session()
    try:
        return (
            session.query(CaregiverLinkRecord)
            .filter(
                CaregiverLinkRecord.patient_user_id == patient_user_id,
                CaregiverLinkRecord.status != "revoked",
            )
            .order_by(CaregiverLinkRecord.created_at.desc())
            .all()
        )
    finally:
        session.close()


def list_patients_for_caregiver(caregiver_user_id: str) -> list[CaregiverLinkRecord]:
    """Active links where this user is the caregiver."""
    session = get_session()
    try:
        return (
            session.query(CaregiverLinkRecord)
            .filter(
                CaregiverLinkRecord.caregiver_user_id == caregiver_user_id,
                CaregiverLinkRecord.status == "active",
            )
            .order_by(CaregiverLinkRecord.accepted_at.desc())
            .all()
        )
    finally:
        session.close()


def revoke_link(link_id: int, patient_user_id: str) -> bool:
    """Only the patient who owns the link can revoke it. Returns False if
    the link doesn't exist or doesn't belong to this patient."""
    session = get_session()
    try:
        record = (
            session.query(CaregiverLinkRecord)
            .filter(
                CaregiverLinkRecord.id == link_id,
                CaregiverLinkRecord.patient_user_id == patient_user_id,
            )
            .first()
        )
        if record is None:
            return False
        record.status = "revoked"
        record.revoked_at = datetime.now(timezone.utc)
        session.commit()
        return True
    finally:
        session.close()


def has_active_access(caregiver_user_id: str, patient_user_id: str) -> bool:
    """
    THE authorization check every caregiver-scoped route (see
    app/routes/caregivers.py) must call before returning or modifying
    any of a patient's data. True only for a currently-active,
    non-revoked link between exactly this caregiver and this patient.
    """
    session = get_session()
    try:
        return (
            session.query(CaregiverLinkRecord)
            .filter(
                CaregiverLinkRecord.caregiver_user_id == caregiver_user_id,
                CaregiverLinkRecord.patient_user_id == patient_user_id,
                CaregiverLinkRecord.status == "active",
            )
            .first()
            is not None
        )
    finally:
        session.close()
