# Saldo - Bug Fix Roadmap
**Date:** December 20, 2025
**Goal:** Fix critical issues and prepare for endpoint development
**Total Time:** 4-5 hours (distributed across 3 phases)

---

## 🎯 Overview

This roadmap fixes the 3 critical bugs found in the technical review and creates the missing service layer needed for endpoints.

---

## Phase 1: Quick Fixes (30 minutes)
**When:** NOW (before anything else)
**Dependencies:** None
**Output:** Parser ready, enums consistent

### Task 1.1: Fix AccountType Enum Case Inconsistency (10 min)

**Problem:** Schema uses "DEBIT", DB expects "debit"

**Files to modify:**
- Database (Supabase SQL Editor)

**Steps:**

1. **Open Supabase Dashboard**
   - Go to SQL Editor

2. **Run Migration Script:**
```sql
-- Fix accounts table constraint
ALTER TABLE accounts
DROP CONSTRAINT IF EXISTS accounts_account_type_check;

ALTER TABLE accounts
ADD CONSTRAINT accounts_account_type_check
CHECK (account_type IN ('DEBIT', 'CREDIT'));

-- Fix statements table constraint
ALTER TABLE statements
DROP CONSTRAINT IF EXISTS statements_account_type_check;

ALTER TABLE statements
ADD CONSTRAINT statements_account_type_check
CHECK (account_type IN ('DEBIT', 'CREDIT', 'INVESTMENT'));

-- Update existing data (if any)
UPDATE accounts SET account_type = 'DEBIT' WHERE account_type = 'debit';
UPDATE accounts SET account_type = 'CREDIT' WHERE account_type = 'credit';

UPDATE statements SET account_type = 'DEBIT' WHERE account_type = 'debit';
UPDATE statements SET account_type = 'CREDIT' WHERE account_type = 'credit';
UPDATE statements SET account_type = 'INVESTMENT' WHERE account_type = 'investment';

-- Update default value for statements
ALTER TABLE statements ALTER COLUMN account_type SET DEFAULT 'DEBIT';
```

3. **Verify:**
```sql
-- Check constraints
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conname LIKE '%account_type%';

-- Should show: account_type IN ('DEBIT', 'CREDIT', 'INVESTMENT')
```

4. **Add INVESTMENT to AccountType Enum:**
```python
# File: backend/app/schemas/account.py
# Line 8-10

class AccountType(str, Enum):
    debit = "DEBIT"
    credit = "CREDIT"
    investment = "INVESTMENT"  # ← ADD THIS LINE
```

**Verification:**
- [ ] DB constraints updated to uppercase
- [ ] Existing data migrated (if any)
- [ ] AccountType enum includes INVESTMENT
- [ ] No errors when creating test account

---

### Task 1.2: Add `needs_review` to Parser Return Dict (5 min)

**Problem:** `parse_transaction_line()` doesn't return `needs_review` field

**File to modify:**
- `backend/app/utils/pdf_parser.py`

**Steps:**

1. **Open `pdf_parser.py`**

2. **Find `parse_transaction_line()` function (line 73)**

3. **Locate the return dict (line 148-159)**

4. **Add `needs_review` field:**
```python
# Line 148-159 (BEFORE)
result = {
    'date': fecha_operacion,
    'date_liquidacion': fecha_liquidacion,
    'description': description,
    'amount_abs': amount_abs,
    'movement_type': None,
    'saldo_operacion': saldo_operacion,
    'saldo_liquidacion': saldo_liquidacion
}

# Line 148-160 (AFTER)
result = {
    'date': fecha_operacion,
    'date_liquidacion': fecha_liquidacion,
    'description': description,
    'amount_abs': amount_abs,
    'movement_type': None,
    'needs_review': True,  # ← ADD THIS LINE (default True, will be updated by determine_transaction_type)
    'saldo_operacion': saldo_operacion,
    'saldo_liquidacion': saldo_liquidacion
}
```

**Verification:**
- [ ] `needs_review` field added to return dict
- [ ] Default value is `True`
- [ ] Parser still runs without errors

**Test:**
```python
# Run parser test
cd backend
source venv/bin/activate
python -c "
from app.utils.pdf_parser import parse_transaction_line
line = '11/NOV 11/NOV STARBUCKS COFFEE 150.00 10948.46 10948.46'
result = parse_transaction_line(line)
print('needs_review' in result)  # Should print: True
print(result['needs_review'])     # Should print: True
"
```

