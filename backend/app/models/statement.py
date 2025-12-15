from sqlalchemy import Column, String, Integer, Date, Text, ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base

class Statement(Base):
    __tablename__ = "statements"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to users 
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # File info
    bank_name = Column(String(50), nullable=False)
    account_type = Column(String(20), nullable=False, default="debit", server_default="debit")  # ← NUEVO
    statement_month = Column(Date, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size_kb = Column(Integer, nullable=True)
    
    # Processing status
    parsing_status = Column(
        String(20), 
        nullable=False, 
        default="pending",
        server_default="pending"
    )
    error_message = Column(Text, nullable=True)
    
    # Security & audit
    file_hash = Column(String(64), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    processed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Relationship to User
    user = relationship("User", back_populates="statements")
    
    # Table constraints & indexes
    __table_args__ = (
        # Check constraint para parsing_status
        CheckConstraint(
            "parsing_status IN ('pending', 'processing', 'success', 'failed')",
            name="check_parsing_status"
        ),
        
        # Check constraint para account_type (NUEVO)
        CheckConstraint(
            "account_type IN ('debit', 'credit', 'investment')",
            name="check_account_type"
        ),
        
        # Unique constraint (mismo mes + banco + tipo de cuenta por usuario) - ACTUALIZADO
        UniqueConstraint(
            "user_id", "bank_name", "account_type", "statement_month", 
            name="unique_user_statement"
        ),
        
        # Índices (nombres coinciden con SQL)
        Index("idx_statements_user_id", "user_id"),
        Index("idx_statements_status", "parsing_status"),
        Index("idx_statements_account_type", "account_type"),  # ← NUEVO
    )
    
    def __repr__(self):
        return f"<Statement(id={self.id}, bank={self.bank_name}, type={self.account_type}, month={self.statement_month}, status={self.parsing_status})>"