# Business Decisions - Saldo MVP

> **Purpose:** Audit trail of critical product, business logic, and architectural decisions
> **Last Updated:** 2025-12-30
> **Status:** MVP Phase

---

## Core Philosophy

**"Simplicidad correcta > overengineering"**

For MVP, we prioritize:
1. **Semantic consistency** - Schema contracts match implementation reality
2. **Audit-ability** - Code should be easy to trace and debug
3. **Honest UX** - Better to show "unknown" than misclassify
4. **Performance consciousness** - Consolidate queries, avoid over-fetching

---

## 1. PDF Parser = Ingestion Only, DB = Source of Truth

### Decisión
El PDF parser es **solo una herramienta de ingestion inicial**. Una vez que los datos están en la DB, la base de datos se convierte en la **única fuente de verdad** para toda la UI, stats, y dashboards.

### Motivo
- **Correcciones manuales:** Los usuarios pueden corregir errores de clasificación vía `PATCH /transactions/{id}`
- **Auditabilidad:** El estado actual de las transacciones refleja decisiones del usuario, no solo del parser
- **Evolución:** El parser mejora con el tiempo, pero los datos históricos permanecen

### Implicación
- Stats endpoints (`/transactions/stats`, `/statements/{id}/health`) SIEMPRE consultan la DB actual
- NO recalculamos a partir del PDF
- NO usamos `summary_data` del PDF para stats de transacciones (solo para reconciliación)

### Ejemplo
```python
# ❌ INCORRECTO
pdf_cash_flow = summary_data["deposits_amount"] - summary_data["charges_amount"]
return {"cash_flow": pdf_cash_flow}

# ✅ CORRECTO
db_cash_flow = db.query(func.sum(Transaction.amount)).scalar()
return {"cash_flow": db_cash_flow}
```

---

## 2. Manual Corrections via PATCH /transactions/{id}

### Decisión
Los usuarios pueden corregir clasificaciones erróneas del parser mediante `PATCH /api/transactions/{id}`, pero con restricciones:

**Permitido:**
- Cambiar `movement_type` de CARGO ↔ ABONO
- Cambiar `movement_type` a CARGO o ABONO si era UNKNOWN
- Cambiar `category` (futuro)
- Marcar/desmarcar `needs_review`

**NO permitido:**
- Usuario NO puede setear una transacción como UNKNOWN manualmente
- Usuario NO puede cambiar `amount_abs` (dato del PDF, inmutable)

### Motivo
- **UNKNOWN es diagnóstico, no manual:** UNKNOWN significa "el parser no pudo clasificar", no es una opción para el usuario
- **amount_abs inmutable:** Es el dato crudo del PDF, cambiar esto rompe la reconciliación con `summary_data`

### Implicación
- Business rules automáticas:
  - `movement_type != UNKNOWN` → auto-setea `needs_review = False`
  - `movement_type == UNKNOWN` → imposible (endpoint rechaza)
- El campo `amount` (signed) se recalcula automáticamente al cambiar `movement_type`

### Ejemplo
```python
# ✅ Usuario corrige CARGO → ABONO
PATCH /transactions/{id}
{
  "movement_type": "ABONO"
}
# Backend recalcula: amount = +amount_abs, needs_review = False

# ❌ Usuario intenta setear UNKNOWN
PATCH /transactions/{id}
{
  "movement_type": "UNKNOWN"
}
# → 422 Validation Error (solo parser puede crear UNKNOWN)
```

---

## 3. Statement summary_data - Parser Output Stored

### Decisión
Al procesar un statement PDF, guardamos el **output completo del parser** en el campo JSONB `statements.summary_data`:

```json
{
  "starting_balance": 8500.00,
  "final_balance": 10500.00,
  "deposits_amount": 5000.00,
  "charges_amount": 3000.00,
  "n_deposits": 17,
  "n_charges": 17,
  "period_days": 30,
  "period_start": "2025-12-01",
  "period_end": "2025-12-31"
}
```

### Motivo
- **Reconciliación:** Permite comparar PDF original vs DB actual (`/statements/{id}/health`)
- **Debugging:** Podemos verificar si el parser extrajo correctamente los totales
- **Audit trail:** Sabemos qué leyó el parser en el momento del upload

### Implicación
- Statements antiguos (pre-migration) pueden tener `summary_data = NULL`
- `/statements/{id}/health` maneja NULL con warning `NO_SUMMARY_DATA`
- `summary_data` NO se usa para stats de transacciones (solo para validación)

### Ejemplo
```python
# Statement health check
if statement.summary_data is None:
    return {
        "has_summary_data": False,
        "is_reconciled": None,
        "warnings": ["NO_SUMMARY_DATA"]
    }

pdf_cash_flow = summary_data["deposits_amount"] - summary_data["charges_amount"]
db_cash_flow = sum(transactions.amount)  # From DB, not PDF
difference = db_cash_flow - pdf_cash_flow
```

