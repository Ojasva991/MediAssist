"""
/reminders routes.

Ownership enforced the same way as every other user-data route in this
project (see app/routes/history.py, app/routes/passport.py): a reminder
can only be read/modified/deleted by the user who created it.

Scope reminder (see app/models/reminder.py for the full note): these are
IN-APP reminders only. There is no push notification, email, or SMS
behind this - the frontend is responsible for being honest about that
in its copy, and this backend should never grow a "send at remind_at"
job without that infrastructure actually existing first.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user_id
from app.models.reminder import ReminderCreate, ReminderOut, ReminderUpdate
from app.storage.reminder_store import (
    complete_reminder,
    create_reminder,
    delete_reminder,
    get_reminder,
    list_reminders,
    update_reminder,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reminders", tags=["Reminders"])


def _require_ownership(reminder_id: int, current_user_id: str):
    record = get_reminder(reminder_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No reminder found with that id."
        )
    if record.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to act on this reminder.",
        )
    return record


@router.get("", response_model=list[ReminderOut])
def list_my_reminders(
    include_inactive: bool = False,
    current_user_id: str = Depends(get_current_user_id),
) -> list[ReminderOut]:
    return list_reminders(current_user_id, include_inactive=include_inactive)


@router.post("", response_model=ReminderOut, status_code=status.HTTP_201_CREATED)
def create_my_reminder(
    payload: ReminderCreate,
    current_user_id: str = Depends(get_current_user_id),
) -> ReminderOut:
    return create_reminder(current_user_id, payload.model_dump())


@router.patch("/{reminder_id}", response_model=ReminderOut)
def update_my_reminder(
    reminder_id: int,
    payload: ReminderUpdate,
    current_user_id: str = Depends(get_current_user_id),
) -> ReminderOut:
    _require_ownership(reminder_id, current_user_id)
    changes = payload.model_dump(exclude_unset=True)
    return update_reminder(reminder_id, changes)


@router.post("/{reminder_id}/complete", response_model=ReminderOut)
def complete_my_reminder(
    reminder_id: int,
    current_user_id: str = Depends(get_current_user_id),
) -> ReminderOut:
    _require_ownership(reminder_id, current_user_id)
    return complete_reminder(reminder_id)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_reminder(
    reminder_id: int,
    current_user_id: str = Depends(get_current_user_id),
) -> None:
    _require_ownership(reminder_id, current_user_id)
    delete_reminder(reminder_id)