---

### Task 1.3: Create Date Helper Utility (10 min)

**Problem:** Parser returns '11/NOV', but Transaction model needs `date(2025, 11, 11)`

**File to create:**
- `backend/app/utils/date_helpers.py`

**Steps:**

1. **Create new file:**
```bash
touch backend/app/utils/date_helpers.py
```

2. **Add code:**
```python
# backend/app/utils/date_helpers.py

from datetime import date

# Map Spanish month abbreviations to month numbers
MONTH_MAP = {
    'ENE': 1,   # Enero
    'FEB': 2,   # Febrero
    'MAR': 3,   # Marzo
    'ABR': 4,   # Abril
    'MAY': 5,   # Mayo
    'JUN': 6,   # Junio
    'JUL': 7,   # Julio
    'AGO': 8,   # Agosto
    'SEP': 9,   # Septiembre
    'OCT': 10,  # Octubre
    'NOV': 11,  # Noviembre
    'DIC': 12   # Diciembre
}


def parse_bbva_date(date_str: str, statement_month: date) -> date:
    """
    Convert BBVA date format (DD/MMM) to full date object.

    BBVA PDFs only include day and month (e.g., '11/NOV'), not the year.
    We infer the year from the statement month, handling edge cases where
    transactions from the previous year appear in January statements.

    Args:
        date_str: Date string from PDF in format 'DD/MMM' (e.g., '11/NOV')
        statement_month: The statement period date (e.g., date(2025, 11, 1))

    Returns:
        Full date object with inferred year (e.g., date(2025, 11, 11))

    Examples:
        >>> parse_bbva_date('11/NOV', date(2025, 11, 1))
        date(2025, 11, 11)

        >>> # Edge case: January statement with December transaction
        >>> parse_bbva_date('28/DIC', date(2025, 1, 1))
        date(2024, 12, 28)  # Previous year!

    Raises:
        ValueError: If date_str format is invalid or month abbreviation unknown
    """
    try:
        # Parse date string
        day_str, month_abbr = date_str.split('/')
        day = int(day_str)

        # Get month number from abbreviation
        if month_abbr not in MONTH_MAP:
            raise ValueError(f"Unknown month abbreviation: {month_abbr}")

        month = MONTH_MAP[month_abbr]

        # Start with statement year
        year = statement_month.year

        # Handle year rollover
        # Example: Statement is January 2025, transaction is "28/DIC" (December)
        # This transaction happened in December 2024 (previous year)
        if month > statement_month.month:
            year -= 1

        return date(year, month, day)

    except ValueError as e:
        raise ValueError(f"Invalid date format '{date_str}': {e}")


def validate_transaction_date(transaction_date: date, statement_month: date) -> bool:
    """
    Validate that a transaction date is reasonable given the statement period.

    Transactions should be within 1 month before/after statement month.

    Args:
        transaction_date: The parsed transaction date
        statement_month: The statement period

    Returns:
        True if date is valid, False otherwise

    Examples:
        >>> validate_transaction_date(date(2025, 11, 15), date(2025, 11, 1))
        True

        >>> validate_transaction_date(date(2025, 10, 28), date(2025, 11, 1))
        True  # Last few days of previous month OK

        >>> validate_transaction_date(date(2023, 5, 15), date(2025, 11, 1))
        False  # Too far in past
    """
    # Allow transactions within ±2 months of statement month
    month_diff = abs(
        (transaction_date.year * 12 + transaction_date.month) -
        (statement_month.year * 12 + statement_month.month)
    )

    return month_diff <= 2
```

3. **Create unit tests:**
```bash
touch backend/tests/test_date_helpers.py
```

