from datetime import date
from uuid import UUID
from typing import List, Optional
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, func

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
    Convierte el dict del parser en un objeto Transaction en la DB.
    """
    # 1. Parsear la fecha completa
    transaction_date = parse_bbva_date(
        parser_dict['date'],
        statement_month
    )
    
    # 2. Validar que la fecha sea razonable
    if not validate_transaction_date(transaction_date, statement_month):
        raise ValueError(
            f"Transaction date {transaction_date} is too far from "
            f"statement month {statement_month}. Possible parsing error."
        )
    
    # 3. Calcular el hash para deduplicación
    transaction_hash = compute_transaction_hash(
        user_id=user_id,
        account_id=account_id,
        transaction_date=transaction_date,
        description=parser_dict['description'],
        amount_abs=parser_dict['amount_abs']
    )
    
    # 4. Convertir montos a Decimal
    amount_abs = Decimal(str(parser_dict['amount_abs']))
    amount = Decimal(str(parser_dict['amount'])) if parser_dict.get('amount') is not None else None
    saldo_operacion = Decimal(str(parser_dict['saldo_operacion'])) if parser_dict.get('saldo_operacion') is not None else None
    saldo_liquidacion = Decimal(str(parser_dict['saldo_liquidacion'])) if parser_dict.get('saldo_liquidacion') is not None else None
    
    # 5. Crear el objeto Transaction
    transaction = Transaction(
        user_id=user_id,
        account_id=account_id,
        statement_id=statement_id,
        date=parser_dict['date'],
        date_liquidacion=parser_dict.get('date_liquidacion'),
        transaction_date=transaction_date,
        description=parser_dict['description'],
        amount_abs=amount_abs,
        amount=amount,
        movement_type=parser_dict['movement_type'],
        needs_review=parser_dict['needs_review'],
        category=parser_dict.get('category'),
        saldo_operacion=saldo_operacion,
        saldo_liquidacion=saldo_liquidacion,
        transaction_hash=transaction_hash
    )
    
    # 6. Guardar en DB
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
    Obtiene transacciones de un usuario con filtros opcionales.
    """
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    
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
    
    query = query.order_by(Transaction.transaction_date.desc())
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
    Actualiza la clasificación de una transacción (correcciones manuales).
    """
    transaction = db.query(Transaction).filter(
        and_(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        )
    ).first()
    
    if not transaction:
        raise ValueError(
            f"Transaction {transaction_id} not found or does not belong to user {user_id}"
        )
    
    if movement_type is not None:
        transaction.movement_type = movement_type.value
        
        if movement_type == MovementType.CARGO:
            transaction.amount = -abs(transaction.amount_abs)
        elif movement_type == MovementType.ABONO:
            transaction.amount = abs(transaction.amount_abs)
        else:
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
    Obtiene conteo de transacciones por tipo (para dashboard).
    """
    results = db.query(
        Transaction.movement_type,
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.user_id == user_id
    ).group_by(
        Transaction.movement_type
    ).all()
    
    return {row.movement_type: row.count for row in results}
