"""
app/services/transaction_service.py

Service layer for Transactions:
- Convert parser dicts -> Transaction ORM rows
- Query with filters/pagination
- Manual classification updates
- Counts by movement_type

Design choices:
- movement_type is stored in DB as STRING: "CARGO" | "ABONO" | "UNKNOWN"
- amount_abs is always positive
- amount is:
    - negative for CARGO
    - positive for ABONO
    - None for UNKNOWN
- create_* functions use SAVEPOINT (begin_nested) + flush, so you can batch-insert
  and commit once at the end of statement processing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.transaction import Transaction  # aligns with your Transaction model 
from app.schemas.transactions import MovementType
from app.utils.date_helpers import parse_bbva_date, validate_transaction_date
from app.utils.hash_helpers import compute_transaction_hash


ALLOWED_MOVEMENT_TYPES = {"CARGO", "ABONO", "UNKNOWN"}


def _to_decimal(v: Any) -> Optional[Decimal]:
    """Convert numeric/string to Decimal safely. Returns None if v is None."""
    if v is None:
        return None
    # str(...) handles floats/ints/Decimal/strings without binary float artifacts in most practical cases
    return Decimal(str(v))


def _movement_type_to_db_value(movement_type: Any) -> str:
    """
    Accepts MovementType enum OR string and returns the DB string value.
    Raises ValueError if invalid.
    """
    if isinstance(movement_type, MovementType):
        mt = movement_type.value
    else:
        mt = str(movement_type)

    if mt not in ALLOWED_MOVEMENT_TYPES:
        raise ValueError(f"Invalid movement_type: {movement_type}. Must be one of {sorted(ALLOWED_MOVEMENT_TYPES)}")
    return mt


def _compute_signed_amount(amount_abs: Decimal, movement_type_db: str) -> Optional[Decimal]:
    """
    amount_abs: positive Decimal
    movement_type_db: "CARGO" | "ABONO" | "UNKNOWN"
    """
    if movement_type_db == "CARGO":
        return -abs(amount_abs)
    if movement_type_db == "ABONO":
        return abs(amount_abs)
    # UNKNOWN
    return None


def create_transaction_from_parser_dict(
    parser_dict: Dict[str, Any],
    user_id: UUID,
    account_id: UUID,
    statement_id: UUID,
    statement_month: date,
    db: Session,
) -> Optional[Transaction]:
    """
    Create ONE Transaction from parser output.

    Returns:
        Transaction if inserted
        None if duplicate detected (transaction_hash unique violation)

    Notes:
    - Uses SAVEPOINT + flush (no commit). Caller should commit once after batch insert.
    - Enforces movement_type must already be classified (not None).
    """
    # Basic required fields from parser
    required = ["date", "description", "amount_abs"]
    missing = [k for k in required if k not in parser_dict]
    if missing:
        raise ValueError(f"Missing required parser fields: {missing}")

    # 1) Parse & validate transaction_date
    transaction_date = parse_bbva_date(parser_dict["date"], statement_month)
    if not validate_transaction_date(transaction_date, statement_month):
        raise ValueError(
            f"Transaction date {transaction_date} is outside valid range for statement month {statement_month}"
        )

    # 2) movement_type must be present/valid
    if parser_dict.get("movement_type") is None:
        raise ValueError(
            "movement_type cannot be None. Ensure determine_transaction_type() was called "
            "on parser output before inserting."
        )
    movement_type_db = _movement_type_to_db_value(parser_dict["movement_type"])

    # 3) Convert numerics to Decimal FIRST (stable hashing + DB precision)
    amount_abs = _to_decimal(parser_dict["amount_abs"])
    if amount_abs is None:
        raise ValueError("amount_abs cannot be None")

    saldo_operacion = _to_decimal(parser_dict.get("saldo_operacion"))
    saldo_liquidacion = _to_decimal(parser_dict.get("saldo_liquidacion"))

    # 4) Signed amount derived from movement_type (UNKNOWN => None)
    amount = _compute_signed_amount(amount_abs, movement_type_db)

    # 5) needs_review: prefer parser value, else derive from movement_type
    needs_review = parser_dict.get("needs_review")
    if needs_review is None:
        needs_review = (movement_type_db == "UNKNOWN")
    else:
        needs_review = bool(needs_review)

    # 6) Compute transaction_hash using normalized amount_abs (Decimal)
    # Include occurrence_index to handle multiple identical transactions in same statement
    occurrence_index = parser_dict.get('_occurrence_index', 0)
    transaction_hash = compute_transaction_hash(
        user_id=user_id,
        account_id=account_id,
        statement_id=statement_id,
        transaction_date=transaction_date,
        description=str(parser_dict["description"]),
        amount_abs=amount_abs,
        occurrence_index=occurrence_index,
    )

    # 7) Build ORM object (match your model fields)
    tx = Transaction(
        user_id=user_id,
        account_id=account_id,
        statement_id=statement_id,
        date=str(parser_dict["date"]),
        date_liquidacion=parser_dict.get("date_liquidacion"),
        transaction_date=transaction_date,
        description=str(parser_dict["description"]),
        amount_abs=amount_abs,
        amount=amount,
        movement_type=movement_type_db,
        needs_review=needs_review,
        category=parser_dict.get("category"),
        saldo_operacion=saldo_operacion,
        saldo_liquidacion=saldo_liquidacion,
        transaction_hash=transaction_hash,
    )

    # 8) Insert with SAVEPOINT to safely skip duplicates in batch
    try:
        with db.begin_nested():  # SAVEPOINT
            db.add(tx)
            db.flush()  # triggers integrity checks now
        return tx
    except IntegrityError:
        # Duplicate hash or other constraint at row-level: skip this row
        # We don't rollback the whole session; SAVEPOINT handles row rollback.
        return None


def create_transactions_from_parser_output(
    parser_transactions: List[Dict[str, Any]],
    user_id: UUID,
    account_id: UUID,
    statement_id: UUID,
    statement_month: date,
    db: Session,
) -> Tuple[List[Transaction], int]:
    """
    Create MANY transactions. Intended for statement processing.

    Returns:
        (created_transactions, duplicates_skipped_count)

    Note:
    - No commit here; caller should db.commit() once after loop + statement status updates.
    - Handles duplicate transactions within same statement by tracking occurrence count
    """
    created: List[Transaction] = []
    duplicates = 0

    # Track occurrence count for identical transactions (same content, different occurrences)
    seen_content: Dict[str, int] = {}

    for d in parser_transactions:
        # Create content key (without occurrence index)
        content_key = f"{d.get('date')}:{d.get('description')}:{d.get('amount_abs')}"

        # Track occurrence index for this content
        occurrence_index = seen_content.get(content_key, 0)
        seen_content[content_key] = occurrence_index + 1

        # Add occurrence index to parser dict for hash computation
        d['_occurrence_index'] = occurrence_index

        tx = create_transaction_from_parser_dict(
            parser_dict=d,
            user_id=user_id,
            account_id=account_id,
            statement_id=statement_id,
            statement_month=statement_month,
            db=db,
        )
        if tx is None:
            duplicates += 1
        else:
            created.append(tx)

    return created, duplicates


def get_transactions_by_user(
    user_id: UUID,
    db: Session,
    account_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    movement_type: Optional[MovementType] = None,
    needs_review: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Transaction]:
    """
    Query transactions with optional filters.

    Security: always filters by user_id.
    """
    # Clamp to prevent abuse
    limit = min(max(limit, 1), 200)
    offset = max(offset, 0)

    q = db.query(Transaction).filter(Transaction.user_id == user_id)

    if account_id is not None:
        q = q.filter(Transaction.account_id == account_id)

    if start_date is not None:
        q = q.filter(Transaction.transaction_date >= start_date)

    if end_date is not None:
        q = q.filter(Transaction.transaction_date <= end_date)

    if movement_type is not None:
        q = q.filter(Transaction.movement_type == movement_type.value)

    if needs_review is not None:
        q = q.filter(Transaction.needs_review == needs_review)

    return q.order_by(Transaction.transaction_date.desc()).limit(limit).offset(offset).all()


def update_transaction_classification(
    transaction_id: UUID,
    user_id: UUID,
    db: Session,
    movement_type: Optional[MovementType] = None,
    category: Optional[str] = None,
    needs_review: Optional[bool] = None,
) -> Transaction:
    """
    Update user-editable fields on a transaction.

    Rules:
    - If movement_type changes:
        - amount is recalculated from amount_abs
        - if needs_review not provided, we auto-set:
            - True when movement_type == UNKNOWN
            - False otherwise
    - category updates as-is (string)
    """
    tx = (
        db.query(Transaction)
        .filter(and_(Transaction.id == transaction_id, Transaction.user_id == user_id))
        .first()
    )

    if not tx:
        raise ValueError(f"Transaction {transaction_id} not found or access denied")

    if movement_type is not None:
        movement_type_db = _movement_type_to_db_value(movement_type)
        tx.movement_type = movement_type_db
        tx.amount = _compute_signed_amount(tx.amount_abs, movement_type_db)

        # If caller didn't specify needs_review, derive it from movement_type
        if needs_review is None:
            tx.needs_review = (movement_type_db == "UNKNOWN")

    if category is not None:
        tx.category = category

    if needs_review is not None:
        tx.needs_review = bool(needs_review)

    # No commit here if you want route-level transaction control; but for single updates it’s fine to commit.
    db.commit()
    db.refresh(tx)
    return tx


def count_transactions_by_type(user_id: UUID, db: Session) -> Dict[str, int]:
    """
    Count transactions grouped by movement_type.
    Returns:
        {"CARGO": 45, "ABONO": 12, "UNKNOWN": 3}
    """
    rows = (
        db.query(
            Transaction.movement_type,
            func.count(Transaction.id).label("count"),
        )
        .filter(Transaction.user_id == user_id)
        .group_by(Transaction.movement_type)
        .all()
    )

    return {str(movement_type): int(count) for movement_type, count in rows}
