# 🗺️ Saldo Backend MVP - Roadmap Completo

> **Branch actual:** `feature/transactions-account-endpoints`
> **Última actualización:** 2025-12-29
> **Tiempo estimado total:** 17 horas (Opción B - MVP Robusto)

---

## 📊 Estado del Proyecto

### ✅ Completado
- Infrastructure & Database Setup (SSL para Supabase)
- SQLAlchemy Models (User, Account, Statement, Transaction)
- Auth Router (`/api/auth/*`) - Register, Login, /me
- Statements Router (`/api/statements/*`) - Full CRUD + Processing
- PDF Parser (BBVA Débito con clasificación inteligente)
- Transaction Service (con deduplicación por hash)
- Statement Service (upload, process, validaciones)

### 🔴 En Progreso
- **Phase 1:** CRUD Endpoints (Transactions + Accounts)

### 🟡 Siguiente
- Transactions Router (Milestone 1.1)

---

## 🎯 PHASE 1: CRUD Endpoints (14 horas)

### Milestone 1.1: Transactions Router 🔴 PRIORITARIO
**Tiempo:** 4 horas | **Complejidad:** Media | **Status:** Pending

#### Objetivos
Exponer todas las transacciones del usuario vía API REST con validaciones robustas y reglas de negocio automáticas.

#### Endpoints a Implementar

##### 1. `GET /api/transactions/`
**Descripción:** Lista paginada de transacciones con filtros

**Query Params:**
- `account_id` (UUID, opcional): Filtrar por cuenta específica
- `start_date` (date, opcional): Fecha inicio (YYYY-MM-DD)
  - **Validación:** Debe ser <= end_date si ambos están presentes
- `end_date` (date, opcional): Fecha fin (YYYY-MM-DD)
  - **Validación:** Debe ser >= start_date si ambos están presentes
- `movement_type` (enum, opcional): CARGO | ABONO | UNKNOWN
- `needs_review` (boolean, opcional): Filtrar por revisión pendiente
- `limit` (int, opcional): Default 50, **Max 200**
  - **Validación:** Debe estar entre 1 y 200
- `offset` (int, opcional): Default 0
  - **Validación:** Debe ser >= 0

**Response:** `List[TransactionList]`
**Orden:** `transaction_date DESC`
**Service:** `get_transactions_by_user()`

**Edge Cases:**
- `limit > 200` → Capear a 200
- `offset < 0` → 422 Validation Error
- `start_date > end_date` → 422 con mensaje "start_date must be <= end_date"
- `movement_type` inválido → 422 Validation Error

---

##### 2. `GET /api/transactions/stats`
**Descripción:** Estadísticas de transacciones por tipo de movimiento

**Response:**
```json
{
  "CARGO": 123,
  "ABONO": 45,
  "UNKNOWN": 2
}
```

**Service:** `count_transactions_by_type()`

**Notas:**
- MVP: Stats globales del usuario (sin filtros)
- V1.1: Considerar agregar filtros opcionales (account_id, date_range)

---

##### 3. `GET /api/transactions/{id}`
**Descripción:** Obtener detalle de transacción específica

**Path Params:**
- `id` (UUID, requerido)

**Response:** `TransactionResponse`

**Security:**
- ✅ Ownership check: Filtrar por `user_id` del JWT
- ✅ Error handling: Retornar **404** (NO 403) si no existe o no pertenece al usuario
  - Razón: No filtrar existencia de recursos a otros usuarios

**Edge Cases:**
- ID no encontrado → 404 Not Found
- ID de otro usuario → 404 Not Found (no 403)
- UUID inválido → 422 Validation Error

---

##### 4. `PATCH /api/transactions/{id}`
**Descripción:** Actualizar clasificación de transacción (manual override)

**Path Params:**
- `id` (UUID, requerido)

**Body:** `TransactionUpdate`
```json
{
  "movement_type": "CARGO",  // opcional
  "needs_review": false,      // opcional
  "category": "Supermercado"  // opcional (V1.1)
}
```