```python
# backend/tests/test_date_helpers.py

import pytest
from datetime import date
from app.utils.date_helpers import parse_bbva_date, validate_transaction_date


class TestParseBBVADate:
    """Test BBVA date parsing logic."""

    def test_same_month_and_year(self):
        """Transaction in same month as statement."""
        result = parse_bbva_date('11/NOV', date(2025, 11, 1))
        assert result == date(2025, 11, 11)

    def test_previous_month_same_year(self):
        """Transaction in previous month (no year rollover)."""
        result = parse_bbva_date('28/OCT', date(2025, 11, 1))
        assert result == date(2025, 10, 28)

    def test_year_rollover(self):
        """Transaction from previous year (Jan statement with Dec transaction)."""
        result = parse_bbva_date('28/DIC', date(2025, 1, 1))
        assert result == date(2024, 12, 28)

    def test_all_months(self):
        """Test all Spanish month abbreviations."""
        months = [
            ('15/ENE', date(2025, 6, 1), date(2025, 1, 15)),
            ('20/FEB', date(2025, 6, 1), date(2025, 2, 20)),
            ('05/MAR', date(2025, 6, 1), date(2025, 3, 5)),
            ('10/ABR', date(2025, 6, 1), date(2025, 4, 10)),
            ('25/MAY', date(2025, 6, 1), date(2025, 5, 25)),
            ('30/JUN', date(2025, 6, 1), date(2025, 6, 30)),
            ('15/JUL', date(2025, 6, 1), date(2025, 7, 15)),
            ('20/AGO', date(2025, 6, 1), date(2025, 8, 20)),
            ('05/SEP', date(2025, 6, 1), date(2025, 9, 5)),
            ('10/OCT', date(2025, 6, 1), date(2025, 10, 10)),
            ('25/NOV', date(2025, 6, 1), date(2025, 11, 25)),
            ('28/DIC', date(2025, 6, 1), date(2025, 12, 28)),
        ]

        for date_str, statement_month, expected in months:
            result = parse_bbva_date(date_str, statement_month)
            assert result == expected

    def test_invalid_format(self):
        """Test invalid date format raises error."""
        with pytest.raises(ValueError):
            parse_bbva_date('invalid', date(2025, 11, 1))

    def test_invalid_month(self):
        """Test unknown month abbreviation raises error."""
        with pytest.raises(ValueError):
            parse_bbva_date('11/XXX', date(2025, 11, 1))


class TestValidateTransactionDate:
    """Test transaction date validation."""

    def test_same_month(self):
        """Transaction in same month is valid."""
        assert validate_transaction_date(date(2025, 11, 15), date(2025, 11, 1))

    def test_previous_month(self):
        """Transaction in previous month is valid."""
        assert validate_transaction_date(date(2025, 10, 28), date(2025, 11, 1))

    def test_next_month(self):
        """Transaction in next month is valid."""
        assert validate_transaction_date(date(2025, 12, 5), date(2025, 11, 1))

    def test_too_far_past(self):
        """Transaction too far in past is invalid."""
        assert not validate_transaction_date(date(2023, 5, 15), date(2025, 11, 1))

    def test_too_far_future(self):
        """Transaction too far in future is invalid."""
        assert not validate_transaction_date(date(2027, 5, 15), date(2025, 11, 1))
```

**Verification:**
- [ ] File created: `backend/app/utils/date_helpers.py`
- [ ] Tests created: `backend/tests/test_date_helpers.py`
- [ ] All tests pass: `pytest backend/tests/test_date_helpers.py -v`

---

### Task 1.4: Create Hash Helper Utility (5 min)

**Problem:** Transaction model requires `transaction_hash` for deduplication

**File to create:**
- `backend/app/utils/hash_helpers.py`

**Steps:**

1. **Create new file:**
```bash
touch backend/app/utils/hash_helpers.py
```

2. **Add code:**
```python
# backend/app/utils/hash_helpers.py

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
```

3. **Create unit tests:**
```bash
touch backend/tests/test_hash_helpers.py
```

