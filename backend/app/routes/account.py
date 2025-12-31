from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.account import Account
from app.schemas.account import AccountList, AccountType, AccountResponse, AccountCreate, AccountUpdate
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
    account, created = account_service.get_or_create_account(
        db=db,
        user_id=current_user.id,
        bank_name=account_data.bank_name,
        account_type=account_data.account_type.value,  # Convert Enum to string
        display_name=account_data.display_name
    )

    db.commit()
    db.refresh(account)

    # Set appropriate status code based on whether account was created
    response.status_code = 201 if created else 200

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


@router.patch("/{account_id}", response_model=AccountResponse, status_code=200)
def update_account(
    account_id: UUID,
    update_data: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update account details (partial update).

    Allows updating:
    - display_name: Friendly name for the account
    - is_active: Active status (soft delete if False)

    Note: bank_name and account_type cannot be changed (ignored if provided)

    Path parameters:
    - account_id: UUID of the account to update

    Request body (all fields optional, at least one required):
    - display_name: New display name
    - is_active: New active status

    Returns:
    - 200 OK with updated account
    - 404 Not Found if account doesn't exist or doesn't belong to user
    - 422 Validation Error if no fields provided

    Security:
    - Only owner can update their accounts
    """
    account = account_service.update_account(
        db = db,
        account_id = account_id,
        user_id = current_user.id,
        display_name = update_data.display_name,
        is_active = update_data.is_active
    )

    return account


@router.delete("/{account_id}", status_code=204)
def delete_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft-delete account (sets is_active=false).

    Preserves all historical data (statements, transactions).
    Idempotent: returns 204 even if account is already inactive.

    Path parameters:
    - account_id: UUID of the account to delete

    Returns:
    - 204 No Content on success
    - 404 Not Found if account doesn't exist or doesn't belong to user

    Security:
    - Only owner can delete their accounts
    - Returns 404 (not 403) to avoid leaking existence of accounts

    Note: This is a soft delete. Use PATCH to reactivate (is_active=true).
    """
    account_service.deactivate_account(
        db=db,
        account_id=account_id,
        user_id=current_user.id
    )

    return None