---

## 4. Separación de Métricas: Cash Flow vs Net Worth

### Decisión
**`/transactions/stats` representa SOLO cash flow (flujos del período), NO net worth.**

**Cash flow:**
- `cash_flow = total_abono + total_cargo` (suma de amounts signed)
- **NO incluye** `starting_balance` ni `final_balance`
- Es un análisis de **flujo** del conjunto de transacciones filtradas

**Net worth (futuro endpoint `/accounts/summary`):**
- Net worth = suma de saldos actuales de todas las cuentas
- Requiere `starting_balance` + cash_flow acumulado
- Es un **snapshot** del patrimonio actual

### Motivo
- **Claridad semántica:** Cash flow ≠ net worth
- **Evitar confusión:** Mezclar ambos en un endpoint genera expectativas incorrectas
- **Simplicidad MVP:** Cash flow es más fácil de implementar (solo sumar transacciones)

### Implicación
- `/transactions/stats` NO devuelve balances
- Futuro endpoint `/accounts/summary` manejará net worth
- Frontend debe mostrar claramente que stats = análisis de flujo del período

### Ejemplo
```json
// ✅ CORRECTO - /transactions/stats
{
  "global_stats": {
    "total_abono": "47856.22",    // Income
    "total_cargo": "-56862.50",   // Expenses
    "cash_flow": "-9006.28"       // Net flow (negative = deficit)
  }
}

// ❌ INCORRECTO - mezclar con balances
{
  "starting_balance": "8500.00",  // ❌ NO en stats
  "cash_flow": "-9006.28",
  "ending_balance": "-506.28"     // ❌ NO en stats
}
```

---

## 5. Data Quality Flags en Stats

### Decisión
`/transactions/stats` incluye dos indicadores de calidad del dato:

**A) `is_complete`**
- `is_complete = (count_unknown == 0)`
- Indica si el cash_flow es completo o está incompleto por transacciones sin clasificar

**B) `unknown_amount_abs_total`**
- Suma de `amount_abs` de transacciones UNKNOWN
- Es un monto positivo **informativo** (cuánto dinero está sin clasificar)
- **NO afecta** `cash_flow`, `total_abono`, ni `total_cargo`

### Motivo
- **Honestidad con el usuario:** Si hay UNKNOWN, el usuario debe saberlo
- **Accionable:** `unknown_amount_abs_total` cuantifica el problema ("tienes $4,210 sin clasificar")
- **Separación de concerns:** UNKNOWN se cuenta pero NO contamina los totales

### Implicación
- UNKNOWN transactions:
  - Se cuentan en `count_unknown` ✅
  - NO suman a `total_abono` ni `total_cargo` ❌
  - Su `amount_abs` suma en `unknown_amount_abs_total` ✅ (informativo)
- Frontend puede mostrar banner: "⚠️ 8 transacciones sin clasificar ($4,210)"

### Ejemplo
```json
{
  "global_stats": {
    "total_abono": "1994.99",           // Solo ABONO conocidos
    "total_cargo": "-15233.73",         // Solo CARGO conocidos
    "cash_flow": "-13238.74",           // total_abono + total_cargo
    "count_unknown": 8,                 // Transacciones sin clasificar
    "is_complete": false,               // ⚠️ Hay UNKNOWN
    "unknown_amount_abs_total": "4210.00"  // Cuánto está sin clasificar
  }
}
```

---

## 6. Reconciliación por Statement: GET /statements/{id}/health

### Decisión
Endpoint dedicado para validar que las transacciones en DB **cuadran** con el resumen del PDF original.

**Fórmula de reconciliación:**
```python
pdf_cash_flow = deposits_amount - charges_amount  # From summary_data
db_cash_flow = sum(transactions.amount WHERE amount IS NOT NULL)  # From DB
difference = db_cash_flow - pdf_cash_flow
is_reconciled = abs(difference) < threshold  # threshold = 10.00 MVP
```

**Warnings:**
- `NO_SUMMARY_DATA`: Statement no tiene `summary_data` (pre-migration)
- `INCOMPLETE_DUE_TO_UNKNOWN`: Hay transacciones UNKNOWN en el statement

### Motivo
- **Detecta errores de clasificación:** Si difference > 10, algo fue mal clasificado
- **Audit trail:** Podemos verificar integridad del parsing + clasificación
- **Transparencia:** Usuario ve si el statement "cuadra" o no

### Implicación
- `/health` es **diagnóstico**, no correctivo
- Si `is_reconciled = False`, usuario debe revisar transacciones manualmente
- Threshold fijo MVP = 10.00 (puede ajustarse en V1.1)

