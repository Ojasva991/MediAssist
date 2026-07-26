"""
Postgres-backed storage for Health Passport records, plus an audit
trail of every create/update/delete (see PassportAuditLogRecord).

Replaces the previous Google Sheets version. Same function signatures
as before (save_passport, get_passport, delete_passport), so
app/routes/passport.py needed no changes for those three - the audit
log is additive.
"""

import logging
from typing import Optional

from app.models.passport import HealthPassport, PassportAuditLogItem
from app.storage.db import get_session
from app.storage.models import PassportAuditLogRecord, PassportRecord

logger = logging.getLogger(__name__)

# Every field that's part of the passport's actual data (excludes
# user_id, which is the key, not a data field). Used both to build a
# snapshot dict and to compute which fields changed on an update.
_PASSPORT_FIELDS = [
    "name",
    "age",
    "gender",
    "blood_group",
    "allergies",
    "medications",
    "chronic_diseases",
    "emergency_contact_name",
    "emergency_contact_phone",
]


def _snapshot_from_record(record: PassportRecord) -> dict:
    return {field: getattr(record, field) for field in _PASSPORT_FIELDS}


def _log_audit(
    session,
    user_id: str,
    action: str,
    snapshot: Optional[dict],
    changed_fields: Optional[list[str]] = None,
) -> None:
    session.add(
        PassportAuditLogRecord(
            user_id=user_id,
            action=action,
            snapshot=snapshot,
            changed_fields=changed_fields,
        )
    )


def save_passport(user_id: str, passport: HealthPassport) -> HealthPassport:
    """Create or update (upsert) a passport for the given user_id.

    Also writes an audit entry: "created" for a brand-new passport, or
    "updated" with the list of fields that actually changed - but only
    if something actually did change, so re-saving identical data
    doesn't pollute the audit log with no-op entries.
    """
    session = get_session()
    try:
        record = session.get(PassportRecord, user_id)
        is_new = record is None
        before_snapshot = None if is_new else _snapshot_from_record(record)

        if is_new:
            record = PassportRecord(user_id=user_id)
            session.add(record)

        record.name = passport.name
        record.age = passport.age
        record.gender = passport.gender
        record.blood_group = passport.blood_group.value
        record.allergies = passport.allergies
        record.medications = passport.medications
        record.chronic_diseases = passport.chronic_diseases
        record.emergency_contact_name = passport.emergency_contact_name
        record.emergency_contact_phone = passport.emergency_contact_phone

        after_snapshot = _snapshot_from_record(record)

        if is_new:
            _log_audit(session, user_id, "created", after_snapshot)
        else:
            changed = [
                field
                for field in _PASSPORT_FIELDS
                if before_snapshot.get(field) != after_snapshot.get(field)
            ]
            if changed:
                _log_audit(session, user_id, "updated", after_snapshot, changed)

        session.commit()
        return passport
    finally:
        session.close()


def get_passport(user_id: str) -> Optional[HealthPassport]:
    """Retrieve a passport, or None if no passport exists for this user_id."""
    session = get_session()
    try:
        record = session.get(PassportRecord, user_id)
        if record is None:
            return None

        return HealthPassport(
            name=record.name,
            age=record.age,
            # Falls back to a placeholder for rows saved before the gender
            # column existed (or before the DB migration below has been run) -
            # the Pydantic model requires a non-blank string, but old rows may
            # have NULL here. Saving the passport again fills in a real value.
            gender=record.gender or "Not specified",
            blood_group=record.blood_group or "UNKNOWN",
            allergies=record.allergies,
            medications=record.medications,
            chronic_diseases=record.chronic_diseases,
            emergency_contact_name=record.emergency_contact_name,
            emergency_contact_phone=record.emergency_contact_phone,
        )
    finally:
        session.close()


def delete_passport(user_id: str) -> bool:
    """Delete a passport. Returns True if it existed and was removed.

    Logs a "deleted" audit entry with a snapshot of what was removed,
    captured before the delete - otherwise there'd be nothing left to
    snapshot afterward.
    """
    session = get_session()
    try:
        record = session.get(PassportRecord, user_id)
        if record is None:
            return False
        snapshot = _snapshot_from_record(record)
        session.delete(record)
        _log_audit(session, user_id, "deleted", snapshot)
        session.commit()
        return True
    finally:
        session.close()


def get_passport_audit_log(user_id: str, limit: int = 50) -> list[PassportAuditLogItem]:
    """Return a user's Health Passport audit trail, most recent first."""
    session = get_session()
    try:
        records = (
            session.query(PassportAuditLogRecord)
            .filter(PassportAuditLogRecord.user_id == user_id)
            .order_by(PassportAuditLogRecord.id.desc())
            .limit(min(limit, 50))
            .all()
        )
        return [
            PassportAuditLogItem(
                id=r.id,
                action=r.action,
                changed_fields=r.changed_fields,
                snapshot=r.snapshot,
                created_at=r.created_at,
            )
            for r in records
        ]
    finally:
        session.close()