**Response:** `TransactionResponse`

**Business Rules (AUTOMÁTICAS):**
1. Si `movement_type != UNKNOWN` → auto-setear `needs_review = False`
2. Si `movement_type == UNKNOWN` → auto-setear `needs_review = True`
3. Solo actualizar campos presentes (partial update real)

**Security:**
- ✅ Ownership check: Verificar que la transacción pertenece al usuario actual
- ✅ Error: 404 si no existe o no es del usuario

**Service:** `update_transaction_classification()`

**Edge Cases:**
- `movement_type` inválido → 422 Validation Error
- Transacción de otro usuario → 404 Not Found
- Body vacío → 200 OK (no-op, no cambios)

---

#### Testing Checklist

**Happy Path:**
- [ ] `GET /transactions/` sin filtros retorna todas las transacciones del usuario
- [ ] `GET /transactions/?limit=10` retorna máximo 10 resultados
- [ ] `GET /transactions/?movement_type=CARGO` filtra correctamente
- [ ] `GET /transactions/?account_id={uuid}` filtra por cuenta
- [ ] `GET /transactions/?start_date=2025-01-01&end_date=2025-01-31` filtra por rango
- [ ] `GET /transactions/stats` retorna conteos correctos
- [ ] `GET /transactions/{id}` con ID válido retorna detalles
- [ ] `PATCH /transactions/{id}` actualiza `movement_type` correctamente
- [ ] `PATCH /transactions/{id}` con `movement_type=CARGO` auto-setea `needs_review=False`

**Edge Cases:**
- [ ] `GET /transactions/?limit=5000` capea a 200
- [ ] `GET /transactions/?start_date=2025-02-01&end_date=2025-01-01` retorna 422
- [ ] `GET /transactions/{id}` de otro usuario retorna 404 (no 403)
- [ ] `PATCH /transactions/{id}` con `movement_type=INVALID` retorna 422

**Security:**
- [ ] Todos los endpoints requieren JWT válido
- [ ] `GET/PATCH` by ID verifican ownership (user_id match)
- [ ] Retornan 404 (no 403) para acceso no autorizado

---

#### Archivos

**Crear:**
- `backend/app/routes/transactions.py`

**Modificar:**
- `backend/app/main.py` (agregar router)

**Dependencias (ya implementadas):**
- `app/services/transaction_service.py` ✅
- `app/schemas/transactions.py` ✅
- `app/core/security.py` (JWT) ✅

---

#### Acceptance Criteria
- [x] 4 endpoints implementados y documentados en Swagger
- [x] Filtros funcionando (account_id, dates, type, needs_review)
- [x] Paginación con validaciones (limit/offset)
- [x] Stats retorna conteos precisos
- [x] PATCH actualiza solo campos enviados (partial update)
- [x] Auth valida ownership en todos los endpoints por ID
- [x] Business rules aplicadas automáticamente (needs_review logic)
- [x] Todos los edge cases testeados manualmente en Swagger

---

### Milestone 1.2: Accounts Router 🟡 SIGUIENTE
**Tiempo:** 4 horas | **Complejidad:** Media | **Status:** Pending

#### Objetivos
CRUD completo de cuentas bancarias con soft delete, validaciones de unicidad y normalización.

#### Endpoints a Implementar

##### 1. `GET /api/accounts/`
**Descripción:** Lista de cuentas del usuario con filtros opcionales

**Query Params:**
- `bank_name` (string, opcional): Ej. "BBVA", "Santander"
- `account_type` (enum, opcional): DEBIT | CREDIT
- `is_active` (boolean, opcional): Default `true` (solo activas)

**Response:** `List[AccountResponse]`
**Orden:** `created_at DESC`
**Service:** `list_user_accounts()`

---

##### 2. `POST /api/accounts/`
**Descripción:** Crear cuenta bancaria (o retornar existente si ya existe)

