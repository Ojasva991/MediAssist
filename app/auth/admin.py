"""
Shared admin-gate dependency for admin-only routes (see
app/routes/rag_review.py, app/routes/admin_analytics.py).

This project has no general role-based access control yet (see
PROJECT_STATE.md's backlog) - settings.ADMIN_USER_IDS is a deliberate
stopgap, not a real permissions system.

Deliberately extracted to ONE function rather than left duplicated
inline in each admin route file (which is how it started) - two
independent copies of "check if admin" is exactly the kind of thing
that quietly drifts when one gets updated and the other doesn't, and
that's a privilege-check bug waiting to happen, not just messy code.
"""

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user_id
from app.config import settings


def require_admin(current_user_id: str = Depends(get_current_user_id)) -> str:
    if current_user_id not in settings.ADMIN_USER_IDS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. This is an admin-only area.",
        )
    return current_user_id
