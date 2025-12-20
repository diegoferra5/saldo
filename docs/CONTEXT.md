# Saldo - Estado del Proyecto
**Fecha:** 20 de Diciembre, 2025  
**Fase:** Week 1, Day 4 - FASE 2 Completada ✅  
**Siguiente:** FASE 3 - Pydantic Schemas

---

## 🎯 Resumen Ejecutivo

**Saldo** es una aplicación de finanzas personales para el mercado mexicano que permite a usuarios:
- Subir estados de cuenta bancarios en PDF (BBVA, Banorte, Santander)
- Parsear y categorizar transacciones automáticamente
- Hacer seguimiento de presupuestos
- Recibir asesoría financiera vía AI (GPT-4)

**MVP Approach:** Manual upload de PDFs (sin APIs bancarias por limitaciones de Belvo en México)

---

## 🏆 Logros - HackMTY 2025

- ✅ **Ganador:** HackMTY 2025 (hackathon más grande de Latinoamérica)
- ✅ **Validación:** Jueces vieron valor en el producto
- ✅ **Objetivo:** Beta pública con 50+ usuarios para Febrero 2026

---

## 📊 Arquitectura Actual

### **Tech Stack**

**Backend:**
- FastAPI (Python 3.11.14)
- PostgreSQL (Supabase)
- SQLAlchemy ORM
- Autenticación JWT (bcrypt)

**Parsing:**
- pdfplumber (extracción de PDFs)
- Parser custom BBVA (85% accuracy en statements modernos)

**Frontend (Planeado - Week 2):**
- Next.js + React
- Tailwind CSS

**Deployment (Planeado - Week 4):**
- Railway (backend)
- Vercel (frontend)
- Supabase (database)

---

## 🗄️ Base de Datos - Schema Completo

### **Tablas (4 principales)**
```
users
├── id (UUID, PK)
├── email (VARCHAR, UNIQUE)
├── hashed_password (VARCHAR)
├── full_name (VARCHAR, nullable)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

accounts
├── id (UUID, PK)
├── user_id (UUID, FK → users.id ON DELETE CASCADE)
├── bank_name (VARCHAR(50))
├── account_type (VARCHAR(10)) -- 'DEBIT' | 'CREDIT'
├── display_name (VARCHAR(100), nullable)
├── is_active (BOOLEAN, default true)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

statements
├── id (UUID, PK)
├── user_id (UUID, FK → users.id ON DELETE CASCADE)
├── account_id (UUID, FK → accounts.id ON DELETE SET NULL, nullable)
├── bank_name (VARCHAR(50))
├── account_type (VARCHAR(20))
├── statement_month (DATE)
├── period_start (DATE, nullable)
├── period_end (DATE, nullable)
├── file_name (VARCHAR(255))
├── file_size_kb (INTEGER, nullable)
├── parsing_status (VARCHAR(20)) -- 'pending' | 'processing' | 'success' | 'failed'
├── error_message (TEXT, nullable)
├── file_hash (VARCHAR(64), nullable)
├── ip_address (VARCHAR(45), nullable)
├── created_at (TIMESTAMP)
├── updated_at (TIMESTAMP)
└── processed_at (TIMESTAMP, nullable)

transactions
├── id (UUID, PK)
├── user_id (UUID, FK → users.id ON DELETE CASCADE)
├── account_id (UUID, FK → accounts.id ON DELETE CASCADE)
├── statement_id (UUID, FK → statements.id ON DELETE CASCADE)
├── date (VARCHAR(10)) -- "11/NOV" (formato original PDF)
├── date_liquidacion (VARCHAR(10), nullable)
├── transaction_date (DATE) -- 2025-11-11 (parseado)
├── description (TEXT)
├── amount_abs (NUMERIC(12,2)) -- Siempre positivo
├── amount (NUMERIC(12,2), nullable) -- Con signo: neg=gasto, pos=ingreso, null=unknown
├── movement_type (VARCHAR(10)) -- 'CARGO' | 'ABONO' | 'UNKNOWN'
├── needs_review (BOOLEAN, default true)
├── category (VARCHAR(50), nullable)
├── saldo_operacion (NUMERIC(12,2), nullable)
├── saldo_liquidacion (NUMERIC(12,2), nullable)
├── transaction_hash (VARCHAR(64)) -- SHA256 para deduplicación
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
```

### **Constraints Importantes**

**accounts:**
- CHECK: `account_type IN ('DEBIT', 'CREDIT')`
- INDEX: `user_id`, `(user_id, is_active)`

**statements:**
- CHECK: `parsing_status IN ('pending', 'processing', 'success', 'failed')`
- CHECK: `account_type IN ('debit', 'credit', 'investment')`
- CHECK: `(period_start IS NULL) OR (period_end IS NULL) OR (period_start <= period_end)`
- UNIQUE (parcial): `(account_id, statement_month) WHERE account_id IS NOT NULL`

