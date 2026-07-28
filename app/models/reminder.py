"""
Data models for medication/follow-up reminders.

Scope note (read before extending this): this feature is IN-APP reminders
only - the list is fetched and shown when the person has the app open,
plus an optional browser Notification popup while the tab is open. There
is deliberately NO background push notification, email, or SMS here -
that would need a service worker + push subscription infrastructure
(the separate "offline-first PWA for SOS" backlog item) or a new
paid email/SMS provider (the separate "notification channels" backlog
item), neither of which exist in this project yet. Don't let a reminder
silently imply a guarantee ("we'll notify you") that the current
implementation can't back up - the frontend copy should stay honest
about this being an in-app-only reminder.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

VALID_CATEGORIES = {"medication", "follow_up", "other"}
# None means one-time. Otherwise, the number of days between
# occurrences - kept to a short, deliberately simple set of options
# rather than full cron/RRULE support, matching this project's existing
# "simple on purpose" bias (see app/insights/trends.py, app/rag/ingest.py).
VALID_REPEAT_DAYS = {None, 1, 7}


class ReminderCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=1000)
    category: str = Field(default="other")
    remind_at: datetime
    repeat_every_days: int | None = Field(
        default=None, description="None = one-time, 1 = daily, 7 = weekly."
    )

    @field_validator("category")
    @classmethod
    def _validate_category(cls, value: str) -> str:
        if value not in VALID_CATEGORIES:
            raise ValueError(f"category must be one of {sorted(VALID_CATEGORIES)}")
        return value

    @field_validator("repeat_every_days")
    @classmethod
    def _validate_repeat(cls, value: int | None) -> int | None:
        if value not in VALID_REPEAT_DAYS:
            raise ValueError("repeat_every_days must be null, 1 (daily), or 7 (weekly)")
        return value


class ReminderUpdate(BaseModel):
    """All fields optional - only send what you want to change."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=1000)
    category: str | None = None
    remind_at: datetime | None = None
    repeat_every_days: int | None = None
    is_active: bool | None = None

    @field_validator("category")
    @classmethod
    def _validate_category(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_CATEGORIES:
            raise ValueError(f"category must be one of {sorted(VALID_CATEGORIES)}")
        return value

    @field_validator("repeat_every_days")
    @classmethod
    def _validate_repeat(cls, value: int | None) -> int | None:
        if value not in VALID_REPEAT_DAYS:
            raise ValueError("repeat_every_days must be null, 1 (daily), or 7 (weekly)")
        return value


class ReminderOut(BaseModel):
    id: int
    title: str
    notes: str | None
    category: str
    remind_at: datetime
    repeat_every_days: int | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