**Body:** `AccountCreate`
```json
{
  "bank_name": "BBVA",           // requerido
  "account_type": "DEBIT",        // requerido (DEBIT | CREDIT)
  "display_name": "BBVA Azul"     // opcional
}
```

**Response:** `AccountResponse`

**Business Rules:**
1. **Unicidad:** `(user_id, bank_name, account_type)`
   - `display_name` NO afecta unicidad (puedes tener 2 BBVAs con nombres distintos si son DEBIT y CREDIT)
2. **Normalización:** `bank_name` se convierte a uppercase antes de guardar
3. **Get-or-Create Pattern:** Si ya existe cuenta con mismo `(user_id, bank_name, account_type)` → retornar existente

**Service:** `get_or_create_account()`

**Edge Cases:**
- Cuenta duplicada (mismo bank+type) → Retorna cuenta existente (no error)
- Falta `bank_name` → 422 Validation Error
- `account_type` inválido → 422 Validation Error

---

##### 3. `GET /api/accounts/{id}`
**Descripción:** Obtener detalle de cuenta específica

**Path Params:**
- `id` (UUID, requerido)

**Response:** `AccountResponse`

**Security:**
- ✅ Ownership check: Filtrar por `user_id` del JWT
- ✅ Error: 404 si no existe o no pertenece al usuario

**Service:** `get_account_by_id()`

---

##### 4. `PATCH /api/accounts/{id}`
**Descripción:** Actualizar cuenta (solo `display_name` y `is_active`)

**Path Params:**
- `id` (UUID, requerido)

**Body:** `AccountUpdate`
```json
{
  "display_name": "Mi Tarjeta Principal",  // opcional
  "is_active": false                        // opcional
}
```

**Response:** `AccountResponse`

**Business Rules:**
1. Solo actualiza campos presentes en request (partial update)
2. **NO** se puede cambiar `bank_name` ni `account_type` (inmutables)
3. Desactivar cuenta (`is_active=False`) NO elimina statements/transactions

**Security:**
- ✅ Ownership check: Verificar que cuenta pertenece al usuario actual

**Service:** `update_account()`

---

##### 5. `DELETE /api/accounts/{id}`
**Descripción:** Soft delete de cuenta (setea `is_active=False`)

**Path Params:**
- `id` (UUID, requerido)

**Response:** `204 No Content`

**Business Rules:**
1. **Soft delete:** Setea `is_active=False` (NO hard delete)
2. **Idempotente:** Si ya está inactiva, retornar 204 OK igual
3. Statements y transactions permanecen visibles (solo cuenta se oculta en UI)
4. Puede reactivarse con `PATCH is_active=True`

**Security:**
- ✅ Ownership check: Verificar que cuenta pertenece al usuario actual

**Service:** `deactivate_account()`

**Edge Cases:**
- DELETE cuenta ya inactiva → 204 OK (idempotente)
- DELETE cuenta con transactions → 204 OK (soft delete preserva data)

---

#### Schemas a Crear

**Archivo:** `backend/app/schemas/account.py`

```python
# AccountResponse - Para GET requests
class AccountResponse(BaseModel):
    id: UUID
    user_id: UUID
    bank_name: str
    account_type: AccountType  # Enum: DEBIT, CREDIT
    display_name: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

# AccountCreate - Para POST
class AccountCreate(BaseModel):
    bank_name: str  # requerido
    account_type: AccountType  # requerido
    display_name: Optional[str] = None

# AccountUpdate - Para PATCH
class AccountUpdate(BaseModel):
    display_name: Optional[str] = None
    is_active: Optional[bool] = None
```

---

#### Testing Checklist

**Happy Path:**
- [ ] `POST /accounts/` crea nueva cuenta
- [ ] `POST /accounts/` con duplicado (bank+type) retorna cuenta existente
- [ ] `GET /accounts/` retorna todas las cuentas del usuario
- [ ] `GET /accounts/?is_active=true` filtra solo activas
- [ ] `GET /accounts/?bank_name=BBVA` filtra por banco
- [ ] `GET /accounts/{id}` retorna detalles de cuenta
- [ ] `PATCH /accounts/{id}` actualiza `display_name`
- [ ] `DELETE /accounts/{id}` setea `is_active=False`

