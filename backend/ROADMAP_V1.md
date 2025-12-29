# 🗺️ Saldo Backend V1 - Roadmap Definitivo

> **Versión:** 1.0 MVP
> **Branch actual:** `feature/transactions-account-endpoints`
> **Última actualización:** 2025-12-29
> **Filosofía:** Slow but safe, no over-engineering, production-ready

---

## 📊 Estado del Proyecto

### ✅ Completado (Foundation)
- ✅ Infrastructure & Database Setup (SSL para Supabase)
- ✅ SQLAlchemy Models (User, Account, Statement, Transaction)
- ✅ Auth Router (`/api/auth/*`) - Register, Login, /me
- ✅ Statements Router (`/api/statements/*`) - Full CRUD + Processing
- ✅ PDF Parser (BBVA Débito con clasificación inteligente)
- ✅ Transaction Service (con deduplicación por hash + occurrence_index)
- ✅ Statement Service (upload, process, validaciones)

### 🔴 En Progreso (Phase 1)
- **Transactions Router** - 5 endpoints con balance validation
- **Accounts Router** - 5 endpoints con soft delete
- **PDF Cleanup** - Auto-delete con logging

### 🟢 Scope V1 (Lo que SÍ incluye)
- ✅ CRUD completo para Transactions y Accounts
- ✅ Balance validation (detectar errores de clasificación)
- ✅ PDF cleanup automático
- ✅ Error handling estandarizado
- ✅ Seed data script para demos
- ✅ Manual testing exhaustivo

### 🔵 Fuera de Scope V1 (Pospuesto a V1.1)
- ❌ Multi-bank parser support (solo BBVA Debit en V1)
- ❌ Bank/type selector en upload (hardcoded por ahora)
- ❌ Automated tests (pytest) - solo manual testing
- ❌ Confidence scores en transacciones
- ❌ Categorías custom de usuario

---

## 🎯 PHASE 1: CRUD Endpoints (15 horas)

### Milestone 1.1: Transactions Router 🔴 AHORA
**Tiempo:** 5 horas | **Complejidad:** Media | **Status:** In Progress

#### Decisiones Clave V1
1. ✅ **Balance Validation Incluida** - Endpoint para detectar errores de clasificación
2. ✅ **Stats Ampliadas** - No solo conteos, también sumas totales
3. ✅ **Limit Cap a 200** (no 500) - Seguridad y performance
4. ✅ **Default Limit: 50** - Balance entre UX y carga
5. ✅ **5 Endpoints** (no 4) - Agregamos validate-balance

---

#### Endpoints a Implementar

##### 1. `GET /api/transactions/` - Lista con filtros
**Descripción:** Endpoint principal para UI de transacciones

**Query Params:**
```python
account_id: Optional[UUID] = None
start_date: Optional[date] = None
end_date: Optional[date] = None
movement_type: Optional[MovementType] = None  # CARGO | ABONO | UNKNOWN
needs_review: Optional[bool] = None
limit: int = 50  # Default 50, Max 200
offset: int = 0  # Min 0
```

**Validaciones:**
- ✅ `limit`: Clamp entre 1 y 200 (capear silenciosamente, no error)
- ✅ `offset`: Max(0, offset) - no negativos
- ✅ `start_date <= end_date`: Raise 422 si inválido
- ✅ `movement_type`: Enum validation automática por Pydantic

**Response:** `List[TransactionList]`
**Orden:** `transaction_date DESC, created_at DESC` (consistente)

**Service:** `get_transactions_by_user()` ✅ (ya existe, actualizar limit)

**Edge Cases:**
- `limit=5000` → Capear a 200 silenciosamente
- `offset=-10` → Convertir a 0 silenciosamente
- `start_date="2025-02-01" & end_date="2025-01-01"` → 422 error
- `movement_type="INVALID"` → 422 error (Pydantic)

---

##### 2. `GET /api/transactions/stats` - Estadísticas ampliadas ⭐ MEJORADO
**Descripción:** Dashboard stats + balance validation helper

**Response V1 (NUEVO):**
```json
{
  "counts": {
    "CARGO": 45,
    "ABONO": 12,
    "UNKNOWN": 3,
    "total": 60
  },
  "amounts": {
    "total_cargo": -15000.50,
    "total_abono": 12000.00,
    "net_balance": -3000.50
  }
}
```

**Service:**
- `count_transactions_by_type()` ✅ (ya existe)
- `sum_transactions_by_type()` ⚠️ (NUEVO - agregar)