```python
# backend/tests/test_hash_helpers.py

import pytest
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.utils.hash_helpers import compute_transaction_hash, validate_hash_format


class TestComputeTransactionHash:
    """Test transaction hash computation."""

    @pytest.fixture
    def sample_data(self):
        """Sample transaction data for testing."""
        return {
            'user_id': UUID('123e4567-e89b-12d3-a456-426614174000'),
            'account_id': UUID('123e4567-e89b-12d3-a456-426614174001'),
            'transaction_date': date(2025, 11, 11),
            'description': 'STARBUCKS COFFEE',
            'amount_abs': 150.00
        }

    def test_hash_length(self, sample_data):
        """Hash should be 64 characters (SHA256 hex)."""
        hash_result = compute_transaction_hash(**sample_data)
        assert len(hash_result) == 64

    def test_hash_is_hex(self, sample_data):
        """Hash should be valid hexadecimal."""
        hash_result = compute_transaction_hash(**sample_data)
        int(hash_result, 16)  # Should not raise ValueError

    def test_deterministic(self, sample_data):
        """Same input should produce same hash."""
        hash1 = compute_transaction_hash(**sample_data)
        hash2 = compute_transaction_hash(**sample_data)
        assert hash1 == hash2

    def test_different_amount(self, sample_data):
        """Different amount should produce different hash."""
        hash1 = compute_transaction_hash(**sample_data)

        sample_data['amount_abs'] = 200.00
        hash2 = compute_transaction_hash(**sample_data)

        assert hash1 != hash2

    def test_different_description(self, sample_data):
        """Different description should produce different hash."""
        hash1 = compute_transaction_hash(**sample_data)

        sample_data['description'] = 'DIFFERENT STORE'
        hash2 = compute_transaction_hash(**sample_data)

        assert hash1 != hash2

    def test_different_date(self, sample_data):
        """Different date should produce different hash."""
        hash1 = compute_transaction_hash(**sample_data)

        sample_data['transaction_date'] = date(2025, 11, 12)
        hash2 = compute_transaction_hash(**sample_data)

        assert hash1 != hash2

    def test_different_user(self, sample_data):
        """Different user_id should produce different hash."""
        hash1 = compute_transaction_hash(**sample_data)

        sample_data['user_id'] = UUID('123e4567-e89b-12d3-a456-426614174999')
        hash2 = compute_transaction_hash(**sample_data)

        assert hash1 != hash2

    def test_different_account(self, sample_data):
        """Different account_id should produce different hash."""
        hash1 = compute_transaction_hash(**sample_data)

        sample_data['account_id'] = UUID('123e4567-e89b-12d3-a456-426614174999')
        hash2 = compute_transaction_hash(**sample_data)

        assert hash1 != hash2

    def test_decimal_amount(self, sample_data):
        """Should handle Decimal amounts."""
        sample_data['amount_abs'] = Decimal('150.00')
        hash_result = compute_transaction_hash(**sample_data)
        assert len(hash_result) == 64

    def test_float_precision(self, sample_data):
        """Float and Decimal with same value should produce same hash."""
        sample_data['amount_abs'] = 150.00
        hash1 = compute_transaction_hash(**sample_data)

        sample_data['amount_abs'] = Decimal('150.00')
        hash2 = compute_transaction_hash(**sample_data)

        assert hash1 == hash2


class TestValidateHashFormat:
    """Test hash format validation."""

    def test_valid_hash(self):
        """Valid 64-char hex string should pass."""
        assert validate_hash_format('a' * 64)
        assert validate_hash_format('0123456789abcdef' * 4)

    def test_invalid_length(self):
        """Wrong length should fail."""
        assert not validate_hash_format('a' * 63)
        assert not validate_hash_format('a' * 65)
        assert not validate_hash_format('')

    def test_invalid_characters(self):
        """Non-hex characters should fail."""
        assert not validate_hash_format('z' * 64)
        assert not validate_hash_format('not_a_hash' + 'a' * 54)

    def test_invalid_type(self):
        """Non-string input should fail."""
        assert not validate_hash_format(123)
        assert not validate_hash_format(None)
        assert not validate_hash_format(['a' * 64])
```

**Verification:**
- [ ] File created: `backend/app/utils/hash_helpers.py`
- [ ] Tests created: `backend/tests/test_hash_helpers.py`
- [ ] All tests pass: `pytest backend/tests/test_hash_helpers.py -v`

---

## ✅ Phase 1 Complete Checklist

- [ ] AccountType enum fixed (DB constraints uppercase)
- [ ] INVESTMENT added to AccountType enum
- [ ] `needs_review` added to parser return dict
- [ ] `date_helpers.py` created with tests
- [ ] `hash_helpers.py` created with tests
- [ ] All tests passing

**Verification Command:**
```bash
cd backend
source venv/bin/activate
pytest tests/test_date_helpers.py tests/test_hash_helpers.py -v
```

---

## Phase 2: Service Layer (2-3 hours)
**When:** After Phase 1 complete
**Dependencies:** Phase 1 utilities
**Output:** Transaction service ready for endpoints

### Task 2.1: Create Transaction Service (90 min)

**Goal:** Transform parser output → Transaction ORM instances

**File to create:**
- `backend/app/services/transaction_service.py`

**Steps:**

1. **Create service file:**
```bash
touch backend/app/services/transaction_service.py
```

