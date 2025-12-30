# 🗺️ Saldo Backend V2 - Roadmap MVP Final

> **Versión:** 2.0 (Updated after cash flow stats + reconciliation implementation)
> **Branch actual:** `feature/transactions-account-endpoints`
> **Última actualización:** 2025-12-30
> **Filosofía:** Production-ready, audit-able, semantic consistency over quick hacks

---

## 📊 Estado Actual del Proyecto

### ✅ Completado (Foundation + Phase 1)

**Infrastructure & Core:**
- ✅ Database setup (SSL Supabase)
- ✅ SQLAlchemy Models (User, Account, Statement, Transaction)
- ✅ Auth Router (`/api/auth/*`) - Register, Login, /me
- ✅ JWT + bcrypt security

**Statements:**
- ✅ Statements Router (`/api/statements/*`) - Full CRUD + Processing
- ✅ PDF Parser (BBVA Débito con clasificación inteligente)
- ✅ Statement Service (upload, process, validaciones)
- ✅ **GET /statements/{id}/health** - Reconciliation endpoint (PDF vs DB)

**Transactions:**
- ✅ Transactions Router (`/api/transactions/*`) - 5 endpoints implementados:
  - ✅ GET / - List with filters (account_id, statement_id, dates, movement_type, needs_review)
  - ✅ **GET /stats** - Cash flow analysis (refactored v2)
    - ✅ Cash flow breakdown by account_type
    - ✅ Data quality flags (`is_complete`, `unknown_amount_abs_total`)
    - ✅ Filters: `statement_id`, `account_id`, `account_type`, `date_from`, `date_to`
  - ✅ GET /validate-balance - Balance validation against PDF summary
  - ✅ GET /{id} - Get transaction details
  - ✅ PATCH /{id} - Update classification (manual corrections)
- ✅ Transaction Service (deduplicación por hash + occurrence_index)

**Accounts:**
- ✅ Account Service (get-or-create pattern) - Service layer completo
- ❌ **Accounts Router PENDIENTE** - `/api/accounts/*` NO implementado aún

---

## 🎯 Lo que FALTA para MVP Ready

### 🔴 Critical (Bloqueantes para MVP)

**1. Accounts Router (4 horas)** ⭐ PRIORITARIO
- [ ] Crear `app/routes/accounts.py`
- [ ] Implementar 5 endpoints:
  - `GET /api/accounts/` - List with filters (bank_name, account_type, is_active)
  - `POST /api/accounts/` - Create account (get-or-create pattern)
  - `GET /api/accounts/{id}` - Get account details
  - `PATCH /api/accounts/{id}` - Update display_name/is_active
  - `DELETE /api/accounts/{id}` - Soft delete (is_active=False)
- [ ] Crear `app/schemas/account.py` (AccountResponse, AccountCreate, AccountUpdate)
- [ ] Registrar router en `main.py`
- **DoD:**
  - 5 endpoints funcionando en Swagger
  - Soft delete idempotente
  - Ownership checks implementados
  - Normalización de bank_name (uppercase)
  - Testing manual completado

**2. PDF Cleanup + Logging (30 min)**
- [ ] Configurar logging en `main.py`
- [ ] Auto-delete PDFs después de `parsing_status=success`
- [ ] Logger profesional (reemplazar `print()` statements)
- **DoD:**
  - Logs configurados con nivel INFO
  - PDFs borrados automáticamente tras procesamiento exitoso
  - Fallos de delete logueados como warnings (no crash)

**2. Testing Manual Exhaustivo (2 horas)**
- [ ] Swagger testing de TODOS los endpoints
- [ ] Edge cases documentados en checklist
- [ ] Security testing (ownership checks)
- **DoD:**
  - Checklist completo (ver sección Testing más abajo)
  - Screenshots de Swagger para documentación
  - Bugs críticos identificados y corregidos