**Razón del cambio:**
- Permite al frontend detectar discrepancias de balance
- Usuario ve de un vistazo: "Gasté $15k, recibí $12k, neto -$3k"
- Valida que clasificación es consistente

**Implementación Simple:**
```python
def sum_transactions_by_type(user_id: UUID, db: Session) -> Dict[str, Decimal]:
    """Sum amounts grouped by movement_type."""
    cargo = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.movement_type == "CARGO"
    ).scalar() or Decimal(0)

    abono = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.movement_type == "ABONO"
    ).scalar() or Decimal(0)

    return {
        "total_cargo": cargo,
        "total_abono": abono,
        "net_balance": cargo + abono
    }
```

---

##### 3. `GET /api/transactions/validate-balance` ⭐ NUEVO
**Descripción:** Validar que transacciones cuadran con statement summary

**Query Params:**
```python
statement_id: UUID  # Requerido
```

**Response:**
```json
{
  "statement_id": "123e4567-e89b-12d3-a456-426614174000",
  "statement_month": "2025-01",
  "summary": {
    "saldo_inicial": 8500.00,
    "saldo_final": 10500.00,
    "total_abonos": 5000.00,
    "total_cargos": -3000.00
  },
  "calculated": {
    "total_abonos": 4850.00,
    "total_cargos": -2850.00,
    "expected_final": 10500.00,
    "calculated_final": 10500.00
  },
  "validation": {
    "is_valid": true,
    "difference": 0.00,
    "warnings": []
  }
}
```

**Casos de error detectados:**
```json
{
  "validation": {
    "is_valid": false,
    "difference": -150.00,
    "warnings": [
      "Total abonos mismatch: expected 5000.00, calculated 4850.00 (diff: -150.00)",
      "This suggests misclassified transactions. Review ABONO transactions."
    ]
  }
}
```

**Service:** `validate_statement_balance()` ⚠️ (NUEVO)

**Lógica:**
1. Fetch statement (con ownership check)
2. Fetch summary del statement (almacenado al procesar)
3. Sum transactions del statement agrupadas por tipo
4. Comparar expected vs calculated
5. Generar warnings si hay discrepancia > $10

**Cuándo usar:**
- Frontend llama después de `POST /statements/{id}/process`
- Si `is_valid=false` → Mostrar warning banner
- Usuario puede entonces filtrar `needs_review=true` O revisar montos grandes

---

##### 4. `GET /api/transactions/{id}` - Detalle completo
**Descripción:** Modal/página de detalle de transacción

**Path Params:**
- `id: UUID`

**Response:** `TransactionResponse` (schema completo con 20+ campos)

**Security:**
- ✅ Ownership check: `user_id` del JWT
- ✅ Return 404 (no 403) si no existe/no pertenece

**Service:** `get_transaction_by_id()` ⚠️ (NUEVO - helper simple)

```python
def get_transaction_by_id(
    transaction_id: UUID,
    user_id: UUID,
    db: Session,
) -> Optional[Transaction]:
    """Get single transaction with ownership check."""
    return (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        )
        .first()
    )
```

---

##### 5. `PATCH /api/transactions/{id}` - Override manual
**Descripción:** Usuario corrige clasificación errónea

**Path Params:**
- `id: UUID`

**Body:** `TransactionUpdate`
```json
{
  "movement_type": "CARGO",    // opcional
  "category": "Supermercado",  // opcional
  "needs_review": false        // opcional
}
```

**Business Rules (AUTO-APLICADAS por service):**
1. Si `movement_type` cambia:
   - Recalcular `amount` (signo)
   - Si no envían `needs_review`:
     - `movement_type != UNKNOWN` → `needs_review = False`
     - `movement_type == UNKNOWN` → `needs_review = True`

2. Si solo cambian `category` o `needs_review`:
   - No recalcular amount

**Response:** `TransactionResponse`

**Service:** `update_transaction_classification()` ✅ (ya existe, ya tiene reglas)

**Security:**
- ✅ Ownership check en service
- ✅ Raises ValueError si no existe → convertir a 404 en route

---

#### Servicios a Agregar/Modificar

**NUEVOS (3 funciones simples):**
```python
# En transaction_service.py

def get_transaction_by_id(...) -> Optional[Transaction]:
    """Simple fetch con ownership."""
    # ~5 líneas

def sum_transactions_by_type(...) -> Dict[str, Decimal]:
    """Sum amounts por tipo."""
    # ~15 líneas (2 queries)

def validate_statement_balance(...) -> Dict[str, Any]:
    """Validar statement balance."""
    # ~30 líneas (fetch + compare)
```