2. **Add service code:**
```python
# backend/app/services/transaction_service.py

from datetime import date
from uuid import UUID
from typing import List, Optional
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.transaction import Transaction
from app.utils.date_helpers import parse_bbva_date, validate_transaction_date
from app.utils.hash_helpers import compute_transaction_hash
from app.schemas.transactions import MovementType


def create_transaction_from_parser_dict(
    parser_dict: dict,
    user_id: UUID,
    account_id: UUID,
    statement_id: UUID,
    statement_month: date,
    db: Session
) -> Transaction:
    """
    Convert parser output dict to Transaction ORM instance and save to database.

    This function bridges the gap between the PDF parser (which returns dicts)
    and the database (which expects Transaction ORM instances). It:
    1. Computes transaction_date from DD/MMM format + statement context
    2. Computes transaction_hash for deduplication
    3. Adds user_id, account_id, statement_id context
    4. Creates and saves Transaction instance

    Args:
        parser_dict: Output from pdf_parser.parse_transaction_line() containing:
            - date: str (e.g., '11/NOV')
            - date_liquidacion: Optional[str]
            - description: str
            - amount_abs: float
            - amount: Optional[float]
            - movement_type: str ('CARGO' | 'ABONO' | 'UNKNOWN')
            - needs_review: bool
            - saldo_operacion: Optional[float]
            - saldo_liquidacion: Optional[float]

        user_id: UUID of the user who owns this transaction
        account_id: UUID of the account this transaction belongs to
        statement_id: UUID of the statement this transaction was parsed from
        statement_month: Statement period date (for inferring transaction year)
        db: SQLAlchemy database session

    Returns:
        Transaction instance (committed to database with generated ID)

    Raises:
        ValueError: If date parsing fails or transaction date is invalid
        IntegrityError: If transaction_hash already exists (duplicate)

    Example:
        >>> parser_dict = {
        ...     'date': '11/NOV',
        ...     'date_liquidacion': '11/NOV',
        ...     'description': 'STARBUCKS COFFEE',
        ...     'amount_abs': 150.00,
        ...     'amount': -150.00,
        ...     'movement_type': 'CARGO',
        ...     'needs_review': False,
        ...     'saldo_operacion': 10948.46,
        ...     'saldo_liquidacion': 10948.46
        ... }
        >>> transaction = create_transaction_from_parser_dict(
        ...     parser_dict, user_id, account_id, statement_id,
        ...     date(2025, 11, 1), db
        ... )
        >>> transaction.transaction_date
        date(2025, 11, 11)
    """
    # 1. Parse transaction date from DD/MMM format
    transaction_date = parse_bbva_date(
        parser_dict['date'],
        statement_month
    )

    # 2. Validate date is reasonable
    if not validate_transaction_date(transaction_date, statement_month):
        raise ValueError(
            f"Transaction date {transaction_date} is too far from "
            f"statement month {statement_month}. Possible parsing error."
        )

    # 3. Compute deduplication hash
    transaction_hash = compute_transaction_hash(
        user_id=user_id,
        account_id=account_id,
        transaction_date=transaction_date,
        description=parser_dict['description'],
        amount_abs=parser_dict['amount_abs']
    )

    # 4. Convert amounts to Decimal (for database precision)
    amount_abs = Decimal(str(parser_dict['amount_abs']))
    amount = Decimal(str(parser_dict['amount'])) if parser_dict.get('amount') is not None else None
    saldo_operacion = Decimal(str(parser_dict['saldo_operacion'])) if parser_dict.get('saldo_operacion') is not None else None
    saldo_liquidacion = Decimal(str(parser_dict['saldo_liquidacion'])) if parser_dict.get('saldo_liquidacion') is not None else None

    # 5. Create Transaction instance
    transaction = Transaction(
        # Context (provided by caller)
        user_id=user_id,
        account_id=account_id,
        statement_id=statement_id,

        # Dates
        date=parser_dict['date'],  # Original format from PDF
        date_liquidacion=parser_dict.get('date_liquidacion'),
        transaction_date=transaction_date,  # Computed full date

        # Transaction details
        description=parser_dict['description'],
        amount_abs=amount_abs,
        amount=amount,

        # Classification
        movement_type=parser_dict['movement_type'],
        needs_review=parser_dict['needs_review'],
        category=parser_dict.get('category'),  # Usually None from parser

        # Balances (optional)
        saldo_operacion=saldo_operacion,
        saldo_liquidacion=saldo_liquidacion,

        # Deduplication
        transaction_hash=transaction_hash
    )

    # 6. Save to database
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


def get_transactions_by_user(
    user_id: UUID,
    db: Session,
    account_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    movement_type: Optional[MovementType] = None,
    needs_review: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Transaction]:
    """
    Query transactions with filters.

    Args:
        user_id: Filter by user (required for security)
        db: Database session
        account_id: Optional filter by account
        start_date: Optional filter by date >= start_date
        end_date: Optional filter by date <= end_date
        movement_type: Optional filter by CARGO/ABONO/UNKNOWN
        needs_review: Optional filter by review status
        limit: Max results to return (default 100)
        offset: Pagination offset (default 0)

    Returns:
        List of Transaction instances ordered by date (newest first)

    Example:
        >>> # Get all November 2025 transactions that need review
        >>> transactions = get_transactions_by_user(
        ...     user_id=user.id,
        ...     db=db,
        ...     start_date=date(2025, 11, 1),
        ...     end_date=date(2025, 11, 30),
        ...     needs_review=True
        ... )
    """
    # Base query (always filter by user for security)
    query = db.query(Transaction).filter(Transaction.user_id == user_id)

    # Apply optional filters
    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)

    if start_date is not None:
        query = query.filter(Transaction.transaction_date >= start_date)

    if end_date is not None:
        query = query.filter(Transaction.transaction_date <= end_date)

    if movement_type is not None:
        query = query.filter(Transaction.movement_type == movement_type.value)

    if needs_review is not None:
        query = query.filter(Transaction.needs_review == needs_review)

    # Order by date (newest first)
    query = query.order_by(Transaction.transaction_date.desc())

    # Apply pagination
    query = query.limit(limit).offset(offset)

    return query.all()


def update_transaction_classification(
    transaction_id: UUID,
    user_id: UUID,
    db: Session,
    movement_type: Optional[MovementType] = None,
    category: Optional[str] = None,
    needs_review: Optional[bool] = None
) -> Transaction:
    """
    Update transaction classification (manual user corrections).

    Args:
        transaction_id: ID of transaction to update
        user_id: ID of user (for security check)
        db: Database session
        movement_type: New movement type (CARGO/ABONO/UNKNOWN)
        category: New category
        needs_review: New review status

    Returns:
        Updated Transaction instance

    Raises:
        ValueError: If transaction not found or doesn't belong to user

    Example:
        >>> # User manually fixes UNKNOWN transaction
        >>> transaction = update_transaction_classification(
        ...     transaction_id=trans.id,
        ...     user_id=user.id,
        ...     db=db,
        ...     movement_type=MovementType.CARGO,
        ...     category='Dining',
        ...     needs_review=False
        ... )
    """
    # Fetch transaction (with security check)
    transaction = db.query(Transaction).filter(
        and_(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id  # Security: user can only update their own
        )
    ).first()

    if not transaction:
        raise ValueError(
            f"Transaction {transaction_id} not found or does not belong to user {user_id}"
        )

    # Update fields (only if provided)
    if movement_type is not None:
        transaction.movement_type = movement_type.value

        # Recalculate amount based on new type
        if movement_type == MovementType.CARGO:
            transaction.amount = -abs(transaction.amount_abs)
        elif movement_type == MovementType.ABONO:
            transaction.amount = abs(transaction.amount_abs)
        else:  # UNKNOWN
            transaction.amount = None

    if category is not None:
        transaction.category = category

    if needs_review is not None:
        transaction.needs_review = needs_review

    db.commit()
    db.refresh(transaction)

    return transaction


def count_transactions_by_type(user_id: UUID, db: Session) -> dict:
    """
    Get transaction counts by movement type for dashboard/stats.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Dict with counts: {'CARGO': 45, 'ABONO': 12, 'UNKNOWN': 3}

    Example:
        >>> stats = count_transactions_by_type(user.id, db)
        >>> print(f"You have {stats['UNKNOWN']} transactions to review")
    """
    from sqlalchemy import func

    results = db.query(
        Transaction.movement_type,
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.user_id == user_id
    ).group_by(
        Transaction.movement_type
    ).all()

    return {row.movement_type: row.count for row in results}
```

