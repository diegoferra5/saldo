"""Transaction hashing utilities for deduplication."""
import hashlib
from uuid import UUID
from datetime import date
from decimal import Decimal


def compute_transaction_hash(
    user_id: UUID,
    account_id: UUID,
    statement_id: UUID,
    transaction_date: date,
    description: str,
    amount_abs: Decimal | float,
    occurrence_index: int = 0
) -> str:
    """
    Compute SHA256 hash for transaction deduplication.

    Hash includes stable identifiers only:
    - user_id
    - account_id
    - statement_id (scopes uniqueness to specific statement)
    - transaction_date (full date)
    - description (normalized)
    - amount_abs (normalized to 2 decimals)
    - occurrence_index (allows multiple identical transactions in same statement)

    Returns:
        64-character hex string (SHA256)
    """
    if not user_id or not account_id or not statement_id:
        raise ValueError("user_id, account_id, and statement_id are required")
    if not isinstance(transaction_date, date):
        raise ValueError(f"transaction_date must be a date, got: {type(transaction_date)}")
    if description is None:
        description = ""

    # Normalize description (avoid hash differences from case/whitespace)
    description_norm = description.strip().upper()

    # Normalize amount to 2 decimals (avoid float/Decimal formatting differences)
    if isinstance(amount_abs, Decimal):
        amount_str = f"{amount_abs.quantize(Decimal('0.00'))}"
    else:
        amount_str = f"{float(amount_abs):.2f}"

    # Build deterministic string representation
    # Format: user_id:account_id:statement_id:YYYY-MM-DD:DESCRIPTION:amount:occurrence
    hash_input = (
        f"{user_id}:"
        f"{account_id}:"
        f"{statement_id}:"
        f"{transaction_date.isoformat()}:"
        f"{description_norm}:"
        f"{amount_str}:"
        f"{occurrence_index}"
    )

    return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()


def validate_hash_format(transaction_hash: str) -> bool:
    """
    Validate that a hash string is in correct SHA256 hex format.

    Returns:
        True if valid SHA256 hex string (64 chars), False otherwise
    """
    if not isinstance(transaction_hash, str):
        return False
    if len(transaction_hash) != 64:
        return False
    try:
        int(transaction_hash, 16)
        return True
    except ValueError:
        return False

