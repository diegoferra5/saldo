from sqlalchemy import Column, String, Integer, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Statement(Base):
    """
    Represents a bank statement uploaded by a user.
    
    A statement belongs to both a user and (optionally) an account.
    Transactions are parsed from the statement PDF.
    
    Note: Constraints and indexes are managed in the database (Supabase).
    This model only maps to the existing schema.
    """
    __tablename__ = "statements"
    
    # Columns
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # ← MANTÉN el default
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    
    # File info
    bank_name = Column(String(50), nullable=False)
    account_type = Column(String(20), nullable=False, default="DEBIT", server_default="DEBIT")
    statement_month = Column(Date, nullable=False)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    file_name = Column(String(255), nullable=False)
    file_size_kb = Column(Integer, nullable=True)
    
    # Processing
    parsing_status = Column(String(20), nullable=False, default="pending", server_default="pending")
    error_message = Column(Text, nullable=True)

    # PDF Summary data (from parser)
    summary_data = Column(JSONB, nullable=True)

    # Security & audit
    file_hash = Column(String(64), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    processed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Relationships (DB handles cascades)
    user = relationship("User", back_populates="statements", passive_deletes=True)
    account = relationship("Account", back_populates="statements", passive_deletes=True)
    transactions = relationship("Transaction", back_populates="statement", passive_deletes=True)
    
    def __repr__(self) -> str:
        return (
            f"<Statement(id={self.id}, "
            f"bank={self.bank_name}, "
            f"type={self.account_type}, "
            f"month={self.statement_month}, "
            f"status={self.parsing_status})>"
        )