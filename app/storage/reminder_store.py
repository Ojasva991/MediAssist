"""
Storage helpers for ReminderRecord (see app/storage/models.py).
Same pattern as the other *_store.py modules: routes never touch
SQLAlchemy sessions/models directly.
"""

from datetime import timedelta

from app.storage.db import get_session
from app.storage.models import ReminderRecord


def create_reminder(user_id: str, data: dict) -> ReminderRecord:
    session = get_session()
    try:
        record = ReminderRecord(user_id=user_id, **data)
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()


def list_reminders(user_id: str, *, include_inactive: bool = False) -> list[ReminderRecord]:
    session = get_session()
    try:
        query = session.query(ReminderRecord).filter(ReminderRecord.user_id == user_id)
        if not include_inactive:
            query = query.filter(ReminderRecord.is_active.is_(True))
        return query.order_by(ReminderRecord.remind_at.asc()).all()
    finally:
        session.close()


def get_reminder(reminder_id: int) -> ReminderRecord | None:
    session = get_session()
    try:
        return session.query(ReminderRecord).filter(ReminderRecord.id == reminder_id).first()
    finally:
        session.close()


def update_reminder(reminder_id: int, changes: dict) -> ReminderRecord | None:
    session = get_session()
    try:
        record = session.query(ReminderRecord).filter(ReminderRecord.id == reminder_id).first()
        if record is None:
            return None
        for key, value in changes.items():
            setattr(record, key, value)
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()


def delete_reminder(reminder_id: int) -> bool:
    session = get_session()
    try:
        record = session.query(ReminderRecord).filter(ReminderRecord.id == reminder_id).first()
        if record is None:
            return False
        session.delete(record)
        session.commit()
        return True
    finally:
        session.close()


def complete_reminder(reminder_id: int) -> ReminderRecord | None:
    """
    Marks a reminder done.

    One-time (repeat_every_days is None): deactivates it - it's done,
    it won't show up again.

    Repeating (repeat_every_days is 1 or 7): advances remind_at forward
    by that many days and keeps it active, so "completing" a daily
    medication reminder means "I took it, remind me again tomorrow,"
    not "delete this forever."
    """
    session = get_session()
    try:
        record = session.query(ReminderRecord).filter(ReminderRecord.id == reminder_id).first()
        if record is None:
            return None
        if record.repeat_every_days:
            record.remind_at = record.remind_at + timedelta(days=record.repeat_every_days)
        else:
            record.is_active = False
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()