**MODIFICAR:**
```python
# get_transactions_by_user()
# Cambiar limit max de 500 → 200
limit = min(max(limit, 1), 200)  # Era 500
```

---

#### Testing Checklist

**Happy Path (9 casos):**
- [ ] `GET /transactions/` sin filtros → todas las transactions
- [ ] `GET /transactions/?limit=10` → max 10 results
- [ ] `GET /transactions/?movement_type=CARGO` → solo CARGO
- [ ] `GET /transactions/?needs_review=true` → solo needs_review
- [ ] `GET /transactions/stats` → conteos + sumas correctas
- [ ] `GET /transactions/validate-balance?statement_id={id}` → is_valid=true
- [ ] `GET /transactions/{id}` → detalles completos
- [ ] `PATCH /transactions/{id}` movement_type=CARGO → needs_review=False auto
- [ ] `PATCH /transactions/{id}` category solo → no tocar amount

**Edge Cases (7 casos):**
- [ ] `GET /transactions/?limit=5000` → capea a 200
- [ ] `GET /transactions/?offset=-5` → usa 0
- [ ] `GET /transactions/?start_date=2025-02-01&end_date=2025-01-01` → 422
- [ ] `GET /transactions/{uuid_otro_user}` → 404 (no 403)
- [ ] `GET /transactions/validate-balance` con statement mal clasificado → is_valid=false + warnings
- [ ] `PATCH /transactions/{id}` con movement_type inválido → 422
- [ ] `PATCH /transactions/{id}` de otro user → 404

**Security (3 casos):**
- [ ] Todos los endpoints requieren JWT
- [ ] GET/PATCH by ID validan ownership
- [ ] No se filtra existencia (404 siempre, no 403)

---

#### Acceptance Criteria
- [x] 5 endpoints implementados (no 4)
- [x] Balance validation agregada (validate-balance endpoint)
- [x] Stats incluye sumas totales (amounts)
- [x] Limit capeado a 200 (no 500)
- [x] Validación start_date <= end_date en route
- [x] Business rules automáticas (needs_review)
- [x] Ownership checks en todos los ID-based endpoints
- [x] Todos los edge cases testeados
- [x] Swagger docs completas con ejemplos

---

### Milestone 1.2: Accounts Router 🟡 SIGUIENTE
**Tiempo:** 4 horas | **Complejidad:** Media | **Status:** Pending

#### Decisiones Clave V1
1. ✅ **Soft Delete Only** - No hard delete (is_active flag)
2. ✅ **Get-or-Create Pattern** - POST retorna existente si duplicado
3. ✅ **Unicidad:** `(user_id, bank_name, account_type)`
4. ✅ **display_name NO afecta unicidad** - Pueden haber 2 BBVAs con nombres distintos
5. ✅ **Normalización:** `bank_name.upper()` antes de guardar

---

#### Endpoints a Implementar

##### 1. `GET /api/accounts/` - Lista con filtros
**Query Params:**
```python
bank_name: Optional[str] = None
account_type: Optional[AccountType] = None  # DEBIT | CREDIT
is_active: bool = True  # Default solo activas
```

**Response:** `List[AccountResponse]`
**Orden:** `created_at DESC`

**Service:** `list_user_accounts()` ✅ (ya existe)

---

##### 2. `POST /api/accounts/` - Crear o retornar existente
**Body:** `AccountCreate`
```json
{
  "bank_name": "BBVA",
  "account_type": "DEBIT",
  "display_name": "BBVA Azul"  // opcional
}
```

**Business Rules:**
1. Normalizar `bank_name = bank_name.strip().upper()`
2. Check unicidad: `(user_id, bank_name, account_type)`
3. Si existe → retornar existente (200 OK)
4. Si no existe → crear (201 Created)

**Response:** `AccountResponse`

**Service:** `get_or_create_account()` ✅ (ya existe)

---

##### 3. `GET /api/accounts/{id}` - Detalle
**Path Params:** `id: UUID`

**Response:** `AccountResponse`

**Security:** Ownership check

**Service:** `get_account_by_id()` ✅ (ya existe)

---

##### 4. `PATCH /api/accounts/{id}` - Actualizar
**Body:** `AccountUpdate`
```json
{
  "display_name": "Mi Cuenta Principal",  // opcional
  "is_active": false                       // opcional
}
```

**Business Rules:**
- Solo actualiza campos enviados
- **NO** se puede cambiar `bank_name` ni `account_type` (inmutables)

**Response:** `AccountResponse`

