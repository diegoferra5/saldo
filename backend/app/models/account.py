# app/models/account.py

import uuid

from sqlalchemy import (
    Column,
    String,
    Boolean,
    ForeignKey,
    CheckConstraint,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Account(Base):
    """
    Represents a user's financial account (debit or credit).

    IMPORTANT — Deletion policy (MVP):
    - NEVER call session.delete(account) from the app layer.
    - ALWAYS soft-delete: account.is_active = False
    - This preserves history for auditability and avoids accidental data loss.
    """
    __tablename__ = "accounts"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key -> users
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Account info
    bank_name = Column(String(50), nullable=False)
    account_type = Column(String(10), nullable=False)  # 'DEBIT' | 'CREDIT'
    display_name = Column(String(100), nullable=True)

    # Status (soft delete)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))

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
        onupdate=func.now(),
    )

    # Relationships (no ORM cascade; DB rules apply)
    user = relationship("User", back_populates="accounts")

    # statements.account_id is ON DELETE SET NULL in DB
    statements = relationship(
        "Statement",
        back_populates="account",
        passive_deletes=True,
    )

    # transactions.account_id is ON DELETE CASCADE in DB
    # We keep ORM explicit (no cascade); DB handles it if a hard-delete ever happens.
    transactions = relationship(
        "Transaction",
        back_populates="account",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint(
            "account_type IN ('DEBIT', 'CREDIT')",
            name="check_account_type",
        ),
        Index("idx_accounts_user_id", "user_id"),
        Index("idx_accounts_user_active", "user_id", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"<Account(id={self.id}, "
            f"user_id={self.user_id}, "
            f"bank={self.bank_name}, "
            f"type={self.account_type}, "
            f"active={self.is_active})>"
        )
