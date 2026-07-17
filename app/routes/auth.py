"""
/auth routes - signup and login.

Issues JWT access tokens on successful signup/login. Passport routes
(app/routes/passport.py) require this token and verify its subject
matches the user_id being accessed.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.auth.security import create_access_token, hash_password, verify_password
from app.models.auth import TokenResponse, UserLogin, UserSignup
from app.storage.user_store import create_user, email_exists, get_user_by_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: UserSignup) -> TokenResponse:
    """Create a new account and return an access token for it."""
    if email_exists(payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    password_hash = hash_password(payload.password)
    user = create_user(name=payload.name, email=payload.email, password_hash=password_hash)

    token = create_access_token(user_id=user["user_id"])
    return TokenResponse(
        access_token=token,
        user_id=user["user_id"],
        name=user["name"],
        email=user["email"],
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin) -> TokenResponse:
    """Verify credentials and return an access token."""
    user = get_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        # Same error for "no such user" and "wrong password" - don't leak
        # which one it was, that's an account enumeration vector.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    token = create_access_token(user_id=user["user_id"])
    return TokenResponse(
        access_token=token,
        user_id=user["user_id"],
        name=user["name"],
        email=user["email"],
    )