**Service:** `update_account()` ✅ (ya existe)

---

##### 5. `DELETE /api/accounts/{id}` - Soft delete
**Response:** `204 No Content`

**Business Rules:**
- Soft delete: `is_active = False`
- **Idempotente:** Si ya inactiva → 204 OK igual
- Transactions/statements NO se borran (solo ocultar cuenta)

**Service:** `deactivate_account()` ✅ (ya existe)

---

#### Schemas a Crear

**Archivo:** `backend/app/schemas/account.py`

```python
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.models.account import AccountType  # Enum ya existe en model


class AccountResponse(BaseModel):
    """Account data for API responses."""
    id: UUID
    user_id: UUID
    bank_name: str
    account_type: AccountType
    display_name: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccountCreate(BaseModel):
    """Create new account."""
    bank_name: str
    account_type: AccountType
    display_name: Optional[str] = None


class AccountUpdate(BaseModel):
    """Update account fields."""
    display_name: Optional[str] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")
```

---

#### Testing Checklist

**Happy Path (8 casos):**
- [ ] `POST /accounts/` crea cuenta nueva → 201
- [ ] `POST /accounts/` duplicado → retorna existente 200
- [ ] `GET /accounts/` → lista todas
- [ ] `GET /accounts/?is_active=false` → solo inactivas
- [ ] `GET /accounts/{id}` → detalles
- [ ] `PATCH /accounts/{id}` display_name → actualizado
- [ ] `PATCH /accounts/{id}` is_active=False → desactivada
- [ ] `DELETE /accounts/{id}` → 204 + is_active=False

**Edge Cases (4 casos):**
- [ ] `POST` sin bank_name → 422
- [ ] `DELETE` ya inactiva → 204 OK (idempotente)
- [ ] `GET/PATCH/DELETE` de otro user → 404
- [ ] `POST` con bank_name="  bbva  " → normalizado a "BBVA"

**Security (2 casos):**
- [ ] JWT requerido en todos
- [ ] Ownership checks funcionan

---

### Milestone 1.3: PDF Cleanup + Logger 🟢 RÁPIDO
**Tiempo:** 30 min | **Complejidad:** Baja | **Status:** Pending

#### Cambios

**1. `main.py` - Configurar logging:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

**2. `statement_service.py` - Delete PDF + Logger:**
```python
import logging
import os

logger = logging.getLogger(__name__)

# En process_statement(), después de parsing_status="success":
if statement.parsing_status == "success":
    try:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            logger.info(f"PDF deleted: {pdf_path}")
    except Exception as e:
        logger.warning(f"Failed to delete PDF {pdf_path}: {e}")
        # NO fallar el statement
```

**3. Reemplazar todos los `print()` con `logger.info()`**

---

#### Testing
- [ ] Upload + process statement
- [ ] Verificar PDF borrado de `/tmp`
- [ ] Logs muestran "PDF deleted"
- [ ] Si falla delete → warning, no crash

---

## 🎯 PHASE 1.5: Quality (3 horas)

### Milestone 1.5a: Error Handling 🟡
**Tiempo:** 1 hora

**Crear:** `app/core/errors.py`
```python
from pydantic import BaseModel
from typing import Optional

class ErrorResponse(BaseModel):
    detail: str
    code: str
    field: Optional[str] = None

ERROR_CODES = {
    "INVALID_DATE_RANGE": "start_date must be <= end_date",
    "RESOURCE_NOT_FOUND": "Resource not found",
    # ...
}
```

**Uso en routers:**
```python
from app.core.errors import ErrorResponse

raise HTTPException(
    status_code=422,
    detail=ErrorResponse(
        detail="start_date must be before end_date",
        code="INVALID_DATE_RANGE"
    ).dict()
)
```

---

### Milestone 1.5b: Seed Script 🔥
**Tiempo:** 2 horas

**Crear:** `backend/scripts/seed_demo_data.py`

**Genera:**
- 1 user: `demo@saldo.com` / `Demo1234!`
- 2 accounts: BBVA Debit, Santander Credit
- 1 statement: BBVA, 2025-01, processed
- 50 transactions: 20 CARGO, 25 ABONO, 5 UNKNOWN

**Uso:**
```bash
python scripts/seed_demo_data.py
# Output:
# ✅ User: demo@saldo.com
# ✅ Accounts: 2
# ✅ Transactions: 50
```

---

## 🚫 FUERA DE SCOPE V1 (Pospuesto)