3. **Create unit tests:**
```bash
touch backend/tests/test_transaction_service.py
```

```python
# backend/tests/test_transaction_service.py

import pytest
from datetime import date
from uuid import uuid4
from decimal import Decimal

from app.services.transaction_service import (
    create_transaction_from_parser_dict,
    get_transactions_by_user,
    update_transaction_classification,
    count_transactions_by_type
)
from app.models.transaction import Transaction
from app.schemas.transactions import MovementType


@pytest.fixture
def sample_parser_dict():
    """Sample parser output."""
    return {
        'date': '11/NOV',
        'date_liquidacion': '11/NOV',
        'description': 'STARBUCKS COFFEE',
        'amount_abs': 150.00,
        'amount': -150.00,
        'movement_type': 'CARGO',
        'needs_review': False,
        'category': None,
        'saldo_operacion': 10948.46,
        'saldo_liquidacion': 10948.46
    }


@pytest.fixture
def sample_context():
    """Sample context data."""
    return {
        'user_id': uuid4(),
        'account_id': uuid4(),
        'statement_id': uuid4(),
        'statement_month': date(2025, 11, 1)
    }


class TestCreateTransactionFromParserDict:
    """Test parser dict → Transaction conversion."""

    def test_creates_transaction(self, db, sample_parser_dict, sample_context):
        """Should create Transaction instance with all fields."""
        transaction = create_transaction_from_parser_dict(
            parser_dict=sample_parser_dict,
            db=db,
            **sample_context
        )

        assert transaction.id is not None
        assert transaction.user_id == sample_context['user_id']
        assert transaction.account_id == sample_context['account_id']
        assert transaction.statement_id == sample_context['statement_id']
        assert transaction.transaction_date == date(2025, 11, 11)
        assert transaction.description == 'STARBUCKS COFFEE'
        assert transaction.amount_abs == Decimal('150.00')
        assert transaction.amount == Decimal('-150.00')
        assert transaction.movement_type == 'CARGO'
        assert transaction.needs_review is False
        assert len(transaction.transaction_hash) == 64

    def test_computes_transaction_date(self, db, sample_parser_dict, sample_context):
        """Should compute full date from DD/MMM format."""
        transaction = create_transaction_from_parser_dict(
            sample_parser_dict, db=db, **sample_context
        )

        assert transaction.transaction_date == date(2025, 11, 11)

    def test_handles_year_rollover(self, db, sample_parser_dict, sample_context):
        """Should handle transactions from previous year."""
        # January statement with December transaction
        sample_context['statement_month'] = date(2025, 1, 1)
        sample_parser_dict['date'] = '28/DIC'

        transaction = create_transaction_from_parser_dict(
            sample_parser_dict, db=db, **sample_context
        )

        assert transaction.transaction_date == date(2024, 12, 28)

    def test_computes_transaction_hash(self, db, sample_parser_dict, sample_context):
        """Should compute deduplication hash."""
        transaction = create_transaction_from_parser_dict(
            sample_parser_dict, db=db, **sample_context
        )

        assert len(transaction.transaction_hash) == 64
        assert transaction.transaction_hash.isalnum()

    def test_prevents_duplicates(self, db, sample_parser_dict, sample_context):
        """Should prevent duplicate transactions (same hash)."""
        # Create first transaction
        trans1 = create_transaction_from_parser_dict(
            sample_parser_dict, db=db, **sample_context
        )

        # Try to create duplicate (should raise IntegrityError)
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            create_transaction_from_parser_dict(
                sample_parser_dict, db=db, **sample_context
            )


class TestGetTransactionsByUser:
    """Test transaction querying with filters."""

    @pytest.fixture
    def create_test_transactions(self, db, sample_context):
        """Create sample transactions for testing."""
        transactions = [
            {**sample_parser_dict, 'date': '01/NOV', 'movement_type': 'CARGO'},
            {**sample_parser_dict, 'date': '15/NOV', 'movement_type': 'ABONO'},
            {**sample_parser_dict, 'date': '20/NOV', 'movement_type': 'UNKNOWN', 'needs_review': True},
        ]

        for trans_dict in transactions:
            create_transaction_from_parser_dict(trans_dict, db=db, **sample_context)

    def test_gets_user_transactions(self, db, sample_context, create_test_transactions):
        """Should return user's transactions."""
        transactions = get_transactions_by_user(
            user_id=sample_context['user_id'],
            db=db
        )

        assert len(transactions) == 3

    def test_filters_by_account(self, db, sample_context, create_test_transactions):
        """Should filter by account_id."""
        transactions = get_transactions_by_user(
            user_id=sample_context['user_id'],
            account_id=sample_context['account_id'],
            db=db
        )

        assert all(t.account_id == sample_context['account_id'] for t in transactions)

    def test_filters_by_movement_type(self, db, sample_context, create_test_transactions):
        """Should filter by movement type."""
        transactions = get_transactions_by_user(
            user_id=sample_context['user_id'],
            movement_type=MovementType.CARGO,
            db=db
        )

        assert all(t.movement_type == 'CARGO' for t in transactions)

    def test_filters_by_needs_review(self, db, sample_context, create_test_transactions):
        """Should filter by review status."""
        transactions = get_transactions_by_user(
            user_id=sample_context['user_id'],
            needs_review=True,
            db=db
        )

        assert len(transactions) == 1
        assert transactions[0].movement_type == 'UNKNOWN'


# ... more tests
```

