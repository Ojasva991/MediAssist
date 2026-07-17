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

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.auth.security import decode_access_token

_bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    description="Paste the access_token returned from /auth/login or /auth/signup",
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