**3. README.md Actualización (1 hora)**
- [ ] Cómo correr el proyecto (setup completo)
- [ ] Environment variables necesarias
- [ ] Endpoints principales documentados
- [ ] Link a Swagger docs
- **DoD:**
  - Developer nuevo puede correr proyecto en <15 min
  - Todas las env vars documentadas
  - Ejemplos de uso de cada endpoint

---

### 🟡 High Priority (Muy recomendado para MVP)

**4. Seed Script (2 horas)**
- [ ] Crear `scripts/seed_demo_data.py`
- [ ] Generar data realista (1 user, 2 accounts, 50 transactions)
- [ ] Script idempotente (puede correr múltiples veces)
- **DoD:**
  - Script corre sin errores
  - Crea usuario `demo@saldo.com` / `Demo1234!`
  - 50 transacciones distribuidas (CARGO/ABONO/UNKNOWN)
  - Documentado en README

**5. Error Handling Estandarizado (1 hora)**
- [ ] Crear `app/core/errors.py`
- [ ] ErrorResponse schema con códigos machine-readable
- [ ] Aplicar en endpoints críticos
- **DoD:**
  - Schema ErrorResponse creado
  - Códigos de error documentados
  - Frontend puede mostrar mensajes user-friendly

---

### 🟢 Nice to Have (Postergable a V1.1)

**6. Statement Summary Data Migration**
- [ ] Migración para statements antiguos sin `summary_data`
- [ ] Backfill con defaults o NULL
- **Nota:** Actualmente `/statements/{id}/health` maneja NULL correctamente con warnings

**7. Automated Tests**
- [ ] Unit tests (pytest)
- [ ] Integration tests
- **Nota:** MVP usa manual testing exhaustivo

---

## ✅ Testing Checklist (Manual - Swagger)

### Authentication (`/api/auth/`)
- [ ] POST /register - Usuario nuevo creado
- [ ] POST /register - Email duplicado → 400
- [ ] POST /login - Credenciales correctas → JWT token
- [ ] POST /login - Credenciales incorrectas → 401
- [ ] GET /me - Con token válido → user data
- [ ] GET /me - Sin token → 401

### Statements (`/api/statements/`)
- [ ] POST /upload - PDF válido → statement created
- [ ] POST /upload - No PDF → 400
- [ ] POST /upload - Statement duplicado → 400
- [ ] POST /{id}/process - Statement válido → transactions created
- [ ] POST /{id}/process - Statement de otro user → 404
- [ ] GET / - Lista statements del user
- [ ] GET /{id} - Statement válido → details
- [ ] GET /{id} - Statement de otro user → 404
- [ ] **GET /{id}/health - Statement con summary_data → is_reconciled true/false**
- [ ] **GET /{id}/health - Statement sin summary_data → warning NO_SUMMARY_DATA**
- [ ] **GET /{id}/health - Statement con UNKNOWN → warning INCOMPLETE_DUE_TO_UNKNOWN**
- [ ] DELETE /{id} - Statement borrado + transactions cascade

### Transactions (`/api/transactions/`)
- [ ] GET / - Sin filtros → todas las transactions
- [ ] GET /?limit=10 → max 10 results
- [ ] GET /?limit=5000 → capeado a 200
- [ ] GET /?movement_type=CARGO → solo CARGO
- [ ] GET /?account_id={uuid} → filtradas por cuenta
- [ ] GET /?statement_id={uuid} → filtradas por statement
- [ ] GET /?start_date=X&end_date=Y → rango válido
- [ ] GET /?start_date > end_date → 422 error
- [ ] **GET /stats - Sin filtros → global stats con is_complete, unknown_amount_abs_total**
- [ ] **GET /stats?statement_id={uuid} → stats del statement**
- [ ] **GET /stats?account_type=debit → stats solo DEBIT**
- [ ] **GET /stats?date_from=X&date_to=Y → stats del período**
- [ ] GET /validate-balance?statement_id={uuid} → validation result
- [ ] GET /{id} - Transaction válida → details
- [ ] GET /{id} - Transaction de otro user → 404
- [ ] PATCH /{id} - movement_type=CARGO → needs_review=False auto
- [ ] PATCH /{id} - movement_type=UNKNOWN → needs_review=True auto
- [ ] PATCH /{id} - Transaction de otro user → 404

