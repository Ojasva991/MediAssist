"""
Shared admin-gate dependency for admin-only routes (see
app/routes/rag_review.py, app/routes/admin_analytics.py,
app/routes/admin_users.py).

Checks real, database-backed role-based access control
(UserRecord.role, see app/storage/user_store.py's get_role/set_role) -
this REPLACES the old settings.ADMIN_USER_IDS env-var stopgap as the
primary mechanism.

settings.ADMIN_USER_IDS is kept as a deliberate, temporary fallback
(an OR condition, not removed outright) so nobody who already had
access via the env var loses it the moment this deploys, before
they've been migrated to role="admin" in the database (see
app/scripts/grant_admin.py for how to do that migration). Once every
env-var admin has been migrated to a real role, remove the
ADMIN_USER_IDS check entirely - it should not become a permanent
second, parallel admin system living alongside the real one.
"""

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user_id
from app.config import settings
from app.storage.user_store import get_role


def require_admin(current_user_id: str = Depends(get_current_user_id)) -> str:
    role = get_role(current_user_id)
    is_admin_by_role = role == "admin"
    is_admin_by_legacy_env_var = current_user_id in settings.ADMIN_USER_IDS  # transitional, see module docstring

    if not (is_admin_by_role or is_admin_by_legacy_env_var):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. This is an admin-only area.",
        )
    return current_user_id
