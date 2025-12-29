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
    TransactionUpdate,
)
from app.services.transaction_service import (
    get_transactions_by_user,
    update_transaction_classification,
)


router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.get("/", response_model=List[TransactionList])
def list_transactions(
    # Filters
    account_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    movement_type: Optional[MovementType] = None,
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