**Verification:**
- [ ] Service file created with all functions
- [ ] Unit tests created
- [ ] Tests pass: `pytest backend/tests/test_transaction_service.py -v`

---

### Task 2.2: Create Statement Service (30 min)

**File:** `backend/app/services/statement_service.py`

(Implementation similar to transaction_service - details in next phase if needed)

---

## Phase 3: Integration & Validation (1 hour)
**When:** After Phase 2 complete
**Dependencies:** All previous phases
**Output:** Everything working end-to-end

### Task 3.1: Integration Test (30 min)

**File:** `backend/tests/test_integration.py`

Test the complete flow:
1. Create user, account
2. "Upload" PDF (use parser directly)
3. Create transactions via service
4. Query transactions
5. Update transaction classification
6. Verify database state

### Task 3.2: Update Parser to Use Service (15 min)

Update `pdf_parser.py` main block to use new service layer (if needed for testing).

### Task 3.3: Final Verification (15 min)

- [ ] All unit tests pass
- [ ] Integration test passes
- [ ] No database constraint violations
- [ ] Parser → Service → DB flow works
- [ ] Ready for endpoint development

---

## Timeline Summary

| Phase | Duration | Tasks | Output |
|-------|----------|-------|--------|
| **Phase 1** | 30 min | Fix enums, add utilities | ✅ Parser ready |
| **Phase 2** | 2-3 hrs | Create service layer | ✅ Service ready |
| **Phase 3** | 1 hr | Integration testing | ✅ End-to-end working |
| **TOTAL** | **4-5 hrs** | | **🚀 Ready for endpoints** |

