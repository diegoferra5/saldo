from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.transactions import (
    BalanceValidationResponse,
    CashFlowStats,
    DateRange,
    MovementType,
    TransactionList,
    TransactionResponse,
    TransactionStatsResponse,
    TransactionUpdate,
)
from app.services.transaction_service import (
    get_cash_flow_stats,
    get_transaction_by_id,
    get_transactions_by_user,
    update_transaction_classification,
    validate_statement_balance,
)


router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.get("/", response_model=List[TransactionList])
def list_transactions(
    # Filters
    account_id: Optional[UUID] = Query(None, description="Filter by account (UUID from GET /api/accounts/)"),
    statement_id: Optional[UUID] = Query(None, description="Filter by statement (UUID from GET /api/statements/)"),
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
    - statement_id: Filter by specific statement
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
        statement_id=statement_id,
        start_date=start_date,
        end_date=end_date,
        movement_type=movement_type,
        needs_review=needs_review,
        limit=limit,
        offset=offset,
    )

    return transactions


@router.get("/stats", response_model=TransactionStatsResponse)
def get_transaction_stats(
    # Filters
    account_id: Optional[UUID] = Query(None, description="Filter by account"),
    account_type: Optional[str] = Query(None, description="Filter by account type (debit|credit)"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    # Dependencies
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionStatsResponse:
    """
    Get cash flow statistics (income - expenses).

    Cash flow represents the net movement of money during a period.
    Does NOT include account balances - only transaction flows.

    Filters:
    - account_id: Filter by specific account
    - account_type: Filter by account type (debit | credit)
    - date_from: Start date (YYYY-MM-DD)
    - date_to: End date (YYYY-MM-DD)

    Returns:
    - date_range: Period analyzed (null if no date filters)
    - global: Overall cash flow stats with counts
    - by_account_type: Breakdown by account type (only keys with data)

    Notes:
    - cash_flow = total_abono + total_cargo (positive = surplus, negative = deficit)
    - UNKNOWN transactions are counted but excluded from totals (amount=None)
    - Reflects current DB state (includes manual corrections via PATCH)
    """
    # Validate date range
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from must be less than or equal to date_to",
        )

    # Get cash flow stats
    result = get_cash_flow_stats(
        user_id=current_user.id,
        db=db,
        account_id=account_id,
        account_type=account_type,
        date_from=date_from,
        date_to=date_to,
    )

    # Construct response using new schemas
    return TransactionStatsResponse(
        date_range=DateRange(start=result["date_range"]["from"], end=result["date_range"]["to"]),
        global_stats=CashFlowStats(**result["global"]),
        by_account_type={
            k: CashFlowStats(**v) for k, v in result["by_account_type"].items()
        }
    )


@router.get("/validate-balance", response_model=BalanceValidationResponse)
def validate_balance(
    statement_id: UUID = Query(..., description="Statement ID to validate"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BalanceValidationResponse:
    """
    Validate that transactions match statement PDF summary.

    Compares:
    - PDF summary (from statement.summary_data)
    - Current transaction totals in DB (includes manual corrections)

    Returns:
    - is_valid: True if difference < $10 threshold
    - warnings: List of discrepancies if validation fails

    Use case:
    - Call after POST /statements/{id}/process
    - If is_valid=false, show warning banner in UI
    - User can then review transactions with needs_review=true
    """
    try:
        result = validate_statement_balance(
            statement_id=statement_id,
            user_id=current_user.id,
            db=db,
        )
        return BalanceValidationResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


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
