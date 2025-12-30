from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date 
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.account import AccountList, AccountType, AccountResponse
from app.services import account_service

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])

@router.get("/", response_model=List[AccountList], status_code=200)
async def get_accounts_list(
    bank_name: Optional[str] = Query(default=None, description="Filter by bank name"),
    account_type: Optional[str] = Query(default=None, description="Filter by account type (DEBIT/CREDIT)"),
    is_active: Optional[bool] = Query(default=True, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all accounts for authenticated user.

    Optional filters:
    - bank_name: Filter by specific bank (e.g., "BBVA", "Santander")
    - account_type: Filter by account type (accepts "debit", "DEBIT", "credit", "CREDIT")
    - is_active: Filter by active status (default: True)

    Returns accounts ordered by creation date (newest first).
    """
    accounts = account_service.list_user_accounts(
        db=db,
        user_id=current_user.id,
        bank_name=bank_name,
        account_type=account_type,  # Service normalizes to uppercase
        is_active=is_active
    )

    return accounts