**transactions:**
- CHECK: `movement_type IN ('CARGO', 'ABONO', 'UNKNOWN')`
- CHECK: `amount_abs >= 0`
- UNIQUE: `transaction_hash` con constraint parcial
- INDEX: `user_id`, `account_id`, `statement_id`, `transaction_date`
- INDEX GIN: `description` (búsqueda texto)

---

## 🏗️ Modelos ORM - SQLAlchemy (COMPLETOS ✅)

### **Filosofía de Diseño**

**Principios aplicados:**
1. **DB como Source of Truth:** Supabase maneja constraints e índices
2. **ORM como Mapper:** Modelos solo mapean a schema existente
3. **Validaciones en Pydantic:** Reglas de negocio en schemas, no en ORM
4. **Soft Delete:** Accounts nunca se borran, solo `is_active = False`
5. **Passive Deletes:** DB maneja cascades vía FK constraints

### **User Model** (`app/models/user.py`)
```python
- Columnas: id, email, hashed_password, full_name, created_at, updated_at
- Relationships: accounts, statements, transactions
- Approach: Data mapping (sin __table_args__)
- Cascade: passive_deletes en todos los relationships
```

### **Account Model** (`app/models/account.py`)
```python
- Columnas: id, user_id, bank_name, account_type, display_name, is_active, timestamps
- Relationships: user, statements, transactions
- Approach: Data mapping (sin __table_args__)
- Soft Delete: NUNCA session.delete(), siempre is_active = False
- Note: updated_at usa onupdate=func.now() (migrar a trigger DB en producción)
```

### **Statement Model** (`app/models/statement.py`)
```python
- Columnas: 16 campos incluyendo IDs, file info, processing status, dates
- Relationships: user, account, transactions
- Approach: Data mapping (sin __table_args__)
- Parsing Status: pending → processing → success/failed
```

### **Transaction Model** (`app/models/transaction.py`)
```python
- Columnas: 18 campos incluyendo 3 formatos de fecha, montos, clasificación
- Relationships: user, account, statement
- Approach: Data mapping (sin __table_args__)
- Classification: CARGO (gasto) | ABONO (ingreso) | UNKNOWN (revisar)
- Deduplicación: transaction_hash (SHA256)
```

---

## 🔧 Componentes Completados

### **✅ FASE 1 - Database Setup (Completada)**
- [x] Schema en Supabase
- [x] Tablas: users, accounts, statements, transactions
- [x] Foreign Keys con políticas CASCADE/SET NULL
- [x] Constraints e índices
- [x] Row Level Security policies

### **✅ FASE 2 - Models & ORM (Completada)**
- [x] SQLAlchemy Base setup
- [x] User model
- [x] Account model  
- [x] Statement model
- [x] Transaction model
- [x] Relationships bidireccionales
- [x] Arquitectura consistente (DB source of truth)

### **⏳ FASE 3 - Pydantic Schemas (Siguiente)**
- [ ] User schemas (registro, login, response)
- [ ] Account schemas (create, update, response)
- [ ] Statement schemas (upload, response, list)
- [ ] Transaction schemas (response, update, list)

---

## 🧠 Decisiones de Diseño Importantes

### **1. Manual Upload vs API Automática**

**Decisión:** Manual upload de PDFs  
**Razón:** Belvo (agregador bancario) solo soporta Brasil, no México  
**Beneficio:** Más control, validación de concepto, path a API después

### **2. Soft Delete en Accounts**

**Decisión:** Nunca borrar accounts, solo `is_active = False`  
**Razón:** 
- Preserva histórico financiero
- Auditoría y compliance (CONDUSEF)
- Usuario puede reactivar si fue error

### **3. DB Source of Truth (No ORM Constraints)**

**Decisión:** No duplicar constraints/índices en ORM  
**Razón:**
- Supabase ya tiene todo configurado
- Evita inconsistencias ORM ↔ DB
- Validaciones irán en Pydantic (mejor lugar)
- Más simple y mantenible

### **4. Passive Deletes en Todos los Relationships**

**Decisión:** `passive_deletes=True` en todos los relationships  
**Razón:**
- DB tiene ON DELETE CASCADE/SET NULL bien configurados
- Dejamos que PostgreSQL maneje eficientemente
- Evita N+1 queries de SQLAlchemy
- Consistencia: DB ejecuta, ORM no interviene

### **5. Three-Way Foreign Keys en Transactions**

**Decisión:** Transaction tiene FK a user, account Y statement  
**Razón:**
- Denormalización intencional para queries rápidas
- Permite: "Dame todas las transacciones del usuario" sin JOIN a statement
- Facilita analytics y reportes
- Trade-off: Redundancia aceptable por performance

### **6. Movement Type: CARGO/ABONO/UNKNOWN**

**Decisión:** Clasificación conservadora con categoría UNKNOWN  
**Razón:**
- Mejor marcar UNKNOWN que clasificar incorrectamente
- Usuario revisa manualmente transacciones ambiguas
- Parser logra 85% accuracy en statements modernos
- Path a ML personalizado después

---