### Ejemplo
```json
// ✅ Statement reconciled
{
  "statement_id": "uuid",
  "has_summary_data": true,
  "db_cash_flow": "-9006.28",
  "pdf_cash_flow": "-9006.28",
  "difference": "0.00",
  "is_reconciled": true,
  "warnings": []
}

// ⚠️ Statement NOT reconciled
{
  "statement_id": "uuid",
  "has_summary_data": true,
  "db_cash_flow": "-9006.28",
  "pdf_cash_flow": "-9150.00",
  "difference": "143.72",          // Discrepancy!
  "is_reconciled": false,
  "warnings": ["INCOMPLETE_DUE_TO_UNKNOWN"]
}
```

---

## 7. FastAPI Route Ordering

### Decisión
**Rutas específicas SIEMPRE antes de rutas parametrizadas.**

### Motivo
FastAPI evalúa rutas en orden de definición. Si `/{id}` está antes de `/health`, FastAPI intenta parsear "health" como UUID y falla.

### Implicación
En todos los routers, definir rutas en este orden:
1. Rutas fijas (ej. `/stats`, `/health`, `/validate-balance`)
2. Rutas parametrizadas (ej. `/{id}`, `/{statement_id}`)

### Ejemplo
```python
# ✅ CORRECTO
@router.get("/stats")  # Ruta fija primero
def get_stats(): ...

@router.get("/{id}")   # Ruta parametrizada después
def get_by_id(id: UUID): ...

# ❌ INCORRECTO
@router.get("/{id}")   # FastAPI parseará "stats" como UUID
def get_by_id(id: UUID): ...

@router.get("/stats")  # Nunca se alcanza
def get_stats(): ...
```

---

## 8. Schema Semantic Consistency

### Decisión
**Los schemas Pydantic deben reflejar la REALIDAD del service, no ser "optimistas".**

### Motivo
- **Evita bugs latentes:** Si un campo es `Optional[int]` pero siempre retorna `int`, el schema miente
- **Auditabilidad:** El schema es el contrato - debe ser preciso
- **Prevents false assumptions:** Código que asume Optional puede romper si nunca es None

### Implicación
- Si un campo SIEMPRE tiene valor → usar tipo directo (`int`), no `Optional[int]`
- Si un campo PUEDE ser None → usar `Optional[...]` explícitamente
- Revisar schemas cuando refactorizamos services

### Ejemplo
```python
# ❌ INCORRECTO - miente sobre la realidad
class CashFlowStats(BaseModel):
    count_abono: Optional[int] = None  # Service SIEMPRE retorna int

# Service
count_abono = db.query(...).count()  # ALWAYS returns int, NEVER None

# ✅ CORRECTO - refleja realidad
class CashFlowStats(BaseModel):
    count_abono: int  # Service siempre retorna int
```

---

## 9. Query Consolidation with CASE WHEN

### Decisión
**Preferir UNA query consolidada con CASE WHEN sobre múltiples queries separadas.**

### Motivo
- **Performance:** Menos round-trips a DB
- **Mantenibilidad:** Menos código, menos duplicación de filtros
- **Auditabilidad:** Más fácil de seguir lógica en un solo lugar

### Implicación
- Para agregaciones complejas, usar SQLAlchemy `case()` para consolidar
- Evitar 3+ queries cuando se pueden hacer en 1
- Trade-off: Queries más complejas, pero más eficientes

### Ejemplo
```python
# ❌ ANTES (3 queries)
sums_query = db.query(...).filter(...).group_by(...)
counts_query = db.query(...).filter(...).group_by(...)  # Duplica filtros!
unknown_query = db.query(...).filter(...).group_by(...) # Duplica filtros!

# ✅ DESPUÉS (1 query consolidada)
from sqlalchemy import case

aggregated_query = db.query(
    Account.account_type,
    Transaction.movement_type,
    func.count(Transaction.id),
    func.sum(case((Transaction.amount.isnot(None), Transaction.amount), else_=0)),
    func.sum(case((Transaction.amount_abs.isnot(None), Transaction.amount_abs), else_=0))
).filter(...).group_by(...)  # Filtros aplicados UNA vez
```

---

## 10. No Optimistic Initialization

### Decisión
**NO inicializar estructuras de datos con valores "optimistas" que luego se corrigen.**

### Motivo
- **Seguridad:** Alguien puede leer el dict antes de la corrección
- **Auditabilidad:** El estado intermedio es incorrecto
- **Fintech:** En aplicaciones financieras, NO puede haber estados inconsistentes

### Implicación
- Calcular valores derivados UNA vez, al final, con datos reales
- No inicializar con `is_complete: True` si luego se recalcula
- Estructuras solo existen cuando están completas y correctas