**Edge Cases:**
- [ ] `POST` sin `bank_name` → 422 Validation Error
- [ ] `POST` cuenta duplicada → retorna existente (no crea nueva)
- [ ] `DELETE` cuenta ya inactiva → 204 OK (idempotente)
- [ ] `GET/PATCH/DELETE` cuenta de otro usuario → 404 Not Found

**Security:**
- [ ] Todos los endpoints requieren JWT auth
- [ ] Ownership checks en GET/PATCH/DELETE by ID
- [ ] No se pueden acceder cuentas de otros usuarios

---

#### Archivos

**Crear:**
- `backend/app/schemas/account.py`
- `backend/app/routes/accounts.py`

**Modificar:**
- `backend/app/main.py` (agregar router)

**Dependencias (ya implementadas):**
- `app/services/account_service.py` ✅

---

#### Acceptance Criteria
- [x] 5 endpoints implementados
- [x] Schemas creados en `app/schemas/account.py`
- [x] POST implementa get-or-create pattern (no duplicados)
- [x] DELETE es soft delete (is_active flag)
- [x] DELETE es idempotente
- [x] Ownership checks implementados
- [x] Todos los edge cases testeados en Swagger

---

### Milestone 1.3: PDF Cleanup + Logger 🟢 RÁPIDO
**Tiempo:** 30 minutos | **Complejidad:** Baja | **Status:** Pending

#### Objetivos
Implementar limpieza automática de PDFs después de procesamiento exitoso con logging profesional.

#### Cambios a Implementar

**1. Configurar Logging en `main.py`:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

**2. En `statement_service.py`:**
```python
import logging
import os

logger = logging.getLogger(__name__)

# En process_statement(), después de parsing_status = "success":
if statement.parsing_status == "success":
    try:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            logger.info(f"PDF deleted successfully: {pdf_path}")
    except Exception as e:
        logger.warning(f"Failed to delete PDF {pdf_path}: {e}")
        # NO marcar statement como failed, solo warning
```

**3. Reemplazar todos los `print()` con `logger.info()`/`logger.warning()`**

---

#### Business Rules
1. Solo borrar PDFs después de `parsing_status = "success"`
2. Si delete falla, log warning pero **NO** fallar el statement
3. Esto previene que `/tmp` se llene indefinidamente

#### Notas
- **V1 (MVP):** Delete después de success (simple)
- **V2:** Considerar migrar a Supabase Storage para almacenamiento permanente
- **Limitación:** Si necesitas re-procesamiento, esto lo rompe (necesitarías mantener PDFs)

---

#### Testing Checklist
- [ ] Subir y procesar un statement
- [ ] Verificar que PDF fue eliminado de `/tmp/statements/{user_id}/`
- [ ] Verificar que registro en DB sigue existiendo
- [ ] Verificar logs muestran "PDF deleted successfully"
- [ ] Simular fallo de delete (borrar archivo manualmente) → debe logguear warning, no crashear

---

#### Archivos

**Modificar:**
- `backend/app/main.py` (configurar logging)
- `backend/app/services/statement_service.py` (add logger, delete PDF)

---

#### Acceptance Criteria
- [x] Logging configurado en `main.py`
- [x] Todos los `print()` reemplazados con logger
- [x] PDFs borrados después de procesamiento exitoso
- [x] Fallos de delete logueados como warnings (no errors)
- [x] Procesamiento de statement no falla si delete falla

---

## 🎯 PHASE 1.5: Quality & Developer Experience (3 horas)

### Milestone 1.5a: Error Handling Estandarizado 🟡
**Tiempo:** 1 hora | **Complejidad:** Baja | **Status:** Pending

#### Objetivos
Crear respuestas de error consistentes en toda la API con códigos machine-readable.

#### Archivo a Crear

