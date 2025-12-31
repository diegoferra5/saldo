# 🗺️ Saldo Backend - Roadmap MVP Final

> **Versión:** 3.0 (Updated after Accounts Router implementation)
> **Branch actual:** `feature/transactions-account-endpoints`
> **Última actualización:** 2025-12-31
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
- ✅ Account Service (get-or-create pattern with tuple return)
- ✅ **Accounts Router (`/api/accounts/*`)** - 5 endpoints implementados:
  - ✅ GET / - List with filters (bank_name, account_type, is_active)
  - ✅ POST / - Create account (get-or-create with 201/200 status codes)
  - ✅ GET /{id} - Get account details
  - ✅ PATCH /{id} - Update display_name/is_active
  - ✅ DELETE /{id} - Soft delete (idempotent, returns 204)

---

## 🎯 Lo que FALTA para MVP Ready

### 🔴 Critical (Bloqueantes para MVP)

**1. PDF Cleanup + Logging (30 min)**
- [ ] Configurar logging en `main.py`
- [ ] Auto-delete PDFs después de `parsing_status=success`
- [ ] Logger profesional (reemplazar `print()` statements)
- **DoD:**
  - Logs configurados con nivel INFO
  - PDFs borrados automáticamente tras procesamiento exitoso
  - Fallos de delete logueados como warnings (no crash)

**2. Testing Manual Exhaustivo (2 horas)** ⭐ PRIORITARIO
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

### Accounts (`/api/accounts/`) ⭐ NEW
- [ ] POST / - Nueva cuenta → 201 Created
- [ ] POST / - Cuenta duplicada (bank+type) → 200 OK (retorna existente)
- [ ] POST / - Cuenta inactiva duplicada → reactivada + 200 OK
- [ ] GET / - Lista cuentas del user (default is_active=true)
- [ ] GET /?is_active=false → solo inactivas
- [ ] GET /?bank_name=BBVA → filtradas por banco
- [ ] GET /{id} - Cuenta válida → details
- [ ] GET /{id} - Cuenta de otro user → 404
- [ ] PATCH /{id} - display_name actualizado
- [ ] PATCH /{id} - is_active=false → desactivada
- [ ] PATCH /{id} - Solo display_name (is_active omitido) → OK
- [ ] DELETE /{id} - Cuenta soft deleted (is_active=False) → 204
- [ ] DELETE /{id} - DELETE idempotente (ya inactiva) → 204 OK

---

## 🚀 Sprint Final para MVP (3-4 días)

### ✅ Completado: Accounts Router (31 dic 2025)
- ✅ Creado `app/schemas/account.py` (AccountCreate, AccountUpdate, AccountResponse, AccountList)
- ✅ Creado `app/routes/account.py` con 5 endpoints
- ✅ Refactorizado `get_or_create_account()` → retorna `tuple[Account, bool]`
- ✅ DELETE endpoint implementado (soft delete idempotente)
- ✅ POST endpoint con 201/200 diferenciado
- ✅ Registrado router en `main.py`

### Día 1: Cleanup + Logging (2 horas)
- [ ] Implementar PDF auto-delete
- [ ] Configurar logging profesional
- [ ] Reemplazar print() statements
- [ ] Testing básico

### Día 2: Testing Exhaustivo (4 horas)
- [ ] Ejecutar checklist completo en Swagger (incluye accounts)
- [ ] Documentar edge cases encontrados
- [ ] Corregir bugs críticos
- [ ] Screenshots para docs

### Día 3: Documentation (3 horas)
- [ ] Actualizar README.md
- [ ] Documentar env vars
- [ ] Ejemplos de endpoints (incluir accounts)
- [ ] Setup instructions

### Día 4 (Opcional): Seed Script + Error Handling (3 horas)
- [ ] Implementar seed_demo_data.py (incluir accounts)
- [ ] Crear ErrorResponse schema
- [ ] Testing del seed script
- [ ] Documentar en README

### Final: Polish & Merge (2 horas)
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
- ✅ **Usuario gestiona cuentas (CRUD)** - Accounts router completo

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
| **Accounts Router** | **4** | **🔴 Critical** | **✅ Done** |
| PDF Cleanup + Logging | 0.5 | 🔴 Critical | Pending |
| Testing Manual Exhaustivo | 2 | 🔴 Critical | Pending |
| README Update | 1 | 🔴 Critical | Pending |
| Seed Script | 2 | 🟡 High | Optional |
| Error Handling | 1 | 🟡 High | Optional |
| **Buffer (fixes + polish)** | **1.5** | - | - |
| **TOTAL MVP** | **8 hrs restantes** | **~3-4 días part-time** | - |

---

## 🎯 Próximos Pasos Inmediatos

1. ✅ **Accounts Router completado** (31 dic 2025)
2. 🔴 **AHORA:** Git commit + push de accounts router (5 min)
3. 🔴 PDF Cleanup + Logging (30 min)
4. 🔴 Testing manual exhaustivo (2 horas - usar checklist completo)
5. 🔴 README update (1 hora)
6. 🟡 Seed script (opcional - 2 horas)
7. 🟡 Error handling (opcional - 1 hora)
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

### Accounts ⭐ NEW
- ✅ `GET /api/accounts/` - List with filters
- ✅ `POST /api/accounts/` - Create (get-or-create with 201/200)
- ✅ `GET /api/accounts/{id}` - Get account details
- ✅ `PATCH /api/accounts/{id}` - Update display_name/is_active
- ✅ `DELETE /api/accounts/{id}` - Soft delete (204)

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

## 📝 Changelog

### V3.0 (31 dic 2025) - Accounts Router Complete
**Completado:**
1. ✅ **Accounts Router implementado** (`/api/accounts/*`):
   - 5 endpoints CRUD completos
   - Soft delete idempotente (DELETE → 204)
   - POST con status codes semánticos (201 Created / 200 OK)
   - Ownership checks + filtros
   - Schema: AccountCreate, AccountUpdate, AccountResponse, AccountList

2. ✅ **Service layer refactorizado**:
   - `get_or_create_account()` → retorna `tuple[Account, bool]`
   - Elimina doble query en POST endpoint
   - `statement_service.py` actualizado para usar tuple

**Decisiones técnicas:**
- DELETE implementado (vs solo PATCH is_active) para mejor UX
- 201/200 diferenciados en POST (vs siempre 201)
- No hard delete (soft delete preserva datos históricos)
- `is_active` agregado a AccountUpdate schema

### V2.0 (30 dic 2025) - Stats & Reconciliation
1. ✅ `/transactions/stats` refactorizado (cash flow + data quality)
2. ✅ `/statements/{id}/health` agregado (reconciliación)
3. ✅ Statement `summary_data` JSONB field

### V1.0 - Foundation
- Statements, Transactions, Auth routers completos

---

**🚀 ¿Listo para empezar el sprint final de MVP?**
