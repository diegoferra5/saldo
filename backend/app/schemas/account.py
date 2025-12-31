from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
from datetime import datetime
from typing import Optional
from enum import Enum
from uuid import UUID


class AccountType(str, Enum):
    """
    Account type enum - uppercase to match DB storage.

    Values stored in DB are uppercase (DEBIT, CREDIT).
    Swagger will show dropdown with these exact values.
    """
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class AccountBase(BaseModel):
    bank_name: str = Field(..., min_length=2, max_length=50)
    account_type: AccountType
    display_name: Optional[str] = Field(default=None, max_length=100)

    @field_validator("bank_name")
    @classmethod
    def normalize_bank_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v


class AccountCreate(AccountBase):
    """Input when creating an account"""
    model_config = ConfigDict(extra="forbid")


class AccountResponse(AccountBase):
    id: UUID
    user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class AccountUpdate(BaseModel):
    bank_name: Optional[str] = Field(default=None, min_length=2, max_length=50)
    account_type: Optional[AccountType] = None
    display_name: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("bank_name")
    @classmethod
    def normalize_bank_name(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v

    @model_validator(mode="after")
    def check_at_least_one_field(self):
        if (self.bank_name is None and self.account_type is None and
            self.display_name is None and self.is_active is None):
            raise ValueError("At least one field must be provided for update")
        return self

class AccountList(AccountBase):
    id: UUID
    is_active: bool

    model_config = ConfigDict(from_attributes=True, extra="forbid")

