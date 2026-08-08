from pydantic import BaseModel, field_validator

from app.storage.user_store import VALID_ROLES


class AdminUserOut(BaseModel):
    user_id: str
    name: str
    email: str
    role: str


class SetRoleRequest(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def _validate_role(cls, value: str) -> str:
        if value not in VALID_ROLES:
            raise ValueError(f"role must be one of {sorted(VALID_ROLES)}")
        return value
