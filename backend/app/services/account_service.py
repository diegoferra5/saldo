# app/services/account_service.py

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.account import Account


# Single source of truth for MVP
ALLOWED_ACCOUNT_TYPES = {"DEBIT", "CREDIT"}  # add "INVESTMENT" later if needed


def _normalize_bank_name(bank_name: str) -> str:
    """Normalize bank_name for consistent matching."""
    if not bank_name or not bank_name.strip():
        raise HTTPException(status_code=400, detail="bank_name is required")
    return bank_name.strip()


def _normalize_account_type(account_type: str) -> str:
    """Normalize and validate account_type for MVP."""
    if not account_type or not account_type.strip():
        raise HTTPException(status_code=400, detail="account_type is required")

    at = account_type.strip().upper()
    if at not in ALLOWED_ACCOUNT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid account_type. Allowed: {sorted(ALLOWED_ACCOUNT_TYPES)}",
        )
    return at


def get_account_by_id(db: Session, account_id: UUID, user_id: UUID) -> Account:
    """Return an account by id if it belongs to the user."""
    account = (
        db.query(Account)
        .filter(Account.id == account_id, Account.user_id == user_id)
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return account


def list_user_accounts(
    db: Session,
    user_id: UUID,
    bank_name: Optional[str] = None,
    account_type: Optional[str] = None,
    is_active: Optional[bool] = True,
) -> List[Account]:
    """List user accounts with optional filters."""
    query = db.query(Account).filter(Account.user_id == user_id)

    if bank_name:
        query = query.filter(Account.bank_name == _normalize_bank_name(bank_name))

    if account_type:
        query = query.filter(Account.account_type == _normalize_account_type(account_type))

    if is_active is not None:
        query = query.filter(Account.is_active == is_active)

    return query.order_by(Account.created_at.desc()).all()


def get_or_create_account(
    db: Session,
    user_id: UUID,
    bank_name: str,
    account_type: str,
    display_name: Optional[str] = None,
) -> Account:
    """
    Get an existing account (by user_id + bank_name + account_type), or create it.

    MVP behavior:
    - Only DEBIT/CREDIT allowed
    - If account exists but is inactive, reactivate it
    """
    bn = _normalize_bank_name(bank_name)
    at = _normalize_account_type(account_type)

    account = (
        db.query(Account)
        .filter(
            Account.user_id == user_id,
            Account.bank_name == bn,
            Account.account_type == at,
        )
        .first()
    )

    if account:
        # Reactivate if previously soft-deleted
        if not account.is_active:
            account.is_active = True
        # Optionally fill display_name if missing
        if display_name and not account.display_name:
            account.display_name = display_name.strip()
        db.flush()
        return account

    new_account = Account(
        user_id=user_id,
        bank_name=bn,
        account_type=at,
        display_name=display_name.strip() if display_name else None,
        is_active=True,
    )

    try:
        db.add(new_account)
        db.flush()  # ensure new_account.id exists without committing
        return new_account
    except IntegrityError:
        # Handle race condition if another request created it at the same time
        db.rollback()
        existing = (
            db.query(Account)
            .filter(
                Account.user_id == user_id,
                Account.bank_name == bn,
                Account.account_type == at,
            )
            .first()
        )
        if not existing:
            raise HTTPException(status_code=500, detail="Failed to create account")
        return existing


def update_account(
    db: Session,
    account_id: UUID,
    user_id: UUID,
    display_name: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Account:
    """Update user-editable fields on an account (MVP: display_name + is_active)."""
    account = get_account_by_id(db, account_id, user_id)

    if display_name is not None:
        dn = display_name.strip()
        account.display_name = dn if dn else None

    if is_active is not None:
        account.is_active = is_active

    db.commit()
    db.refresh(account)
    return account


def deactivate_account(db: Session, account_id: UUID, user_id: UUID) -> None:
    """Soft-delete an account by setting is_active=False (never hard delete in MVP)."""
    account = get_account_by_id(db, account_id, user_id)
    account.is_active = False
    db.commit()
