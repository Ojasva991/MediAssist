"""
Data models for authentication (signup, login, tokens).

Kept separate from app/models/passport.py since these represent a
different concern (identity) from the medical data itself.
"""

import re

from pydantic import BaseModel, Field, field_validator

from app.auth.disposable_domains import is_disposable_email

# Deliberately a bit stricter than "has an @ and a dot" (the old check) -
# still permissive of real-world addresses (plus-addressing, subdomains,
# etc.), just rejects obviously-malformed input rather than a proper
# RFC 5322 parser, which is overkill here.
_EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


class UserSignup(BaseModel):
    """Payload for POST /auth/signup."""

    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_PATTERN.match(v):
            raise ValueError("Enter a valid email address")
        if is_disposable_email(v):
            # Best-effort only - see app/auth/disposable_domains.py's
            # scope note. This blocks the common/obvious cases, it is
            # not full email verification.
            raise ValueError(
                "Please use a real, non-disposable email address. "
                "Temporary/throwaway email providers aren't accepted."
            )
        return v


class UserLogin(BaseModel):
    """Payload for POST /auth/login."""

    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class TokenResponse(BaseModel):
    """Returned on successful signup/login."""

    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    email: str
    role: str
