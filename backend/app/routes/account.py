from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.account import Account
from app.schemas.account import AccountList, AccountType, AccountResponse, AccountCreate
from app.services import account_service

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])

@router.get("/", response_model=List[AccountList], status_code=200)
def get_accounts_list(
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


@router.post("/", response_model=AccountResponse)
def create_account(
    account_data: AccountCreate,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new account or return existing one (get-or-create pattern).

    Behavior:
    - If account exists (same bank_name + account_type), returns existing account
    - If account exists but is_active=False, reactivates it and returns
    - If account doesn't exist, creates new account
    - All accounts are scoped to the authenticated user

    Request body:
    - bank_name: Bank name (e.g., "BBVA", "Santander")
    - account_type: Account type (DEBIT or CREDIT)
    - display_name: Optional friendly name (e.g., "Mi cuenta principal")

    Returns:
    - 201 Created if account was created
    - 200 OK if account already existed

    Security:
    - Only creates accounts for authenticated user (current_user.id)
    """
    # Check if account already exists before calling get_or_create
    existing_account = db.query(Account).filter(
        Account.user_id == current_user.id,
        Account.bank_name == account_data.bank_name.strip(),
        Account.account_type == account_data.account_type.value.upper()
    ).first()

    account = account_service.get_or_create_account(
        db=db,
        user_id=current_user.id,
        bank_name=account_data.bank_name,
        account_type=account_data.account_type.value,  # Convert Enum to string
        display_name=account_data.display_name
    )

    db.commit()
    db.refresh(account)

    # Set appropriate status code
    if existing_account is None:
        response.status_code = 201  # Created
    else:
        response.status_code = 200  # OK (already existed)

    return account


@router.get("/{account_id}", response_model=AccountResponse, status_code=200)
def get_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific account by ID.

    Returns account details if it belongs to the authenticated user.

    Path parameters:
    - account_id: UUID of the account to retrieve

    Returns:
    - 200 OK with account details
    - 404 Not Found if account doesn't exist or doesn't belong to user

    Security:
    - Only returns account if it belongs to authenticated user
    - Returns 404 (not 403) to avoid leaking existence of accounts
    """
    account = account_service.get_account_by_id(
        db=db,
        account_id=account_id,
        user_id=current_user.id
    )

    return account
