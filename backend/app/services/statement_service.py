import os
import hashlib
import re
from datetime import datetime, date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import UploadFile, HTTPException

from app.models.statement import Statement


def sanitize_filename(filename: str) -> str:
    """
    Remove dangerous characters from filename.
    
    Args:
        filename: Original filename from upload
    
    Returns:
        Safe filename with only alphanumeric, dots, dashes, underscores
    """
    # Keep only safe characters
    safe = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Remove path components (../, ./, etc.)
    safe = os.path.basename(safe)
    
    # Ensure it ends with .pdf
    if not safe.lower().endswith('.pdf'):
        safe += '.pdf'
    
    return safe


def calculate_file_hash(file_content: bytes) -> str:
    """
    Calculate SHA-256 hash of file content for duplicate detection.
    
    Args:
        file_content: Raw bytes of the file
    
    Returns:
        Hexadecimal string of the hash
    """
    return hashlib.sha256(file_content).hexdigest()


def save_file_temporarily(file: UploadFile, user_id: str) -> tuple[str, int, bytes, str]:
    """
    Save uploaded PDF to temporary directory.
    
    Args:
        file: Uploaded file from FastAPI
        user_id: UUID of the user (for organizing files)
    
    Returns:
        Tuple of (file_path, file_size_kb, file_content, safe_filename)
    
    Raises:
        HTTPException: If file is not a PDF or is too large
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Read file content
    file_content = file.file.read()
    file_size_bytes = len(file_content)
    file_size_kb = file_size_bytes // 1024
    
    # Validate file size (max 10MB for MVP)
    max_size_mb = 10
    if file_size_kb > (max_size_mb * 1024):
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum size is {max_size_mb}MB"
        )
    
    # Sanitize original filename
    sanitized = sanitize_filename(file.filename)
    
    # Create temp directory structure: /tmp/statements/{user_id}/
    temp_dir = f"/tmp/statements/{user_id}"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Generate unique filename with timestamp to avoid collisions
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{sanitized}"
    file_path = os.path.join(temp_dir, safe_filename)
    
    # Write file to disk
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Return safe_filename (what's actually saved) instead of original
    return file_path, file_size_kb, file_content, safe_filename


def create_statement_record(
    db: Session,
    user_id: str,
    bank_name: str,
    account_type: str,
    statement_month: date,  # ← FIXED: was datetime, now date
    file_name: str,  # This should be the safe_filename from save_file_temporarily
    file_size_kb: int,
    file_hash: str,
    ip_address: Optional[str] = None
) -> Statement:
    """
    Create a new statement record in the database.
    
    Args:
        db: Database session
        user_id: UUID of the user
        bank_name: Name of the bank (BBVA, Santander, etc.)
        account_type: Type of account (debit, credit, investment)
        statement_month: Month of the statement (date, not datetime)
        file_name: Safe filename (what's actually saved on disk)
        file_size_kb: Size of file in KB
        file_hash: SHA-256 hash of file content
        ip_address: IP address of the user (optional)
    
    Returns:
        Created Statement object
    
    Raises:
        HTTPException: If duplicate statement exists
    """
    # Check for duplicate (same user + bank + account_type + month)
    existing = db.query(Statement).filter(
        Statement.user_id == user_id,
        Statement.bank_name == bank_name,
        Statement.account_type == account_type,
        Statement.statement_month == statement_month
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Statement for {bank_name} ({account_type}) - {statement_month.strftime('%B %Y')} already exists"
        )
    
    # Create new statement
    new_statement = Statement(
        user_id=user_id,
        bank_name=bank_name,
        account_type=account_type,
        statement_month=statement_month,
        file_name=file_name,  # This is now the safe_filename
        file_size_kb=file_size_kb,
        file_hash=file_hash,
        ip_address=ip_address,
        parsing_status="pending"
    )
    
    try:
        db.add(new_statement)
        db.commit()
        db.refresh(new_statement)
        return new_statement
    
    except IntegrityError as e:
        # Race condition: another request created the same statement
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Statement for {bank_name} ({account_type}) - {statement_month.strftime('%B %Y')} already exists"
        )


def get_user_statements(
    db: Session,
    user_id: str,
    bank_name: Optional[str] = None,
    account_type: Optional[str] = None
) -> list[Statement]:
    """
    Get all statements for a user with optional filters.
    
    Args:
        db: Database session
        user_id: UUID of the user
        bank_name: Optional filter by bank
        account_type: Optional filter by account type
    
    Returns:
        List of Statement objects
    """
    query = db.query(Statement).filter(Statement.user_id == user_id)
    
    if bank_name:
        query = query.filter(Statement.bank_name == bank_name)
    
    if account_type:
        query = query.filter(Statement.account_type == account_type)
    
    # Order by most recent first
    return query.order_by(Statement.created_at.desc()).all()


def get_statement_by_id(db: Session, statement_id: str, user_id: str) -> Statement:
    """
    Get a specific statement by ID, ensuring it belongs to the user.
    
    Args:
        db: Database session
        statement_id: UUID of the statement
        user_id: UUID of the user (for security check)
    
    Returns:
        Statement object
    
    Raises:
        HTTPException: If statement not found or doesn't belong to user
    """
    statement = db.query(Statement).filter(
        Statement.id == statement_id,
        Statement.user_id == user_id  # Security: ensure ownership
    ).first()
    
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")
    
    return statement


def delete_statement(db: Session, statement_id: str, user_id: str) -> None:
    """
    Delete a statement and its associated file.
    
    Args:
        db: Database session
        statement_id: UUID of the statement
        user_id: UUID of the user (for security check)
    
    Raises:
        HTTPException: If statement not found or doesn't belong to user
    """
    statement = get_statement_by_id(db, statement_id, user_id)
    
    # Delete the PDF file from /tmp if it still exists
    # Now we use the actual filename stored in DB
    file_path = f"/tmp/statements/{user_id}/{statement.file_name}"
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            # Log but don't fail (file might already be deleted)
            print(f"Warning: Could not delete file {file_path}: {e}")
    
    db.delete(statement)
    db.commit()