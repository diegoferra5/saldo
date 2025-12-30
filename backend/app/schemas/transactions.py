from pydantic import BaseModel, ConfigDict, model_validator
from datetime import date as DateType, datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal
from enum import Enum


class MovementType(str, Enum):
    """Transaction movement type"""
    CARGO = "CARGO"      # Gasto/Cargo
    ABONO = "ABONO"      # Ingreso/Abono
    UNKNOWN = "UNKNOWN"  # Requiere clasificación manual


class TransactionResponse(BaseModel):
    """Complete transaction data (output)"""
    # IDs
    id: UUID
    user_id: UUID
    account_id: UUID
    statement_id: UUID

    # Dates
    date: str  # "11/NOV" - formato original del PDF
    date_liquidacion: Optional[str] = None  # "11/NOV" o None
    transaction_date: DateType  # 2025-11-11 - fecha parseada completa

    # Transaction details
    description: str
    amount_abs: Decimal  # Siempre positivo
    amount: Optional[Decimal] = None  # Con signo (neg=gasto, pos=ingreso, None=unknown)
    movement_type: MovementType
    needs_review: bool
    category: Optional[str] = None

    # Balances (del PDF, pueden no estar)
    saldo_operacion: Optional[Decimal] = None
    saldo_liquidacion: Optional[Decimal] = None

    # Metadata
    transaction_hash: str  # SHA256 para deduplicación
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "account_id": "123e4567-e89b-12d3-a456-426614174002",
                "statement_id": "123e4567-e89b-12d3-a456-426614174003",
                "date": "11/NOV",
                "date_liquidacion": "11/NOV",
                "transaction_date": "2025-11-11",
                "description": "STARBUCKS COFFEE",
                "amount_abs": 150.00,
                "amount": -150.00,
                "movement_type": "CARGO",
                "needs_review": False,
                "category": "Food & Dining",
                "saldo_operacion": 10948.46,
                "saldo_liquidacion": 10948.46,
                "transaction_hash": "a1b2c3d4...",
                "created_at": "2025-12-14T10:30:00",
                "updated_at": "2025-12-14T10:30:00"
            }
        }
    )


class TransactionList(BaseModel):
    """Summarized transaction data for lists (output)"""
    id: UUID
    account_id: UUID
    transaction_date: DateType
    description: str
    amount_abs: Decimal
    amount: Optional[Decimal] = None
    movement_type: MovementType
    category: Optional[str] = None
    needs_review: bool

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "account_id": "123e4567-e89b-12d3-a456-426614174002",
                "transaction_date": "2025-11-11",
                "description": "STARBUCKS COFFEE",
                "amount_abs": 150.00,
                "amount": -150.00,
                "movement_type": "CARGO",
                "category": "Food & Dining",
                "needs_review": False
            }
        }
    )


class TransactionUpdate(BaseModel):
    """Update transaction fields (manual fixes)."""
    category: Optional[str] = None
    needs_review: Optional[bool] = None
    movement_type: Optional[MovementType] = None

    @model_validator(mode="after")
    def check_at_least_one_field(self):
        if self.category is None and self.needs_review is None and self.movement_type is None:
            raise ValueError("At least one field must be provided for update")

        # Prevent setting to UNKNOWN (transactions should be classified as CARGO or ABONO)
        if self.movement_type == MovementType.UNKNOWN:
            raise ValueError("Cannot set movement_type to UNKNOWN. Use CARGO or ABONO to classify the transaction.")

        return self

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "category": "Entertainment",
                "needs_review": False,
                "movement_type": "CARGO"
            }
        }
    )


class TransactionStats(BaseModel):
    """Transaction statistics by type (output)"""
    count_cargo: int
    count_abono: int
    count_unknown: int
    total_cargo: Decimal  # Negative
    total_abono: Decimal  # Positive
    net_balance: Decimal

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "count_cargo": 45,
                "count_abono": 12,
                "count_unknown": 3,
                "total_cargo": -15750.50,
                "total_abono": 28000.00,
                "net_balance": 12249.50
            }
        }
    )


class BalanceValidationSummary(BaseModel):
    """PDF summary data from statement"""
    saldo_inicial: Decimal
    saldo_final: Decimal
    total_abonos: Decimal
    total_cargos: Decimal  # Negative

    model_config = ConfigDict(extra="forbid")


class BalanceValidationCalculated(BaseModel):
    """Calculated values from DB transactions"""
    total_abonos: Decimal
    total_cargos: Decimal  # Negative
    expected_final: Decimal
    calculated_final: Decimal

    model_config = ConfigDict(extra="forbid")


class BalanceValidationResult(BaseModel):
    """Validation result"""
    is_valid: bool
    difference: Decimal
    warnings: list[str]

    model_config = ConfigDict(extra="forbid")


class BalanceValidationResponse(BaseModel):
    """Balance validation response (output)"""
    statement_id: str
    statement_month: str
    summary: BalanceValidationSummary
    calculated: BalanceValidationCalculated
    validation: BalanceValidationResult

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "statement_id": "123e4567-e89b-12d3-a456-426614174000",
                "statement_month": "2025-01",
                "summary": {
                    "saldo_inicial": 8500.00,
                    "saldo_final": 10500.00,
                    "total_abonos": 5000.00,
                    "total_cargos": -3000.00
                },
                "calculated": {
                    "total_abonos": 5000.00,
                    "total_cargos": -3000.00,
                    "expected_final": 10500.00,
                    "calculated_final": 10500.00
                },
                "validation": {
                    "is_valid": True,
                    "difference": 0.00,
                    "warnings": []
                }
            }
        }
    )
