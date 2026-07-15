"""
In-memory storage for Health Passport records.

This is a deliberately simple in-memory store, matching the "in-memory"
choice made for this hackathon MVP (see Milestone 5 decision). Data is
lost when the server restarts - worth knowing before a demo, not a bug.

Storage is isolated behind these functions rather than exposing the
raw dict to route code. That means swapping this for a real database
later (e.g. SQLite) only requires changing THIS file - no route code
changes needed.
"""

from app.models.passport import HealthPassport

# user_id -> HealthPassport. Not thread-safe in a heavy multi-worker
# setup, but fine for a single-process hackathon demo.
_STORE: dict[str, HealthPassport] = {}


def save_passport(user_id: str, passport: HealthPassport) -> HealthPassport:
    """Create or update (upsert) a passport for the given user_id."""
    _STORE[user_id] = passport
    return passport


def get_passport(user_id: str) -> HealthPassport | None:
    """Retrieve a passport, or None if no passport exists for this user_id."""
    return _STORE.get(user_id)


def delete_passport(user_id: str) -> bool:
    """Delete a passport. Returns True if it existed and was removed."""
    if user_id in _STORE:
        del _STORE[user_id]
        return True
    return False
