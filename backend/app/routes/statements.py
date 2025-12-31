from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Literal  
from datetime import date
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.statement import StatementResponse, StatementList, StatementHealthResponse
from app.services import statement_service

router = APIRouter(prefix="/api/statements", tags=["Statements"])


@router.post("/upload", response_model=StatementResponse, status_code=201)
async def upload_statement(
    file: UploadFile = File(..., description="PDF statement file"),
    bank_name: str = Form(..., description="Bank name (BBVA, Santander, etc.)"),
    account_type: Literal["debit", "credit", "investment"] = Form(
        default="debit", 
        description="Account type: debit, credit, investment"
    ),
    statement_month: date = Form(..., description="Statement month (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Upload a bank statement PDF.
    
    Process:
    1. Validate and save file temporarily
    2. Calculate file hash (for duplicate detection)
    3. Create database record
    4. Return statement metadata
    
    Note: PDF is saved to /tmp and will be parsed later.
    """
    # Validate bank_name
    allowed_banks = ['BBVA', 'Santander', 'Banorte', 'Banamex', 'HSBC', 'Scotiabank']
    if bank_name not in allowed_banks:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid bank. Allowed: {', '.join(allowed_banks)}"
        )
    
    
    # Normalize statement_month to first day of month
    statement_month = statement_month.replace(day=1)
    
    # Get client IP address (for audit trail)
    ip_address = None
    if request:
        ip_address = request.client.host if request.client else None
    
    # Save file temporarily and get metadata
    file_path, file_size_kb, file_content, safe_filename = statement_service.save_file_temporarily(
        file=file,
        user_id=current_user.id
    )
    
    # Calculate file hash for duplicate detection
    file_hash = statement_service.calculate_file_hash(file_content)
    
    # Create database record
    # SECURITY: Use current_user.id from JWT, NOT from request params
    statement = statement_service.create_statement_record(
        db=db,
        user_id=current_user.id,  # From authenticated user
        bank_name=bank_name,
        account_type=account_type,
        statement_month=statement_month,
        file_name=safe_filename,  # Actual filename on disk
        file_size_kb=file_size_kb,
        file_hash=file_hash,
        ip_address=ip_address
    )
    
    return statement


@router.get("/", response_model=List[StatementList])
async def list_statements(
    bank_name: Optional[str] = None,
    account_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all statements for the authenticated user.
    
    Optional filters:
    - bank_name: Filter by specific bank
    - account_type: Filter by account type (debit, credit, investment)
    
    Returns statements ordered by creation date (newest first).
    """
    statements = statement_service.get_user_statements(
        db=db,
        user_id=current_user.id,
        bank_name=bank_name,
        account_type=account_type
    )
    
    return statements


@router.get("/{statement_id}/health", response_model=StatementHealthResponse)
async def get_statement_health(
    statement_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check statement reconciliation health.

    Compares PDF summary (from summary_data JSONB) vs actual DB transactions.

    Returns:
    - db_cash_flow: Sum of transactions.amount (signed) for this statement
    - pdf_cash_flow: deposits_amount - charges_amount from summary_data
    - difference: db_cash_flow - pdf_cash_flow
    - is_reconciled: True if abs(difference) < threshold (10.00)
    - warnings: List of warning codes:
        - "NO_SUMMARY_DATA": summary_data is NULL
        - "INCOMPLETE_DUE_TO_UNKNOWN": Statement has UNKNOWN transactions

    Security: Only returns health if statement belongs to authenticated user.
    """
    from decimal import Decimal

    result = statement_service.get_statement_health(
        db=db,
        statement_id=statement_id,
        user_id=current_user.id,
        threshold=Decimal("10.00")
    )

    return StatementHealthResponse(**result)


@router.get("/{statement_id}", response_model=StatementResponse)
async def get_statement(
    statement_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific statement by ID.
    
    Security: Only returns statement if it belongs to authenticated user.
    """
    statement = statement_service.get_statement_by_id(
        db=db,
        statement_id=str(statement_id),
        user_id=current_user.id
    )
    
    return statement


@router.delete("/{statement_id}", status_code=204)
async def delete_statement(
    statement_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a statement and its associated file.
    
    Security: Only deletes if statement belongs to authenticated user.
    """
    statement_service.delete_statement(
        db=db,
        statement_id=str(statement_id),
        user_id=current_user.id
    )
    
    # 204 No Content - successful deletion
    return None

@router.post("/{statement_id}/process")
def process_statement(
    statement_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Parse statement PDF and generate transactions.
    
    Process:
    1. Verify statement exists and belongs to user
    2. Extract transactions from PDF
    3. Classify as CARGO/ABONO/UNKNOWN
    4. Insert into database
    
    Returns:
        {
            "statement_id": "...",
            "status": "success",
            "transactions_found_lines": 45,
            "transactions_parsed": 43,
            "transactions_inserted": 40,
            "duplicates_skipped": 3
        }
    """
    # This already checks ownership and raises 404 if not found
    result = statement_service.process_statement(
        db=db,
        statement_id=statement_id,
        user_id=current_user.id
    )

    return result
