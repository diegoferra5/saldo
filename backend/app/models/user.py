from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class User(Base):
    """
    Represents a registered user in Saldo.
    
    Deletion Policy:
    - User deletion is handled at the database level (ON DELETE CASCADE).
    - When a user is deleted, PostgreSQL automatically removes:
      * All accounts
      * All statements
      * All transactions
    - The ORM uses passive_deletes=True to delegate this to the database.
    """
    __tablename__ = "users"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User Info
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    
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
        onupdate=func.now(),
    )
    
    # Relationships - DB handles cascades via ON DELETE CASCADE
    accounts = relationship(
        "Account",
        back_populates="user",
        passive_deletes=True
    )
    statements = relationship(
        "Statement",
        back_populates="user",
        passive_deletes=True
    )

    transactions = relationship(
        "Transaction",
        back_populates="user",
        passive_deletes=True)

    @property
    def net_worth(self) -> float:
        """
        Calculate the user's total net worth.

        Net worth is the sum of all account balances:
        - DEBIT accounts have positive balances (assets)
        - CREDIT accounts have negative balances (liabilities)
        - Only active accounts are included
        - Accounts with NULL balance are treated as 0

        Returns:
            float: Total net worth
        """
        total = sum(
            float(account.balance or 0)
            for account in self.accounts
            if account.is_active
        )
        return total

    def __repr__(self) -> str:
        return f"<User(email={self.email})>"