## 📁 Estructura del Proyecto
```
saldo/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app (pendiente)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py            # ✅ SQLAlchemy setup
│   │   ├── config.py              # ✅ Settings (Supabase URL, JWT secret)
│   │   └── security.py            # ✅ Password hashing, JWT
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                # ✅ User ORM model
│   │   ├── account.py             # ✅ Account ORM model
│   │   ├── statement.py           # ✅ Statement ORM model
│   │   └── transaction.py         # ✅ Transaction ORM model
│   ├── schemas/                   # ⏳ Pydantic (siguiente)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── account.py
│   │   ├── statement.py
│   │   └── transaction.py
│   ├── api/                       # ⏳ FastAPI routes (Week 1-2)
│   │   ├── __init__.py
│   │   ├── deps.py                # Dependencies (get_db, get_current_user)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py            # Login, register
│   │       ├── accounts.py        # CRUD accounts
│   │       ├── statements.py      # Upload, parse
│   │       └── transactions.py    # List, update, categorize
│   ├── services/                  # ⏳ Business logic (Week 2-3)
│   │   ├── __init__.py
│   │   ├── parser_service.py     # PDF parsing integration
│   │   └── categorization.py     # Auto-categorization
│   └── parsers/
│       ├── __init__.py
│       └── bbva_parser.py         # ✅ BBVA PDF parser (85% accuracy)
├── tests/                         # ⏳ Testing (Week 4)
├── .env                           # Environment variables
├── requirements.txt               # Dependencies
└── README.md
```

---

## 🔄 Parser BBVA - Status

**Archivo:** `parsers/bbva_parser.py`  
**Accuracy:** 85% en statements modernos (Nov 2025)

**Funciones principales:**
1. `extract_statement_summary()` - Extrae totales del bloque "Comportamiento"
2. `extract_transaction_lines()` - Obtiene líneas de transacciones del PDF
3. `parse_transaction_line()` - Parsea cada línea en estructura
4. `determine_transaction_type()` - Clasifica CARGO/ABONO/UNKNOWN

**Output por transacción:**
```python
{
    'date': '11/NOV',
    'date_liquidacion': '11/NOV',
    'description': 'STARBUCKS COFFEE',
    'amount_abs': 150.00,
    'movement_type': 'CARGO',
    'amount': -150.00,
    'needs_review': False,
    'saldo_operacion': 10948.46,
    'saldo_liquidacion': 10948.46
}
```

**Features futuras:**
- [ ] Extracción de beneficiario (líneas de detalle)
- [ ] Parser Santander y Banorte
- [ ] ML personalizado por usuario
- [ ] Detección de transacciones recurrentes

---

## 🎯 Roadmap - 8 Semanas

### **Week 1 (Actual)** ✅ ~75% Completa
- [x] Database setup
- [x] Models ORM
- [ ] **→ Pydantic schemas** (siguiente)
- [ ] Auth endpoints (register/login)
- [ ] Statement upload endpoint básico

### **Week 2** (Dec 15-21)
- [ ] Frontend MVP (Next.js)
- [ ] Upload UI (drag & drop)
- [ ] Transaction list view
- [ ] Budget creation

### **Week 3** (Dec 22-28)
- [ ] Categorización automática
- [ ] Budget tracking dashboard
- [ ] OpenAI GPT-4 integration
- [ ] CSV parser genérico

### **Week 4** (Dec 29-Jan 4)
- [ ] Testing & bug fixes
- [ ] Security review
- [ ] Performance optimization
- [ ] Deploy a staging

### **Weeks 5-8**
- Beta testing → Public beta → Production launch
- Target: 50+ usuarios activos para Feb 9, 2026

---

## 📊 Métricas de Éxito (Feb 2026)

**Producto:**
- 50+ usuarios activos
- 70%+ retention (usuarios regresan)
- 4.0+ rating
- <3 seg page load

**Técnico:**
- 0 data breaches
- 99.5% uptime
- Response times <500ms p95

**Usuario:**
- 80%+ recomendarían a un amigo
- "Me ahorró dinero" mencionado 5+ veces

---

## 🔑 Próximo Paso Inmediato

**FASE 3: Pydantic Schemas**

**Objetivo:** Definir validación de requests/responses para API

**Schemas necesarios:**
1. **User:** UserCreate, UserLogin, UserResponse, Token
2. **Account:** AccountCreate, AccountUpdate, AccountResponse
3. **Statement:** StatementUpload, StatementResponse, StatementList
4. **Transaction:** TransactionResponse, TransactionUpdate, TransactionList

**Estimado:** 3-4 horas

---

## 💡 Aprendizajes Clave

1. **Web-first > Mobile-first para MVP:** Iteración más rápida
2. **Constraints no se duplican:** DB tiene verdad, ORM mapea
3. **Soft delete en fintech:** NUNCA borrar data financiera
4. **Parser conservador:** Mejor UNKNOWN que clasificación incorrecta
5. **Arquitectura simple:** Menos capas = menos bugs en MVP

---

**Última actualización:** 20 Dic 2025, 18:30 CST  
**Siguiente sesión:** Pydantic Schemas  
**Status general:** ✅ On track para beta Feb 2026