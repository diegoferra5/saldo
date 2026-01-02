# app/services/statement_service.py

import os
import hashlib
import re
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
import logging

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from app.models.statement import Statement
from app.models.account import Account
from app.models.transaction import Transaction

from app.services.account_service import get_or_create_account


from app.utils.pdf_parser import parse_bbva_debit_statement

from app.services.transaction_service import create_transactions_from_parser_output

logger = logging.getLogger(__name__)


# -------------------------
# Upload helpers
# -------------------------

def sanitize_filename(filename: str) -> str:
    """Return a safe filename for storage (remove path + dangerous chars)."""
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    safe = os.path.basename(safe)
    if not safe.lower().endswith(".pdf"):
        safe += ".pdf"
    return safe


def calculate_file_hash(file_content: bytes) -> str:
    """Return SHA-256 hex digest for file content (duplicate detection)."""
    return hashlib.sha256(file_content).hexdigest()


def save_file_temporarily(file: UploadFile, user_id: UUID) -> tuple[str, int, bytes, str]:
    """Save the uploaded PDF to /tmp/statements/{user_id}/ and return file metadata."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file_content = file.file.read()
    file_size_bytes = len(file_content)
    file_size_kb = file_size_bytes // 1024

    # Enforce max size for MVP
    max_size_mb = 10
    if file_size_kb > (max_size_mb * 1024):
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {max_size_mb}MB")

    sanitized = sanitize_filename(file.filename)

    # Store under /tmp for MVP
    temp_dir = f"/tmp/statements/{str(user_id)}"
    os.makedirs(temp_dir, exist_ok=True)

    # Prefix timestamp to prevent collisions
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{sanitized}"
    file_path = os.path.join(temp_dir, safe_filename)

    with open(file_path, "wb") as f:
        f.write(file_content)

    logger.info(f"Statement file saved | size_kb={file_size_kb}")

    return file_path, file_size_kb, file_content, safe_filename


# -------------------------
# Statements CRUD
# -------------------------

def create_statement_record(
    db: Session,
    user_id: UUID,
    bank_name: str,
    account_type: str,
    statement_month: date,
    file_name: str,
    file_size_kb: int,
    file_hash: str,
    ip_address: Optional[str] = None,
) -> Statement:
    """Create a Statement row with duplicate prevention for same (user, bank, type, month)."""
    # Normalize to match DB constraints (DEBIT/CREDIT)
    account_type = account_type.upper().strip()
    bank_name = bank_name.strip()

    existing = (
        db.query(Statement)
        .filter(
            Statement.user_id == user_id,
            Statement.bank_name == bank_name,
            Statement.account_type == account_type,
            Statement.statement_month == statement_month,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Statement for {bank_name} ({account_type}) - {statement_month.strftime('%B %Y')} already exists",
        )

    new_statement = Statement(
        user_id=user_id,
        bank_name=bank_name,
        account_type=account_type,
        statement_month=statement_month,
        file_name=file_name,
        file_size_kb=file_size_kb,
        file_hash=file_hash,
        ip_address=ip_address,
        parsing_status="pending",
    )

    try:
        db.add(new_statement)
        db.commit()
        db.refresh(new_statement)
        logger.info(
            f"Statement record created | "
            f"statement_id={new_statement.id} | "
            f"user_id={user_id} | "
            f"bank={bank_name} | "
            f"type={account_type}"
        )
        return new_statement
    except IntegrityError:
        db.rollback()
        logger.warning(
            f"Duplicate statement rejected | "
            f"user_id={user_id} | "
            f"bank={bank_name} | "
            f"type={account_type} | "
            f"month={statement_month.strftime('%Y-%m')}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Statement for {bank_name} ({account_type}) - {statement_month.strftime('%B %Y')} already exists",
        )


def get_user_statements(
    db: Session,
    user_id: UUID,
    bank_name: Optional[str] = None,
    account_type: Optional[str] = None,
) -> List[Statement]:
    """Return statements for a user with optional bank/type filters."""
    query = db.query(Statement).filter(Statement.user_id == user_id)

    if bank_name:
        query = query.filter(Statement.bank_name == bank_name.strip())

    if account_type:
        query = query.filter(Statement.account_type == account_type.upper().strip())

    return query.order_by(Statement.created_at.desc()).all()


def get_statement_by_id(db: Session, statement_id: UUID, user_id: UUID) -> Statement:
    """Return a statement by id if it belongs to the given user."""
    statement = (
        db.query(Statement)
        .filter(Statement.id == statement_id, Statement.user_id == user_id)
        .first()
    )
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")
    return statement


def delete_statement(db: Session, statement_id: UUID, user_id: UUID) -> None:
    """Delete a statement row and its PDF file (best-effort)."""
    statement = get_statement_by_id(db, statement_id, user_id)

    # Delete local file using shared cleanup function
    _cleanup_statement_file(user_id=user_id, file_name=statement.file_name, statement_id=statement_id)

    db.delete(statement)
    db.commit()
    logger.info(f"Statement deleted | statement_id={statement_id}")


def _cleanup_statement_file(user_id: UUID, file_name: str, statement_id: UUID = None) -> None:
    """
    Best-effort cleanup of statement PDF file.

    Called automatically after processing (success or failure) to remove PII from disk.
    Does NOT raise exceptions - logs warnings only.

    Args:
        user_id: User UUID (for directory path)
        file_name: Filename only (NOT full path, for security)
        statement_id: Optional statement ID for safe logging (preferred over file_name)
    """
    file_path = f"/tmp/statements/{str(user_id)}/{file_name}"

    # Use statement_id for logs if available (safer than file_name which may contain PII)
    log_identifier = f"statement_id={statement_id}" if statement_id else f"file=*.pdf"

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Statement file cleaned up | {log_identifier}")
        else:
            # File already deleted or never existed - not an error, just log at INFO level
            logger.info(f"Statement file already removed | {log_identifier}")
    except (FileNotFoundError, PermissionError, OSError) as e:
        # Best-effort: log but don't crash
        logger.warning(
            f"Failed to cleanup statement file | "
            f"{log_identifier} | "
            f"error={type(e).__name__}"
        )
    except Exception as e:
        # Catch any unexpected errors
        logger.warning(
            f"Unexpected error during file cleanup | "
            f"{log_identifier} | "
            f"error={type(e).__name__}"
        )


# -------------------------
# PDF processing pipeline
# -------------------------

def process_statement(db: Session, statement_id: UUID, user_id: UUID) -> dict:
    """
    Parse a statement PDF, classify transactions, insert them, and update parsing status.

    Automatically cleans up the PDF file after processing (success or failure) to remove PII.

    Args:
        db: Database session
        statement_id: Statement UUID to process
        user_id: User UUID (for security check)

    Returns:
        Dict with processing results (transactions_parsed, transactions_inserted, etc.)

    Raises:
        HTTPException: If processing fails
    """
    start_time = datetime.utcnow()

    # Log start - include user_id only in DEBUG mode for privacy
    if logger.isEnabledFor(logging.DEBUG):
        logger.info(
            f"Statement processing started | "
            f"statement_id={statement_id} | "
            f"user_id={user_id}"
        )
    else:
        logger.info(f"Statement processing started | statement_id={statement_id}")

    statement = get_statement_by_id(db, statement_id, user_id)

    # Store filename early for cleanup in finally block (even if processing fails)
    file_name_for_cleanup = statement.file_name

    pdf_path = f"/tmp/statements/{str(user_id)}/{statement.file_name}"
    if not os.path.exists(pdf_path):
        statement.parsing_status = "failed"
        statement.error_message = "PDF file not found on server"
        db.commit()
        logger.error(
            f"Statement processing failed - file not found | "
            f"statement_id={statement_id} | "
        )
        raise HTTPException(status_code=500, detail="Statement file missing on server")

    try:
        # Mark processing
        statement.parsing_status = "processing"
        statement.error_message = None
        db.flush()  # keep everything in one DB transaction

        # Validate parser availability (MVP: only BBVA DEBIT supported)
        if statement.bank_name.upper() != "BBVA" or statement.account_type.upper() != "DEBIT":
            raise HTTPException(
                status_code=400,
                detail=f"Parser not yet implemented for {statement.bank_name} {statement.account_type}. "
                       f"Currently supported: BBVA DEBIT only."
            )

        # Parse PDF using orchestrated parser function
        result = parse_bbva_debit_statement(pdf_path, debug=False)

        parsed = result["transactions"]
        summary = result["summary"]

        if not summary:
            raise ValueError("Failed to extract statement summary from PDF")

        # Ensure Account exists (get or create)
        account, _ = get_or_create_account(
            db=db,
            user_id=statement.user_id,
            bank_name=statement.bank_name,
            account_type=statement.account_type,
        )

        # Link statement to account
        statement.account_id = account.id

        # Store PDF summary data for validation
        statement.summary_data = summary
        db.flush()

        # Insert transactions in batch (savepoints + flush, no commit inside)
        created, duplicates = create_transactions_from_parser_output(
            parser_transactions=parsed,
            user_id=statement.user_id,
            account_id=account.id,
            statement_id=statement.id,
            statement_month=statement.statement_month,
            db=db,
        )

        # Mark success
        statement.parsing_status = "success"
        statement.processed_at = datetime.utcnow()

        # Single commit for atomicity
        db.commit()

        # Calculate duration
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Log success - user_id only in DEBUG for privacy
        if logger.isEnabledFor(logging.DEBUG):
            logger.info(
                f"Statement processing complete | "
                f"statement_id={statement.id} | "
                f"user_id={user_id} | "
                f"tx_parsed={len(parsed)} | "
                f"tx_inserted={len(created)} | "
                f"duplicates={duplicates} | "
                f"warnings_count={len(result.get('warnings', []))} | "
                f"duration_ms={duration_ms}"
            )
        else:
            logger.info(
                f"Statement processing complete | "
                f"statement_id={statement.id} | "
                f"tx_parsed={len(parsed)} | "
                f"tx_inserted={len(created)} | "
                f"duplicates={duplicates} | "
                f"warnings_count={len(result.get('warnings', []))} | "
                f"duration_ms={duration_ms}"
            )

        return {
            "statement_id": str(statement.id),
            "status": "success",
            "transactions_parsed": len(parsed),
            "transactions_inserted": len(created),
            "duplicates_skipped": duplicates,
            "warnings": result.get("warnings", []),
        }

    except Exception as e:
        db.rollback()

        # Calculate duration even on failure
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Log error - level determines PII exposure
        # DEBUG: full details (str(e) + traceback) - only for local development
        # INFO/WARNING/ERROR: only error type - safe for production logs
        is_debug = logger.isEnabledFor(logging.DEBUG)

        if is_debug:
            # Development: include str(e), traceback, and user_id for debugging
            logger.error(
                f"Statement processing failed | "
                f"statement_id={statement_id} | "
                f"user_id={user_id} | "
                f"error={type(e).__name__} | "
                f"duration_ms={duration_ms} | "
                f"message={str(e)}",  # Only in DEBUG mode
                exc_info=True  # Include full traceback in DEBUG
            )
        else:
            # Production: NO str(e), NO traceback, NO user_id (privacy-first)
            logger.error(
                f"Statement processing failed | "
                f"statement_id={statement_id} | "
                f"error={type(e).__name__} | "
                f"duration_ms={duration_ms}"
            )

        # Mark failed (best effort)
        statement = (
            db.query(Statement)
            .filter(Statement.id == statement_id, Statement.user_id == user_id)
            .first()
        )
        if statement:
            statement.parsing_status = "failed"
            # Store only error type (safe), NOT str(e) which may contain PII
            statement.error_message = f"Processing failed: {type(e).__name__}"
            db.commit()

        # Return generic error to client (no PII leakage)
        raise HTTPException(
            status_code=500,
            detail="Failed to process statement. Please check the file and try again."
        )

    finally:
        # Always cleanup PDF file (success or failure) to remove PII from disk
        # Use pre-stored filename (safe even if statement becomes None or errors occur)
        _cleanup_statement_file(user_id=user_id, file_name=file_name_for_cleanup, statement_id=statement_id)


# -------------------------
# Statement Health / Reconciliation
# -------------------------

def get_statement_health(
    db: Session,
    statement_id: UUID,
    user_id: UUID,
    threshold: Decimal = Decimal("10.00"),
) -> Dict[str, Any]:
    """
    Check statement reconciliation health.

    Compares PDF summary (from summary_data JSONB) vs actual DB transactions.

    Args:
        db: Database session
        statement_id: Statement UUID
        user_id: User UUID (for security - ensure statement belongs to user)
        threshold: Reconciliation threshold (default 10.00)

    Returns:
        Dict with:
        - statement_id
        - has_summary_data
        - threshold
        - db_cash_flow: sum of transactions.amount (signed) for this statement
        - pdf_cash_flow: deposits_amount - charges_amount from summary_data
        - difference: db_cash_flow - pdf_cash_flow
        - is_reconciled: True if abs(difference) < threshold
        - warnings: list of warning codes

    Raises:
        HTTPException 404 if statement not found or doesn't belong to user
    """
    # Get statement (security check)
    statement = get_statement_by_id(db, statement_id, user_id)

    warnings = []

    # Calculate db_cash_flow: sum of amount (signed) for this statement, excluding UNKNOWN (amount=NULL)
    db_cash_flow = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.statement_id == statement_id,
            Transaction.user_id == user_id,
            Transaction.amount.isnot(None)  # Exclude UNKNOWN
        )
        .scalar()
    ) or Decimal("0")

    # Check for UNKNOWN transactions
    unknown_count = (
        db.query(func.count(Transaction.id))
        .filter(
            Transaction.statement_id == statement_id,
            Transaction.user_id == user_id,
            Transaction.movement_type == "UNKNOWN"
        )
        .scalar()
    ) or 0

    if unknown_count > 0:
        warnings.append("INCOMPLETE_DUE_TO_UNKNOWN")

    # Check if summary_data exists
    has_summary_data = statement.summary_data is not None

    if not has_summary_data:
        warnings.append("NO_SUMMARY_DATA")
        return {
            "statement_id": statement_id,
            "has_summary_data": False,
            "threshold": threshold,
            "db_cash_flow": db_cash_flow,
            "pdf_cash_flow": None,
            "difference": None,
            "is_reconciled": None,
            "warnings": warnings,
        }

    # Extract PDF cash flow from summary_data
    summary_data = statement.summary_data
    deposits_amount = Decimal(str(summary_data.get("deposits_amount", 0)))
    charges_amount = Decimal(str(summary_data.get("charges_amount", 0)))

    # pdf_cash_flow = deposits (positive) - charges (absolute value, since charges_amount is stored positive)
    # Note: charges_amount in summary_data is stored as positive value (e.g., 56862.50)
    # So we need to subtract it to get the cash flow
    pdf_cash_flow = deposits_amount - charges_amount

    # Calculate difference
    difference = db_cash_flow - pdf_cash_flow

    # Determine if reconciled
    is_reconciled = abs(difference) < threshold

    # Log reconciliation status - user_id only in DEBUG for privacy
    log_level = logger.info if is_reconciled else logger.warning

    if logger.isEnabledFor(logging.DEBUG):
        log_level(
            f"Statement reconciliation check | "
            f"statement_id={statement_id} | "
            f"user_id={user_id} | "
            f"is_reconciled={is_reconciled} | "
            f"difference_abs={abs(difference)} | "
            f"threshold={threshold} | "
            f"unknown_count={unknown_count}"
        )
    else:
        log_level(
            f"Statement reconciliation check | "
            f"statement_id={statement_id} | "
            f"is_reconciled={is_reconciled} | "
            f"difference_abs={abs(difference)} | "
            f"threshold={threshold} | "
            f"unknown_count={unknown_count}"
        )

    return {
        "statement_id": statement_id,
        "has_summary_data": True,
        "threshold": threshold,
        "db_cash_flow": db_cash_flow,
        "pdf_cash_flow": pdf_cash_flow,
        "difference": difference,
        "is_reconciled": is_reconciled,
        "warnings": warnings,
    }