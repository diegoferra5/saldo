# app/models/transaction.py

import uuid
from sqlalchemy import Column, String, Boolean, Numeric, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Transaction(Base):
    """
    Represents a financial transaction parsed from a bank statement PDF.
    
    Constraints and indexes are managed in the database (Supabase).
    This model only maps to the existing schema.
    """
    __tablename__ = "transactions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    statement_id = Column(UUID(as_uuid=True), ForeignKey("statements.id", ondelete="CASCADE"), nullable=False)

    # Dates
    date = Column(String(10), nullable=False)
    date_liquidacion = Column(String(10), nullable=True)
    transaction_date = Column(Date, nullable=False)

    # Description and amounts
    description = Column(Text, nullable=False)
    amount_abs = Column(Numeric(12, 2), nullable=False)
    amount = Column(Numeric(12, 2), nullable=True)

    # Classification
    movement_type = Column(String(10), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    needs_review = Column(Boolean, nullable=False, default=True, server_default="true")
    category = Column(String(50), nullable=True)

    # Balances
    saldo_operacion = Column(Numeric(12, 2), nullable=True)
    saldo_liquidacion = Column(Numeric(12, 2), nullable=True)

    # Metadata
    transaction_hash = Column(String(64), nullable=False)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships (DB handles cascades)
    user = relationship("User", back_populates="transactions", passive_deletes=True)
    account = relationship("Account", back_populates="transactions", passive_deletes=True)
    statement = relationship("Statement", back_populates="transactions", passive_deletes=True)

    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, "
            f"date={self.transaction_date}, "
            f"amount={self.amount}, "
            f"type={self.movement_type})>"
        )