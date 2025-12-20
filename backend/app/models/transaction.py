# app/models/transaction.py

from sqlalchemy import Column, String, Boolean, Numeric, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Transaction(Base):
    """
    Represents a financial transaction from a bank statement.
    
    Transactions are parsed from PDF statements and can be:
    - CARGO (expense/debit)
    - ABONO (income/credit)
    - UNKNOWN (needs manual review)
    
    This is a domain model that enforces core business rules about transactions.
    """
    __tablename__ = "transactions"

# Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False
    )
    statement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("statements.id", ondelete="CASCADE"),
        nullable=False
    )

    # Dates (3 formats from PDF parsing)
    date = Column(String(20), nullable=False)  # Original format: "11/NOV"
    date_liquidacion = Column(String(20), nullable=True)  # Original format
    transaction_date = Column(Date, nullable=False)  # Parsed complete date

    # Description and amounts
    description = Column(Text, nullable=False)
    amount_abs = Column(Numeric(10, 2), nullable=False)  # Always positive
    amount = Column(Numeric(10, 2), nullable=True)  # Negative=expense, Positive=income, NULL=unknown

    # Classification
    movement_type = Column(
        String(10),
        nullable=False,
        default="UNKNOWN",
        server_default="UNKNOWN"
    )
    needs_review = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )
    category = Column(String(50), nullable=True)

    # Balances from PDF (optional, when available)
    saldo_operacion = Column(Numeric(12, 2), nullable=True)
    saldo_liquidacion = Column(Numeric(12, 2), nullable=True)

    # Metadata
    transaction_hash = Column(String(64), nullable=False)
    
    # Timestamps
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )