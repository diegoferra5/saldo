from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import date, datetime
from typing import Optional, Literal
from uuid import UUID

# Schema para upload (request)
class StatementUpload(BaseModel):
    bank_name: str = Field(
        ..., 
        min_length=2, 
        max_length=50, 
        description="Nombre del banco (BBVA, Santander, etc.)"
    )
    account_type: Literal["debit", "credit", "investment"] = Field(
        default="debit",
        description="Tipo de cuenta: debit (débito), credit (crédito), investment (inversión)"
    )
    statement_month: date = Field(
        ..., 
        description="Mes del estado de cuenta (se normaliza a YYYY-MM-01)"
    )

    @field_validator("bank_name")
    @classmethod
    def validate_bank_name(cls, v: str) -> str:
        """Normaliza y valida que el banco esté soportado"""
        allowed_banks = ["BBVA", "Santander", "Banorte", "Banamex", "HSBC", "Scotiabank"]
        normalized = v.strip()
        # Normaliza para aceptar "bbva", "BBVA", etc.
        normalized_upper = normalized.upper()
        allowed_upper = [b.upper() for b in allowed_banks]
        if normalized_upper not in allowed_upper:
            raise ValueError(f"Bank must be one of: {', '.join(allowed_banks)}")
        # Regresa el nombre con el casing canonico de allowed_banks
        return allowed_banks[allowed_upper.index(normalized_upper)]

    @field_validator("statement_month")
    @classmethod
    def validate_month(cls, v: date) -> date:
        """Normalizar al primer día del mes"""
        return v.replace(day=1)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bank_name": "BBVA",
                "account_type": "debit",
                "statement_month": "2025-12-01"
            }
        }
    )

# Schema para response (completo)
class StatementResponse(BaseModel):
    id: UUID
    user_id: UUID
    bank_name: str
    account_type: Literal["debit", "credit", "investment"]
    statement_month: date
    file_name: str
    file_size_kb: Optional[int]
    parsing_status: Literal["pending", "processing", "success", "failed"]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "bank_name": "BBVA",
                "account_type": "debit",
                "statement_month": "2025-12-01",
                "file_name": "estado_cuenta_diciembre.pdf",
                "file_size_kb": 342,
                "parsing_status": "success",
                "error_message": None,
                "created_at": "2025-12-14T10:30:00",
                "updated_at": "2025-12-14T10:35:00",
                "processed_at": "2025-12-14T10:35:00"
            }
        },
    )

# Schema para listar statements del usuario (resumen)
class StatementList(BaseModel):
    id: UUID
    bank_name: str
    account_type: Literal["debit", "credit", "investment"]
    statement_month: date
    file_name: str
    parsing_status: Literal["pending", "processing", "success", "failed"]
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "bank_name": "BBVA",
                "account_type": "credit",
                "statement_month": "2025-11-01",
                "file_name": "bbva_credito_nov.pdf",
                "parsing_status": "pending",
                "created_at": "2025-12-14T10:30:00"
            }
        },
    )