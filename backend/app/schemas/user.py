from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
import uuid


class UserBase(BaseModel):
    """
    Base user schema with common attributes.
    """
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """
    Schema for creating a new user (signup).
    Includes password field.
    """
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """
    Schema for user login.
    """
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """
    Schema for returning user data.
    Does NOT include password.
    """
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models


class UserInDB(UserBase):
    """
    Schema for user stored in database.
    Includes hashed password (internal use only).
    """
    id: uuid.UUID
    hashed_password: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True