**`backend/app/core/errors.py`:**
```python
from pydantic import BaseModel
from typing import Optional

class ErrorResponse(BaseModel):
    detail: str  # Mensaje legible para humanos
    code: str    # Código machine-readable para frontend
    field: Optional[str] = None  # Campo que causó el error

# Error codes estándar
ERROR_CODES = {
    "INVALID_DATE_RANGE": "start_date must be before or equal to end_date",
    "LIMIT_EXCEEDED": "limit must be between 1 and 200",
    "DUPLICATE_STATEMENT": "Statement already exists for this month",
    "RESOURCE_NOT_FOUND": "Resource not found",
    "UNAUTHORIZED_ACCESS": "You don't have access to this resource"
}
```

#### Uso en Routers
```python
from app.core.errors import ErrorResponse

raise HTTPException(
    status_code=422,
    detail=ErrorResponse(
        detail="start_date must be before end_date",
        code="INVALID_DATE_RANGE",
        field="start_date"
    ).dict()
)
```

#### Benefits
- ✅ Mejor UX: Frontend puede mostrar mensajes user-friendly
- ✅ Debugging más fácil: Códigos machine-readable
- ✅ Consistencia: Todos los endpoints retornan mismo formato
- ✅ i18n ready: Error codes pueden traducirse en frontend

---

### Milestone 1.5b: Seed Data Script 🔥 MUY ÚTIL
**Tiempo:** 2 horas | **Complejidad:** Media | **Status:** Pending

#### ¿Por qué es importante?
- ⚡ Acelera onboarding de developers (5 min vs 1 hora manual)
- 🎥 Facilita demos y presentaciones
- 🧪 Testing más rápido (no crear data manualmente)
- 🐛 Permite reproducir bugs con datos consistentes

#### Archivo a Crear

**`backend/scripts/seed_demo_data.py`:**

**Data a generar:**
- **1 usuario:** `demo@saldo.com` / `Demo1234!`
- **2 cuentas:**
  - BBVA Débito - "BBVA Azul - Principal"
  - Santander Crédito - "Santander Free"
- **1 statement:** BBVA Debit, 2025-01, `parsing_status=success`
- **50 transacciones:**
  - 20 CARGO (gastos)
  - 25 ABONO (ingresos)
  - 5 UNKNOWN (revisar)
  - Categorías realistas: Supermercado (OXXO, SORIANA), Transporte (UBER), Restaurantes (STARBUCKS), etc.

#### Dependencia
```bash
pip install Faker
```

#### Uso
```bash
cd backend
python scripts/seed_demo_data.py

# Output esperado:
# ✅ User created: demo@saldo.com
# ✅ Accounts created: 2
# ✅ Statement created: 1
# ✅ Transactions created: 50
#
# 🔑 Login credentials:
#    Email: demo@saldo.com
#    Password: Demo1234!
```

#### Acceptance Criteria
- [x] Script corre sin errores
- [x] Crea 1 usuario con credenciales conocidas
- [x] Crea 2 cuentas (distintos bancos/tipos)
- [x] Crea 50 transacciones realistas con Faker
- [x] Transacciones distribuidas en CARGO/ABONO/UNKNOWN
- [x] Script es idempotente (puede correr múltiples veces)
- [x] Documentado en README

---

## 📋 Git Workflow

### Commits Sugeridos

```bash
# Milestone 1.1
git add app/routes/transactions.py app/main.py
git commit -m "feat: add transactions endpoints (GET, PATCH, stats)"

# Milestone 1.2
git add app/schemas/account.py app/routes/accounts.py app/main.py
git commit -m "feat: add accounts CRUD endpoints with soft delete"

# Milestone 1.3
git add app/main.py app/services/statement_service.py
git commit -m "feat: add logging and auto-delete PDFs after processing"

# Milestone 1.5a
git add app/core/errors.py app/routes/*.py
git commit -m "feat: add standardized error responses"

# Milestone 1.5b
git add scripts/seed_demo_data.py requirements.txt README.md
git commit -m "feat: add seed demo data script for development"
```

