from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator, computed_field
from datetime import datetime, date
from typing import Optional
from enum import Enum
from uuid import UUID
from decimal import Decimal


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

    # Balance tracking (common for all account types)
    balance: Optional[Decimal] = Field(
        default=None,
        description="Current balance. DEBIT: positive=funds available, negative=overdraft. "
                    "CREDIT: negative=amount owed, zero=paid off"
    )
    balance_updated_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when balance was last updated from a statement"
    )
    last_statement_date: Optional[date] = Field(
        default=None,
        description="statement_month of the most recent processed statement that updated this balance"
    )

    # Credit-specific fields (nullable for DEBIT accounts)
    credit_limit: Optional[Decimal] = Field(
        default=None,
        description="Credit limit (CREDIT accounts only)"
    )
    minimum_payment: Optional[Decimal] = Field(
        default=None,
        description="Minimum payment due this period (CREDIT accounts only)"
    )
    payment_min_no_interest: Optional[Decimal] = Field(
        default=None,
        description="Minimum payment amount required to avoid interest charges (CREDIT accounts only)"
    )
    payment_date: Optional[date] = Field(
        default=None,
        description="Suggested/recommended payment date (CREDIT accounts only)"
    )
    payment_due_date: Optional[date] = Field(
        default=None,
        description="Final payment due date / deadline - late fees apply after this date (CREDIT accounts only)"
    )

    # Computed field: available_credit (only for CREDIT accounts)
    @computed_field
    @property
    def available_credit(self) -> Optional[Decimal]:
        """
        Calculate available credit for CREDIT accounts.
        Formula: credit_limit + balance (balance is negative for CREDIT)
        Returns None for DEBIT accounts or if credit_limit/balance is missing.
        """
        if self.account_type == AccountType.CREDIT and self.credit_limit is not None and self.balance is not None:
            return self.credit_limit + self.balance  # balance is negative, so this is actually credit_limit - abs(balance)
        return None

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
    balance: Optional[Decimal] = None
    balance_updated_at: Optional[datetime] = None
    last_statement_date: Optional[date] = None

    # Credit-specific fields (for listing credit accounts)
    credit_limit: Optional[Decimal] = None
    payment_due_date: Optional[date] = None

    # Computed field: available_credit (only for CREDIT accounts)
    @computed_field
    @property
    def available_credit(self) -> Optional[Decimal]:
        """Calculate available credit for CREDIT accounts."""
        if self.account_type == AccountType.CREDIT and self.credit_limit is not None and self.balance is not None:
            return self.credit_limit + self.balance
        return None

    model_config = ConfigDict(from_attributes=True, extra="forbid")