### V1.1 Features (Después de MVP)
- Multi-bank parser support
- Bank/type selector en upload
- Parser registry pattern
- Confidence scores
- Categorías custom
- Automated tests (pytest)
- Bulk operations
- Advanced filters en stats

### V1.1 Decisión: Bank Selector
**Cuándo:** Cuando agregues 2do parser (Santander o BBVA Credit)

**Implementación entonces:**
```python
# POST /api/statements/upload
Body: FormData {
    file: PDF,
    bank_name: str = Form(...),
    account_type: str = Form(...)
}

SUPPORTED_PARSERS = {
    ("BBVA", "DEBIT"): parse_bbva_debit,
    ("Santander", "DEBIT"): parse_santander_debit,
}
```

**Por ahora V1:** Hardcoded BBVA DEBIT, documentar limitación

---

## ✅ Definition of Done - V1

### Phase 1 DONE cuando:

**Transactions Router:**
- [x] 5 endpoints (no 4) implementados
- [x] Balance validation funcional
- [x] Stats con sumas totales
- [x] Limit capeado a 200
- [x] Validaciones robustas
- [x] Business rules automáticas
- [x] Ownership checks
- [x] Testing manual completo

**Accounts Router:**
- [x] 5 endpoints implementados
- [x] Schemas creados
- [x] Soft delete idempotente
- [x] Get-or-create pattern
- [x] Normalización automática
- [x] Testing manual completo

**PDF Cleanup:**
- [x] Logging configurado
- [x] PDFs auto-deleted
- [x] Fallos no rompen processing

### V1 MVP Ready cuando:
- [x] Usuario registra y autentica
- [x] Usuario sube y procesa BBVA debit statement
- [x] Usuario ve/filtra/edita transacciones
- [x] Usuario valida balance (detecta errores)
- [x] Usuario gestiona cuentas (CRUD)
- [x] Seed script funcional para demos
- [x] Testing manual exhaustivo (todos los casos)
- [x] Documentado en README
- [x] Deploy-ready

---

## ⏱️ Time Estimates V1

| Milestone | Horas | Prioridad |
|-----------|-------|-----------|
| 1.1 Transactions (5 endpoints) | 5 | 🔴 Critical |
| 1.2 Accounts (5 endpoints) | 4 | 🔴 Critical |
| 1.3 PDF Cleanup | 0.5 | 🟡 High |
| 1.5a Error Handling | 1 | 🟢 Medium |
| 1.5b Seed Script | 2 | 🟢 Medium |
| **Buffer (testing + fixes)** | **2** | - |
| **TOTAL V1** | **14.5 hrs** | **~2 semanas part-time** |

---

## 📋 Git Strategy V1

### Commits
```bash
# Milestone 1.1
git commit -m "feat: add transactions list endpoint with filters"
git commit -m "feat: add transactions stats with balance sums"
git commit -m "feat: add statement balance validation endpoint"
git commit -m "feat: add transaction detail and update endpoints"

# Milestone 1.2
git commit -m "feat: add account schemas"
git commit -m "feat: add accounts CRUD endpoints with soft delete"

# Milestone 1.3
git commit -m "feat: configure logging and auto-delete PDFs"

# Milestone 1.5
git commit -m "feat: add standardized error responses"
git commit -m "feat: add seed demo data script"
```

### PR
```
Title: feat: Transactions & Accounts CRUD + Balance Validation (V1)

Description:
## Summary
- ✅ Transactions Router (5 endpoints)
  - Balance validation
  - Stats with totals
  - Robust filters
- ✅ Accounts Router (5 endpoints)
  - Soft delete
  - Get-or-create pattern
- ✅ PDF cleanup + logging
- ✅ Error handling
- ✅ Seed script

## Testing
- Manual testing: All 28 test cases passed
- Balance validation: Detects misclassifications
- Security: Ownership checks validated

## V1 Scope Decisions
- ❌ Multi-bank support → V1.1
- ❌ Automated tests → V1.1
- ✅ BBVA Debit only (documented)

Closes #X
```

---

## 🚀 Next Steps

1. ✅ **Aprobar este roadmap V1**
2. ✅ **Empezar Milestone 1.1** - Transactions Router
3. ✅ Implementar endpoint por endpoint (slow but safe)
4. ✅ Testing manual exhaustivo
5. ✅ Milestone 1.2 - Accounts Router
6. ✅ Milestone 1.3 + 1.5
7. ✅ PR + Merge
8. 🚀 **Deploy V1 MVP**

---

**¿Aprobado? ¿Empezamos con el primer endpoint de Transactions?** 🎯