### Pull Request

**Título:**
```
feat: Add Transactions & Accounts CRUD endpoints (Phase 1 + 1.5)
```

**Descripción:**
```markdown
## Summary
- ✅ Transactions Router (4 endpoints con validaciones robustas)
- ✅ Accounts Router (5 endpoints con soft delete)
- ✅ PDF cleanup con logging profesional
- ✅ Strict validations & business rules automáticas
- ✅ Seed data script para demos y testing

## Testing
- Manual testing completo en Swagger
- Todos los edge cases verificados
- Security (ownership checks) validado

## Next Steps
- Merge a main
- Deploy a staging
- Begin Phase 2 (automated tests)
```

---

## ✅ Definition of Done

### Phase 1 DONE cuando:
- [x] **Transactions Router:**
  - 4 endpoints implementados
  - Validaciones: limit (max 200), offset >= 0, start_date <= end_date
  - ORDER BY transaction_date DESC
  - Business rules automáticas (needs_review)
  - Ownership checks en GET/PATCH by ID
  - Error responses: 404 (no 403)
  - Partial update real
  - Edge cases testeados

- [x] **Accounts Router:**
  - 5 endpoints implementados
  - Schemas creados
  - Unicidad: (user_id, bank_name, account_type)
  - Normalización: bank_name uppercase
  - POST usa get-or-create
  - DELETE soft delete idempotente
  - Ownership checks
  - Edge cases testeados

- [x] **PDF Cleanup:**
  - Logging configurado
  - PDFs borrados después de success
  - Fallos logueados como warnings
  - Statement no falla si delete falla

### Phase 1.5 DONE cuando:
- [x] ErrorResponse schema creado
- [x] Seed script genera data realista
- [x] Script es idempotente
- [x] Documentado en README

### MVP Ready cuando:
- [x] Usuario puede registrarse y autenticarse
- [x] Usuario puede subir y procesar statements BBVA débito
- [x] Usuario puede ver/filtrar/editar transacciones vía API
- [x] Usuario puede gestionar cuentas bancarias (CRUD)
- [x] Todos los tests manuales passing
- [x] Seed script disponible para demos
- [x] API deployed y públicamente accesible

---

## ⏱️ Time Estimates

| Phase | Milestone | Hours | Calendar (Part-Time) |
|-------|-----------|-------|---------------------|
| 1 | 1.1 Transactions Router | 4 | 1 día |
| 1 | 1.2 Accounts Router | 4 | 1 día |
| 1 | 1.3 PDF Cleanup | 0.5 | 1 hora |
| **1.5** | **1.5a Error Handling** | **1** | **2 horas** |
| **1.5** | **1.5b Seed Script** | **2** | **4 horas** |
| **Buffer** | **Testing + Fixes** | **1.5** | **3 horas** |
| **TOTAL** | **Phase 1 + 1.5** | **17** | **~2 semanas** |

---

## 🎯 Próximos Pasos Inmediatos

1. ✅ **AHORA:** Empezar Milestone 1.1 (Transactions Router)
2. ✅ Testing manual en Swagger
3. ✅ Milestone 1.2 (Accounts Router)
4. ✅ Testing manual en Swagger
5. ✅ Milestone 1.3 (PDF Cleanup)
6. ✅ Milestone 1.5b (Seed Script) - MUY ÚTIL
7. ✅ Testing completo end-to-end
8. ✅ Commit + Push + PR
9. ✅ Merge a main
10. 🚀 Deploy a staging/production

---

## 📚 Recursos

**Swagger Docs:** http://localhost:8000/docs
**Branch:** `feature/transactions-account-endpoints`
**Main Branch:** `main`

**Comandos útiles:**
```bash
# Levantar servidor
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Ver logs
tail -f logs/app.log  # después de configurar logging

# Seed demo data
python scripts/seed_demo_data.py

# Git status
git status
git log --oneline -10
```

---

**🚀 ¿Listo para empezar con Milestone 1.1?**
