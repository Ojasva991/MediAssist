"""
FastAPI dependency for extracting and verifying the current user from
the Authorization header.

Usage in a route:

    @router.get("/{user_id}")
    def read_passport(user_id: str, current_user_id: str = Depends(get_current_user_id)):
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        ...
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.auth.security import decode_access_token


class _Bearer401(HTTPBearer):
    """
    FastAPI's stock HTTPBearer raises 403 when the Authorization header
    is missing entirely, and would only give 401 for cases we handle
    ourselves below. That means "not logged in at all" and "logged in
    but not allowed" both showed up as 403 to the frontend, with no way
    to tell them apart (e.g. to decide whether to redirect to login).
    This override makes "no credentials" consistently 401 instead, so
    401 always means "not authenticated" and 403 always means
    "authenticated, but not authorized for this resource".
    """

    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        try:
            return await super().__call__(request)
        except HTTPException as exc:
            if exc.status_code == status.HTTP_403_FORBIDDEN:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            raise


_bearer_scheme = _Bearer401(
    scheme_name="BearerAuth",
    description="Paste the access_token returned from /auth/login or /auth/signup",
)

# auto_error=False means: if there's no Authorization header at all, this
# resolves to None instead of raising 401. Used where auth is optional
# (e.g. /analyze, which must keep working for logged-out users, but
# should save history when the caller IS logged in).
_optional_bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    description="Optional - paste an access_token to have this saved to your history.",
    auto_error=False,
)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    """
    Verifies the bearer token and returns the authenticated user's user_id.
    Raises 401 if the token is missing, malformed, or expired.
    """
    token = credentials.credentials
    try:
        return decode_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_optional_bearer_scheme),
) -> Optional[str]:
    """
    Like get_current_user_id, but never raises. Returns None if there's no
    token, or if the token is present but invalid/expired - callers that
    use this dependency must treat "not logged in" and "bad token" the
    same way (i.e. proceed without a saved identity), never as an error.
    """
    if credentials is None:
        return None
    try:
        return decode_access_token(credentials.credentials)
    except JWTError:
        return None