### Ejemplo
```python
# ❌ INCORRECTO - valores optimistas
by_account_type[acc_type] = {
    "is_complete": True,  # ← MENTIRA hasta que se recalcula
    "unknown_amount_abs_total": Decimal("0")  # ← MENTIRA
}
# ... código después recalcula is_complete

# ✅ CORRECTO - calcular una vez con datos reales
# Primera pasada: recolectar datos
raw_data = collect_data()

# Segunda pasada: construir estructura final (UNA vez, correctamente)
for acc_type, data in raw_data.items():
    count_unknown = data["UNKNOWN"]["count"]
    by_account_type[acc_type] = {
        "is_complete": count_unknown == 0,  # ← Calculado con datos reales
        "unknown_amount_abs_total": data["UNKNOWN"]["amount_abs_sum"]
    }
```

---

## 11. UNKNOWN Transactions Handling

### Decisión
UNKNOWN transactions se manejan de forma especial:

**Reglas:**
- `amount = None` (NULL en DB)
- `amount_abs` = valor absoluto del PDF (siempre positivo)
- Se CUENTAN en stats (`count_unknown`)
- NO suman a `total_abono` ni `total_cargo`
- SU `amount_abs` suma en `unknown_amount_abs_total` (informativo)

### Motivo
- **Honestidad:** No inventamos signos cuando no sabemos
- **Auditabilidad:** Separamos "conocido" de "desconocido"
- **Accionable:** Usuario puede ver cuánto está sin clasificar

### Implicación
- Queries de suma SIEMPRE filtran `amount.isnot(None)`
- Queries de conteo NO filtran (incluyen UNKNOWN)
- UNKNOWN no afecta cash_flow, pero sí `is_complete`

### Ejemplo
```python
# ✅ CORRECTO
# Suma de cash flow (excluye UNKNOWN)
db_cash_flow = (
    db.query(func.sum(Transaction.amount))
    .filter(Transaction.amount.isnot(None))  # ← Excluye UNKNOWN
    .scalar()
) or Decimal("0")

# Conteo (incluye UNKNOWN)
count_unknown = (
    db.query(func.count(Transaction.id))
    .filter(Transaction.movement_type == "UNKNOWN")
    .scalar()
)

# Suma informativa de amount_abs (solo UNKNOWN)
unknown_amount_abs_total = (
    db.query(func.sum(Transaction.amount_abs))
    .filter(Transaction.movement_type == "UNKNOWN")
    .scalar()
) or Decimal("0")
```

---

## 12. Multi-Tenant Security by Default

### Decisión
**TODAS las queries SIEMPRE filtran por `user_id` del JWT.**

### Motivo
- **Seguridad:** Prevent data leakage entre usuarios
- **Compliance:** GDPR, privacidad de datos financieros
- **Zero trust:** Nunca asumir que el ID del request es válido

### Implicación
- Obtener `user_id` de `get_current_user()` dependency (JWT)
- NUNCA usar `user_id` del request body/query params
- Retornar 404 (NO 403) cuando recurso no existe/no pertenece al user

### Ejemplo
```python
# ✅ CORRECTO
@router.get("/transactions/{id}")
def get_transaction(
    id: UUID,
    current_user: User = Depends(get_current_user),  # ← From JWT
    db: Session = Depends(get_db)
):
    tx = db.query(Transaction).filter(
        Transaction.id == id,
        Transaction.user_id == current_user.id  # ← ALWAYS filter
    ).first()

    if not tx:
        raise HTTPException(404)  # ← 404, not 403

# ❌ INCORRECTO
@router.get("/transactions/{id}")
def get_transaction(id: UUID, user_id: UUID, db: Session = Depends(get_db)):
    # ❌ user_id from request - can be forged!
    tx = db.query(Transaction).filter(Transaction.id == id).first()
    # ❌ No user_id filter - data leak!
```

---

## Summary of Key Principles

1. **DB is source of truth** - Stats from DB, not PDF
2. **Manual corrections allowed** - But no setting UNKNOWN manually
3. **summary_data stored** - For reconciliation, not for stats
4. **Cash flow ≠ Net worth** - Separate endpoints, separate metrics
5. **Data quality flags** - Be honest about incomplete data
6. **Reconciliation endpoint** - Validate PDF vs DB integrity
7. **Route ordering matters** - Specific before parameterized
8. **Schemas reflect reality** - No lying about Optional fields
9. **Consolidate queries** - Use CASE WHEN for performance
10. **No optimistic init** - Calculate once, correctly
11. **UNKNOWN = special** - Count but don't sum
12. **Multi-tenant by default** - Always filter by user_id

---

**Mantenido por:** @diego
**Próxima revisión:** Post-MVP (after V1.0 launch)