### Accounts (`/api/accounts/`)
- [ ] POST / - Nueva cuenta → created
- [ ] POST / - Cuenta duplicada (bank+type) → retorna existente
- [ ] GET / - Lista cuentas del user
- [ ] GET /?is_active=false → solo inactivas
- [ ] GET /{id} - Cuenta válida → details
- [ ] GET /{id} - Cuenta de otro user → 404
- [ ] PATCH /{id} - display_name actualizado
- [ ] PATCH /{id} - is_active=false → desactivada
- [ ] DELETE /{id} - Cuenta soft deleted (is_active=False)
- [ ] DELETE /{id} - DELETE idempotente (ya inactiva) → 204 OK

---

## 🚀 Sprint Final para MVP (6-7 días)

### Día 1-2: Accounts Router (4 horas) 🔴 BLOQUEANTE
- [ ] Crear `app/schemas/account.py`
- [ ] Crear `app/routes/accounts.py` con 5 endpoints
- [ ] Registrar router en `main.py`
- [ ] Testing básico en Swagger

### Día 3: Cleanup + Logging (2 horas)
- [ ] Implementar PDF auto-delete
- [ ] Configurar logging profesional
- [ ] Reemplazar print() statements
- [ ] Testing básico

### Día 4: Testing Exhaustivo (4 horas)
- [ ] Ejecutar checklist completo en Swagger (incluye accounts)
- [ ] Documentar edge cases encontrados
- [ ] Corregir bugs críticos
- [ ] Screenshots para docs

### Día 5: Documentation (3 horas)
- [ ] Actualizar README.md
- [ ] Documentar env vars
- [ ] Ejemplos de endpoints (incluir accounts)
- [ ] Setup instructions

### Día 6: Seed Script + Error Handling (3 horas)
- [ ] Implementar seed_demo_data.py (incluir accounts)
- [ ] Crear ErrorResponse schema
- [ ] Testing del seed script
- [ ] Documentar en README

### Día 7: Final Polish (2 horas)
- [ ] Code review final
- [ ] Smoke tests end-to-end
- [ ] Git commit + push
- [ ] PR preparado para merge

---

## 📋 Definition of Done - MVP

### Backend MVP Ready cuando:

**Core Functionality:**
- ✅ Usuario registra y autentica
- ✅ Usuario sube y procesa BBVA debit statement
- ✅ Usuario ve/filtra/edita transacciones
- ✅ Usuario valida balance (detecta errores de clasificación)
- ✅ Usuario reconcilia statement (PDF vs DB)
- ✅ Usuario obtiene cash flow stats con data quality flags
- ❌ **Usuario gestiona cuentas (CRUD)** - PENDIENTE (accounts router)

**Quality:**
- [ ] Logging profesional configurado
- [ ] PDFs auto-deleted tras procesamiento
- [ ] Testing manual exhaustivo completado (checklist 100%)
- [ ] README actualizado con setup completo
- [ ] Seed script disponible para demos
- [ ] Error handling estandarizado

**Security:**
- ✅ Todos los endpoints filtran por user_id
- ✅ JWT validation en todos los endpoints protegidos
- ✅ Ownership checks en endpoints by ID
- ✅ No filtración de existencia (404, no 403)

**Documentation:**
- [ ] README.md completo
- [ ] Environment variables documentadas
- [ ] Swagger docs actualizadas
- [ ] Business decisions documentadas

---

## ⏱️ Time Estimates V2

