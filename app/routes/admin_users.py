"""
/admin/users routes - self-service RBAC management for existing admins.

This is what lets admin promotion happen through the app itself, not
just shell access to app/scripts/grant_admin.py - but that script is
still the only way to create the FIRST admin (see its docstring for
why an unauthenticated "become admin" path would be a real
vulnerability). Everything here requires already being an admin.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.admin import require_admin
from app.models.admin_user import AdminUserOut, SetRoleRequest
from app.storage.user_store import get_user_by_id, list_users, set_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/users", tags=["Admin - User Management"])


@router.get("", response_model=list[AdminUserOut])
def list_all_users(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _admin_user_id: str = Depends(require_admin),
) -> list[AdminUserOut]:
    return list_users(limit=limit, offset=offset)


@router.post("/{user_id}/role", response_model=AdminUserOut)
def change_user_role(
    user_id: str,
    payload: SetRoleRequest,
    admin_user_id: str = Depends(require_admin),
) -> AdminUserOut:
    # Deliberately blocked, not just discouraged: an admin locking
    # themselves out by demoting their own only-admin account is a real
    # support headache (app/scripts/grant_admin.py is the recovery path,
    # but better to just not allow the footgun in the first place).
    if user_id == admin_user_id and payload.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't remove your own admin access through this endpoint.",
        )

    if not set_role(user_id, payload.role):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such user.")

    updated = get_user_by_id(user_id)
    return AdminUserOut(**updated)
