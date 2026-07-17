"""
Postgres-backed storage for Health Passport records.

Replaces the previous Google Sheets version. Same function signatures
as before (save_passport, get_passport, delete_passport), so
app/routes/passport.py needs no changes.
"""

import logging
from typing import Optional

from app.models.passport import HealthPassport
from app.storage.db import get_session
from app.storage.models import PassportRecord

logger = logging.getLogger(__name__)


def save_passport(user_id: str, passport: HealthPassport) -> HealthPassport:
    """Create or update (upsert) a passport for the given user_id."""
    session = get_session()
    try:
        record = session.get(PassportRecord, user_id)
        if record is None:
            record = PassportRecord(user_id=user_id)
            session.add(record)

        record.name = passport.name
        record.age = passport.age
        record.blood_group = passport.blood_group.value
        record.allergies = passport.allergies
        record.medications = passport.medications
        record.chronic_diseases = passport.chronic_diseases
        record.emergency_contact_name = passport.emergency_contact_name
        record.emergency_contact_phone = passport.emergency_contact_phone

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
    """Delete a passport. Returns True if it existed and was removed."""
    session = get_session()
    try:
        record = session.get(PassportRecord, user_id)
        if record is None:
            return False
        session.delete(record)
        session.commit()
        return True
    finally:
        session.close()
