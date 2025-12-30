from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.transactions import (
    MovementType,
    TransactionList,
    TransactionResponse,
    TransactionStats,
    TransactionUpdate,
)
from app.services.transaction_service import (
    count_transactions_by_type,
    get_transaction_by_id,
    get_transactions_by_user,
    sum_transactions_by_type,
    update_transaction_classification,
)


router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.get("/", response_model=List[TransactionList])
def list_transactions(
    # Filters
    account_id: Optional[UUID] = Query(None, description="Filter by account (UUID from GET /api/accounts/)"),
    start_date: Optional[date] = Query(None, description="From date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="To date (YYYY-MM-DD)"),
    movement_type: Optional[MovementType] = Query(None, description="Filter by transaction type"),
    needs_review: Optional[bool] = Query(None, description="Filter by review status"),
    # Pagination with validation (endpoint validates input, service also caps to 200 as defense)
    limit: int = Query(50, ge=1, le=200, description="Max results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    # Dependencies
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[TransactionList]:
    """
    List user's transactions with optional filters.

    Filters:
    - account_id: Filter by specific account
    - start_date: From date (YYYY-MM-DD)
    - end_date: To date (YYYY-MM-DD)
    - movement_type: CARGO | ABONO | UNKNOWN
    - needs_review: Filter by review status

    Pagination:
    - limit: Results per page (default 50, max 200)
    - offset: Skip results (default 0)

    Returns transactions ordered by transaction_date DESC.
    """
    # Validate date range
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be less than or equal to end_date",
        )

    # Query transactions with filters
    transactions = get_transactions_by_user(
        user_id=current_user.id,
        db=db,
        account_id=account_id,
        start_date=start_date,
        end_date=end_date,
        movement_type=movement_type,
        needs_review=needs_review,
        limit=limit,
        offset=offset,
    )

    return transactions


@router.get("/{id}", response_model=TransactionResponse)
def get_transaction(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionResponse:
    """
    Get transaction details by ID.

    Returns full transaction details including all fields.
    Only returns transactions owned by the authenticated user.
    """
    transaction = get_transaction_by_id(
        transaction_id=id,
        user_id=current_user.id,
        db=db,
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return transaction


@router.get("/stats", response_model=TransactionStats)
def get_transaction_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionStats:
    """
    Get transaction statistics by movement type.

    Returns:
    - count_cargo: Number of expense transactions
    - count_abono: Number of income transactions
    - count_unknown: Number of unclassified transactions
    - total_cargo: Sum of expenses (negative)
    - total_abono: Sum of income (positive)
    - net_balance: Net balance (total_abono + total_cargo)

    Notes:
    - Reflects current DB state (includes manual corrections via PATCH)
    - UNKNOWN transactions are excluded from totals (amount=None)
    """
    # Get counts by type
    counts = count_transactions_by_type(user_id=current_user.id, db=db)

    # Get sums by type
    sums = sum_transactions_by_type(user_id=current_user.id, db=db)

    return TransactionStats(
        count_cargo=counts.get("CARGO", 0),
        count_abono=counts.get("ABONO", 0),
        count_unknown=counts.get("UNKNOWN", 0),
        total_cargo=sums["total_cargo"],
        total_abono=sums["total_abono"],
        net_balance=sums["net_balance"],
    )


@router.patch("/{id}", response_model=TransactionResponse)
def update_transaction(
    id: UUID,
    update_data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionResponse:
    """
    Update transaction classification.

    Allows manual correction of:
    - movement_type: CARGO | ABONO (UNKNOWN not allowed - use CARGO/ABONO to classify)
    - category: Custom category label
    - needs_review: Review flag

    Business rules (auto-applied):
    - If movement_type is set -> needs_review set to False
    - Amount is recalculated when movement_type changes
    """
    try:
        updated_transaction = update_transaction_classification(
            transaction_id=id,
            user_id=current_user.id,
            db=db,
            movement_type=update_data.movement_type,
            category=update_data.category,
            needs_review=update_data.needs_review,
        )
        return updated_transaction
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