---

## Success Criteria

By the end of this roadmap, you should have:

1. ✅ **No Critical Bugs**
   - AccountType enum consistent
   - Parser returns all required fields
   - Utilities created (date, hash)

2. ✅ **Service Layer Complete**
   - Parser dict → Transaction ORM conversion
   - Query functions with filters
   - Update functions for manual corrections

3. ✅ **All Tests Passing**
   - Unit tests for utilities
   - Unit tests for services
   - Integration test for full flow

4. ✅ **Ready for Endpoints**
   - Can create transactions from parser output
   - Can query transactions
   - Can update transaction classification
   - No database errors

---

## After This Roadmap

You'll be ready to build:

1. **Account Endpoints** (2 hours)
   - `POST /api/accounts`
   - `GET /api/accounts`
   - `PATCH /api/accounts/{id}`

2. **Statement Upload Endpoint** (3-4 hours)
   - `POST /api/statements/upload`
   - Use service layer you just created
   - Return StatementResponse

3. **Transaction Endpoints** (2-3 hours)
   - `GET /api/transactions` (use get_transactions_by_user)
   - `PATCH /api/transactions/{id}` (use update_transaction_classification)

**Total time to working API:** ~10 hours from now

---

## Quick Start Command

```bash
# Activate environment
cd /Users/diegoferra/Documents/ASTRAFIN/PROJECT/backend
source venv/bin/activate

# Run this roadmap
# Phase 1: Quick Fixes (30 min)
# 1. Fix AccountType in Supabase dashboard
# 2. Edit app/utils/pdf_parser.py (add needs_review)
# 3. Create app/utils/date_helpers.py
# 4. Create app/utils/hash_helpers.py
# 5. pytest tests/test_date_helpers.py tests/test_hash_helpers.py -v

# Phase 2: Service Layer (2-3 hrs)
# 1. Create app/services/transaction_service.py
# 2. pytest tests/test_transaction_service.py -v

# Phase 3: Integration (1 hr)
# 1. Create tests/test_integration.py
# 2. pytest tests/test_integration.py -v

# Done! Ready for endpoints 🚀
```

---

**Ready to start? Begin with Phase 1, Task 1.1!**