| Task | Horas | Prioridad | Status |
|------|-------|-----------|--------|
| **Accounts Router** | **4** | **🔴 Critical** | **Pending** |
| PDF Cleanup + Logging | 0.5 | 🔴 Critical | Pending |
| Testing Manual Exhaustivo | 2 | 🔴 Critical | Pending |
| README Update | 1 | 🔴 Critical | Pending |
| Seed Script | 2 | 🟡 High | Pending |
| Error Handling | 1 | 🟡 High | Pending |
| **Buffer (fixes + polish)** | **1.5** | - | - |
| **TOTAL MVP** | **12 hrs** | **~1.5 semanas part-time** | - |

---

## 🎯 Próximos Pasos Inmediatos

1. 🔴 **AHORA:** Implementar Accounts Router (4 horas) - BLOQUEANTE
2. ✅ PDF Cleanup + Logging (30 min)
3. ✅ Testing básico de accounts + cleanup (30 min)
4. ✅ Testing manual exhaustivo (2 horas - usar checklist completo)
5. ✅ README update (1 hora)
6. ✅ Seed script (2 horas)
7. ✅ Error handling (1 hora)
8. ✅ Final testing + polish
9. ✅ Commit + push + PR
10. 🚀 **Merge a main + Deploy MVP**

---

## 📚 Endpoints Implementados (Summary)

### Auth
- `POST /api/auth/register` - Create user
- `POST /api/auth/login` - Get JWT
- `GET /api/auth/me` - Get current user

### Statements
- `POST /api/statements/upload` - Upload PDF
- `POST /api/statements/{id}/process` - Parse PDF
- `GET /api/statements/` - List statements
- `GET /api/statements/{id}` - Get statement
- `GET /api/statements/{id}/health` - **Reconciliation check** ⭐ NEW
- `DELETE /api/statements/{id}` - Delete statement

### Transactions
- `GET /api/transactions/` - List with filters
- `GET /api/transactions/stats` - **Cash flow stats v2** ⭐ REFACTORED
- `GET /api/transactions/validate-balance` - Balance validation
- `GET /api/transactions/{id}` - Get transaction
- `PATCH /api/transactions/{id}` - Update classification

### Accounts
- ❌ **PENDIENTE** - `/api/accounts/*` router NO implementado aún
- ⚠️ Service layer existe (`account_service.py`) pero falta router

---

## 🚫 Out of Scope para MVP (V1.1+)

- Multi-bank parser support (Santander, Banorte)
- Automated tests (pytest)
- Bank/type selector en upload
- Confidence scores
- Custom categories per user
- Bulk operations
- Advanced filters en stats
- ML personalization

---

## 📝 Notas de Cambios V1 → V2

**Qué cambió desde ROADMAP_V1:**
1. ✅ `/transactions/stats` refactorizado completamente:
   - Ahora retorna cash flow breakdown por account_type
   - Incluye `is_complete` y `unknown_amount_abs_total`
   - Acepta filtros: `statement_id`, `account_id`, `account_type`, `date_from`, `date_to`
   - Schemas corregidos (counts son `int`, no `Optional[int]`)
   - Query consolidada con CASE WHEN (performance)

2. ✅ `/statements/{id}/health` endpoint agregado:
   - Reconciliación DB vs PDF summary
   - Warnings: `NO_SUMMARY_DATA`, `INCOMPLETE_DUE_TO_UNKNOWN`
   - Threshold fijo MVP: 10.00

3. ✅ Statement `summary_data` JSONB field agregado
   - Guarda output del parser (deposits_amount, charges_amount, etc.)
   - Usado por `/health` endpoint para reconciliación

4. ✅ Business decisions documentadas (ver `docs/business-decisions.md`)

**Qué falta (ajustado desde V1):**
- ❌ **Accounts Router** - Service layer existe pero falta implementar router (4 horas)
- PDF cleanup (estaba marcado como pendiente, sigue pendiente)
- Testing manual exhaustivo (con nuevo checklist actualizado incluyendo accounts)
- Seed script (prioridad aumentada - muy útil para demos)

---

**🚀 ¿Listo para empezar el sprint final de MVP?**
