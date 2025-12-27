"""Date parsing utilities for BBVA statements."""
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
    # Early validation
    if not date_str or '/' not in date_str:
        raise ValueError(f"Invalid date format: {date_str}")

    try:
        # Normalize input (handle spaces and case)
        date_str = date_str.strip()
        day_str, month_abbr = [x.strip() for x in date_str.split('/', 1)]
        month_abbr = month_abbr.upper()

        # Parse day
        day = int(day_str)

        # Get month number from abbreviation
        month = MONTH_MAP.get(month_abbr)
        if not month:
            raise ValueError(f"Unknown month abbreviation: {month_abbr}")

        # Start with statement year
        year = statement_month.year

        # Handle year rollover
        # Example: Statement is January 2025, transaction is "28/DIC" (December)
        # This transaction happened in December 2024 (previous year)
        if month > statement_month.month:
            year -= 1

        return date(year, month, day)

    except Exception as e:
        raise ValueError(f"Invalid date format '{date_str}': {e}")


def validate_transaction_date(transaction_date: date, statement_month: date) -> bool:
    """
    Validate that a transaction date is reasonable given the statement period.

    Transactions should be within 2 months before/after statement month.

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


