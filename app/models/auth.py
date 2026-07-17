"""
Data models for authentication (signup, login, tokens).

Kept separate from app/models/passport.py since these represent a
different concern (identity) from the medical data itself.
"""

from pydantic import BaseModel, Field, field_validator


class UserSignup(BaseModel):
    """Payload for POST /auth/signup."""

    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Enter a valid email address")
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
