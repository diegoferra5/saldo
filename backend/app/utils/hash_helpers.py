import hashlib
from uuid import UUID
from datetime import date
from decimal import Decimal


def compute_transaction_hash(
    user_id: UUID,
    account_id: UUID,
    transaction_date: date,
    description: str,
    amount_abs: Decimal | float
) -> str:
    """
    Compute SHA256 hash for transaction deduplication.

    The hash uniquely identifies a transaction using fields that should
    never change. If a user uploads the same PDF twice, transactions
    with identical hashes are considered duplicates and won't be re-inserted.

    Hash includes:
    - user_id: Ensures isolation between users
    - account_id: Same transaction in different accounts = different hash
    - transaction_date: Full date (not just DD/MMM from PDF)
    - description: Transaction description
    - amount_abs: Absolute amount (always positive)

    Does NOT include:
    - movement_type: Can be updated by user (UNKNOWN → CARGO)
    - category: User can change categorization
    - needs_review: Can be toggled
    - balances: Can vary if user uploads overlapping statements

    Args:
        user_id: UUID of the user who owns this transaction
        account_id: UUID of the account this transaction belongs to
        transaction_date: Full transaction date (not DD/MMM format)
        description: Transaction description from PDF
        amount_abs: Absolute transaction amount (always positive)

    Returns:
        64-character hex string (SHA256 hash)

    Examples:
        >>> from uuid import UUID
        >>> from datetime import date
        >>> user_id = UUID('123e4567-e89b-12d3-a456-426614174000')
        >>> account_id = UUID('123e4567-e89b-12d3-a456-426614174001')
        >>> hash1 = compute_transaction_hash(
        ...     user_id, account_id, date(2025, 11, 11),
        ...     'STARBUCKS COFFEE', 150.00
        ... )
        >>> len(hash1)
        64

        >>> # Same transaction → same hash
        >>> hash2 = compute_transaction_hash(
        ...     user_id, account_id, date(2025, 11, 11),
        ...     'STARBUCKS COFFEE', 150.00
        ... )
        >>> hash1 == hash2
        True

        >>> # Different amount → different hash
        >>> hash3 = compute_transaction_hash(
        ...     user_id, account_id, date(2025, 11, 11),
        ...     'STARBUCKS COFFEE', 200.00
        ... )
        >>> hash1 != hash3
        True
    """
    # Normalize amount to 2 decimal places (avoid float precision issues)
    if isinstance(amount_abs, Decimal):
        amount_str = str(amount_abs)
    else:
        amount_str = f"{float(amount_abs):.2f}"

    # Build hash input string
    # Format: user_id:account_id:YYYY-MM-DD:description:amount
    hash_input = (
        f"{str(user_id)}:"
        f"{str(account_id)}:"
        f"{transaction_date.isoformat()}:"
        f"{description}:"
        f"{amount_str}"
    )

    # Compute SHA256 hash
    hash_bytes = hashlib.sha256(hash_input.encode('utf-8')).digest()

    # Return as hex string
    return hash_bytes.hex()


def validate_hash_format(transaction_hash: str) -> bool:
    """
    Validate that a hash string is in correct format.

    Args:
        transaction_hash: Hash string to validate

    Returns:
        True if valid SHA256 hex string, False otherwise

    Examples:
        >>> validate_hash_format('a' * 64)
        True

        >>> validate_hash_format('not_a_hash')
        False

        >>> validate_hash_format('a' * 63)  # Too short
        False
    """
    if not isinstance(transaction_hash, str):
        return False

    if len(transaction_hash) != 64:
        return False

    # Check if all characters are valid hex
    try:
        int(transaction_hash, 16)
        return True
    except ValueError:
        return False
