# app/services/statement_service.py

import os
import hashlib
import re
from datetime import datetime, date
from typing import Optional, List, Tuple
from uuid import UUID

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.statement import Statement
from app.models.account import Account

from app.services.account_service import get_or_create_account


from app.utils.pdf_parser import parse_bbva_debit_statement

from app.services.transaction_service import create_transactions_from_parser_output


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
        return new_statement
    except IntegrityError:
        db.rollback()
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

    # Delete local file if it exists
    file_path = f"/tmp/statements/{str(user_id)}/{statement.file_name}"
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Warning: Could not delete file {file_path}: {e}")

    db.delete(statement)
    db.commit()


# -------------------------
# PDF processing pipeline
# -------------------------

def process_statement(db: Session, statement_id: UUID, user_id: UUID) -> dict:
    """Parse a statement PDF, classify transactions, insert them, and update parsing status."""
    statement = get_statement_by_id(db, statement_id, user_id)

    pdf_path = f"/tmp/statements/{str(user_id)}/{statement.file_name}"
    if not os.path.exists(pdf_path):
        statement.parsing_status = "failed"
        statement.error_message = f"PDF file not found at {pdf_path}"
        db.commit()
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
        account = get_or_create_account(
            db=db,
            user_id=statement.user_id,
            bank_name=statement.bank_name,
            account_type=statement.account_type,
        )

        # Link statement to account
        statement.account_id = account.id
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

        # Mark failed (best effort)
        statement = (
            db.query(Statement)
            .filter(Statement.id == statement_id, Statement.user_id == user_id)
            .first()
        )
        if statement:
            statement.parsing_status = "failed"
            statement.error_message = str(e)
            db.commit()

        raise HTTPException(status_code=500, detail=f"Failed to process statement: {str(e)}")