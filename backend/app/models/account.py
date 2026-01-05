# app/models/account.py

import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, Numeric, Date, text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Account(Base):
    """
    Represents a user's financial account (debit or credit).

    Deletion policy (MVP):
    - NEVER call session.delete(account) from the app layer.
    - ALWAYS soft-delete: account.is_active = False
    - This preserves history for auditability.

    Notes:
    - Constraints and indexes are managed in the database (Supabase).
    - This model only maps to the existing schema.
    - `updated_at` is currently managed by SQLAlchemy (ORM-side).
      In production, this should migrate to a DB trigger.
    """
    __tablename__ = "accounts"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Account info
    bank_name = Column(String(50), nullable=False)
    account_type = Column(String(10), nullable=False)  # e.g. DEBIT / CREDIT
    display_name = Column(String(100), nullable=True)

    # Status (soft delete)
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    # ========================================
    # Balance tracking (common for all account types)
    # ========================================
    balance = Column(
        Numeric(15, 2),
        nullable=True,
        comment="Current balance. DEBIT: positive=funds available, negative=overdraft. "
                "CREDIT: negative=amount owed, zero=paid off",
    )
    balance_updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Timestamp when balance was last updated from a statement",
    )
    last_statement_date = Column(
        Date,
        nullable=True,
        comment="statement_month of the most recent processed statement that updated this balance",
    )

    # ========================================
    # Credit-specific fields (nullable for DEBIT accounts)
    # ========================================
    credit_limit = Column(
        Numeric(15, 2),
        nullable=True,
        comment="Credit limit (CREDIT accounts only, NULL for DEBIT)",
    )
    minimum_payment = Column(
        Numeric(15, 2),
        nullable=True,
        comment="Minimum payment due this period (CREDIT accounts only, NULL for DEBIT)",
    )
    payment_min_no_interest = Column(
        Numeric(15, 2),
        nullable=True,
        comment="Minimum payment amount required to avoid interest charges (CREDIT accounts only, NULL for DEBIT)",
    )
    payment_date = Column(
        Date,
        nullable=True,
        comment="Suggested/recommended payment date (CREDIT accounts only, NULL for DEBIT)",
    )
    payment_due_date = Column(
        Date,
        nullable=True,
        comment="Final payment due date / deadline - late fees apply after this date (CREDIT accounts only, NULL for DEBIT)",
    )

    # Timestamps
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),  # ORM-side for MVP; migrate to DB trigger in prod
    )

    # Relationships (DB handles cascades)
    user = relationship(
        "User",
        back_populates="accounts",
        passive_deletes=True,
    )
    statements = relationship(
        "Statement",
        back_populates="account",
        passive_deletes=True,
    )
    transactions = relationship(
        "Transaction",
        back_populates="account",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Account(id={self.id}, "
            f"user_id={self.user_id}, "
            f"bank={self.bank_name}, "
            f"type={self.account_type}, "
            f"active={self.is_active})>"
        )
