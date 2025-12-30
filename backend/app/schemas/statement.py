from enum import Enum
from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from fastapi import Form

from app.schemas.account import AccountType


class ParsingStatus(str, Enum):
    """Enum for statement parsing status"""
    pending = "pending"
    processing = "processing"
    success = "success"
    failed = "failed"


class StatementUploadForm:
    """
    Form-data parser for statement uploads (multipart/form-data).
    This is NOT a Pydantic schema - it's a dependency that parses Form fields.

    Usage in endpoint:
        form: StatementUploadForm = Depends()
    """
    def __init__(
        self,
        statement_month: date = Form(..., description="Mes del estado de cuenta"),
        account_id: Optional[UUID] = Form(None, description="ID de la cuenta (opcional)"),
    ):
        self.statement_month = statement_month.replace(day=1)
        self.account_id = account_id


class StatementResponse(BaseModel):
    """Complete statement data (output)"""
    id: UUID
    user_id: UUID
    account_id: Optional[UUID] = None
    bank_name: str
    account_type: AccountType
    statement_month: date
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    file_name: str
    file_size_kb: Optional[int] = None
    parsing_status: ParsingStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "account_id": "123e4567-e89b-12d3-a456-426614174002",
                "bank_name": "BBVA",
                "account_type": "DEBIT",
                "statement_month": "2025-12-01",
                "period_start": "2025-12-01",
                "period_end": "2025-12-31",
                "file_name": "estado_cuenta_diciembre.pdf",
                "file_size_kb": 342,
                "parsing_status": "success",
                "error_message": None,
                "created_at": "2025-12-14T10:30:00",
                "updated_at": "2025-12-14T10:35:00",
                "processed_at": "2025-12-14T10:35:00"
            }
        }
    )


class StatementList(BaseModel):
    """Summarized statement data for lists (output)"""
    id: UUID
    account_id: Optional[UUID] = None
    bank_name: str
    account_type: AccountType
    statement_month: date
    file_name: str
    parsing_status: ParsingStatus
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "account_id": "123e4567-e89b-12d3-a456-426614174002",
                "bank_name": "BBVA",
                "account_type": "CREDIT",
                "statement_month": "2025-11-01",
                "file_name": "bbva_credito_nov.pdf",
                "parsing_status": "pending",
                "created_at": "2025-12-14T10:30:00"
            }
        }
    )


class StatementHealthResponse(BaseModel):
    """
    Statement reconciliation health check response.

    Compares PDF summary (from summary_data JSONB) vs actual DB transactions.
    """
    statement_id: UUID
    has_summary_data: bool
    threshold: Decimal  # Fixed threshold for reconciliation (e.g., "10.00")
    db_cash_flow: Decimal  # Sum of transactions.amount (signed) for this statement
    pdf_cash_flow: Optional[Decimal] = None  # deposits_amount - charges_amount from summary_data
    difference: Optional[Decimal] = None  # db_cash_flow - pdf_cash_flow
    is_reconciled: Optional[bool] = None  # True if abs(difference) < threshold
    warnings: List[str] = []  # e.g., ["NO_SUMMARY_DATA", "INCOMPLETE_DUE_TO_UNKNOWN"]

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "statement_id": "123e4567-e89b-12d3-a456-426614174000",
                "has_summary_data": True,
                "threshold": "10.00",
                "db_cash_flow": "-9006.28",
                "pdf_cash_flow": "-9006.28",
                "difference": "0.00",
                "is_reconciled": True,
                "warnings": []
            }
        }
    )
