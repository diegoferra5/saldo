from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v


class UserCreate(UserBase):
    """Signup payload."""
    password: str = Field(..., min_length=8, max_length=100)

    model_config = ConfigDict(extra="forbid")


class UserLogin(BaseModel):
    """Login payload."""
    email: EmailStr
    password: str

    model_config = ConfigDict(extra="forbid")


class UserResponse(UserBase):
    """Public user data (no password)."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    net_worth: float

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UserInDB(UserBase):
    """Internal schema (includes hashed_password)."""
    id: UUID
    hashed_password: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid")

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    model_config = ConfigDict(extra="forbid")

class TokenWithUser(Token):
    user: UserResponse
    model_config = ConfigDict(extra="forbid")
