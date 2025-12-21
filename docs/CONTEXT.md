# Saldo - Estado del Proyecto
**Fecha:** 20 de Diciembre, 2025
**Fase:** Week 1, Day 7 - FASE 3 Completada ✅
**Siguiente:** Bug Fixes + Service Layer → Endpoints

---

## 🎯 Resumen Ejecutivo

**Saldo** es una aplicación de finanzas personales para el mercado mexicano que permite a usuarios:
- Subir estados de cuenta bancarios en PDF (BBVA, Banorte, Santander)
- Parsear y categorizar transacciones automáticamente (85% accuracy)
- Hacer seguimiento de presupuestos
- Recibir asesoría financiera vía AI (GPT-4) - Week 3

**MVP Approach:** Manual upload de PDFs (sin APIs bancarias por limitaciones de Belvo en México)

---
## 📊 Arquitectura Actual

### **Tech Stack**

**Backend (Week 1 - Actual):**
- FastAPI (Python 3.11.14)
- PostgreSQL (Supabase)
- SQLAlchemy ORM
- Pydantic v2 (validación)
- Autenticación JWT (bcrypt)
- pdfplumber (extracción PDFs)

**Frontend (Week 2-3):**
- Next.js 14 + React 18
- TypeScript
- Tailwind CSS
- Shadcn/ui components
- React Query (data fetching)
- Zustand (state management)

**AI/ML (Week 3-4):**
- OpenAI GPT-4 (asesoría financiera)
- Sklearn (categorización ML - futuro)

**Deployment (Week 4):**
- Railway (backend)
- Vercel (frontend)
- Supabase (database)
- Cloudflare (CDN)

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
├── account_type (VARCHAR(10)) -- 'DEBIT' | 'CREDIT' | 'INVESTMENT'
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

### **✅ FASE 3 - Pydantic Schemas (Completada)**
- [x] User schemas (UserCreate, UserLogin, UserResponse, Token)
- [x] Account schemas (AccountCreate, AccountUpdate, AccountResponse, AccountList)
- [x] Statement schemas (StatementUploadForm, StatementResponse, StatementList)
- [x] Transaction schemas (TransactionResponse, TransactionUpdate, TransactionList)
- [x] Enums (AccountType, ParsingStatus, MovementType)
- [x] Field validators y model validators

### **✅ FASE 4 - Core & Security (Completada)**
- [x] Config setup (environment variables)
- [x] Database connection (SQLAlchemy engine, SessionLocal)
- [x] Security module (JWT, bcrypt, password hashing)
- [x] get_current_user dependency

### **✅ FASE 5 - Parser BBVA (Completada)**
- [x] extract_transaction_lines() - Extrae líneas del PDF
- [x] parse_transaction_line() - Parsea cada línea
- [x] extract_statement_summary() - Extrae totales
- [x] determine_transaction_type() - Clasifica CARGO/ABONO/UNKNOWN
- [x] 85% accuracy en statements modernos (2024-2025)

### **⏳ FASE 6 - Bug Fixes & Utilities (Siguiente - 30 min)**
- [ ] Fix AccountType enum case (DB constraints → uppercase)
- [ ] Add `needs_review` to parser return dict
- [ ] Create `date_helpers.py` (parse DD/MMM → full date)
- [ ] Create `hash_helpers.py` (transaction deduplication)

### **⏳ FASE 7 - Service Layer (2-3 horas)**
- [ ] Transaction service (create, query, update)
- [ ] Statement service (upload, parse integration)
- [ ] Account service (CRUD operations)
- [ ] Unit tests para services

### **⏳ FASE 8 - API Endpoints (6-8 horas)**
- [ ] Auth endpoints (register, login, /me)
- [ ] Account endpoints (create, list, update)
- [ ] Statement upload endpoint
- [ ] Transaction endpoints (list, update, get)
- [ ] Integration tests

### **⏳ FASE 9 - Frontend MVP (Week 2 - 20-30 horas)**
- [ ] Setup Next.js 14 + TypeScript
- [ ] Auth UI (login, register, protected routes)
- [ ] Upload PDF interface (drag & drop)
- [ ] Transaction list view (table + filters)
- [ ] Transaction detail modal (edit category, review)
- [ ] Dashboard básico (totals, charts)
- [ ] Responsive design (mobile-first)

### **⏳ FASE 10 - Advanced Features (Week 3)**
- [ ] Budget creation & tracking
- [ ] Category management
- [ ] OpenAI GPT-4 integration (financial advice)
- [ ] Export transactions (CSV, Excel)
- [ ] Multi-bank support (Santander, Banorte parsers)

### **⏳ FASE 11 - Testing & Deployment (Week 4)**
- [ ] E2E tests (Playwright)
- [ ] Security audit
- [ ] Performance optimization
- [ ] Deploy to Railway + Vercel
- [ ] CI/CD pipeline (GitHub Actions)

---

## 🎯 Roadmap Detallado - 8 Semanas

### **Week 1 (Dec 13-20)** ✅ ~85% Completa
- [x] Database setup (Supabase)
- [x] Models ORM (SQLAlchemy)
- [x] Pydantic schemas
- [x] Core & Security
- [x] BBVA PDF Parser
- [ ] **→ Bug fixes (30 min)**
- [ ] **→ Service layer (2-3 hrs)**
- [ ] **→ API endpoints (6-8 hrs)**

**Meta Week 1:** API funcional que puede parsear PDFs y retornar transacciones

---

### **Week 2 (Dec 21-27)** - Frontend MVP
**Goal:** Usuario puede registrarse, subir PDF, ver transacciones

#### Backend Tasks (5-8 hrs):
- [ ] Deploy backend a Railway
- [ ] Configure CORS para frontend
- [ ] Add file upload size limits
- [ ] Error handling & logging
- [ ] API documentation (Swagger)

#### Frontend Tasks (20-30 hrs):
**Day 1-2 (Setup & Auth):**
- [ ] Create Next.js 14 project
- [ ] Setup Tailwind + Shadcn/ui
- [ ] Configure TypeScript
- [ ] Create API client (axios/fetch)
- [ ] Build Auth UI:
  - Login page
  - Register page
  - Protected route wrapper
  - JWT token storage (localStorage)

**Day 3-4 (Upload & Parse):**
- [ ] Build Upload interface:
  - Drag & drop component
  - File validation (PDF only, <10MB)
  - Upload progress bar
  - Statement month picker
  - Account selector
- [ ] Show parsing status (pending/processing/success/failed)
- [ ] Error handling UI

**Day 5-6 (Transaction List):**
- [ ] Transaction table component:
  - Date, description, amount, category
  - Filter by date range
  - Filter by movement type
  - Search by description
  - Sort by date/amount
  - Pagination (50 per page)
- [ ] Transaction detail modal:
  - Edit category (dropdown)
  - Mark as reviewed
  - View full details
- [ ] Loading states & skeletons

**Day 7 (Dashboard):**
- [ ] Summary cards:
  - Total income (ABONO)
  - Total expenses (CARGO)
  - Transactions needing review
  - Balance
- [ ] Simple chart (bar/line chart)
- [ ] Recent transactions widget

**Meta Week 2:** Usuario puede usar la app end-to-end

---

### **Week 3 (Dec 28-Jan 3)** - Advanced Features
**Goal:** Budget tracking + AI advice + Multi-bank

#### Backend Tasks (10-15 hrs):
- [ ] Budget CRUD endpoints
- [ ] Budget vs actual spending calculation
- [ ] OpenAI GPT-4 integration:
  - Endpoint: `POST /api/ai/advice`
  - Analyze spending patterns
  - Generate personalized recommendations
  - Max 500 tokens per request
- [ ] Santander parser (similar to BBVA)
- [ ] Banorte parser
- [ ] CSV export endpoint

#### Frontend Tasks (15-20 hrs):
- [ ] Budget creation UI:
  - Category selector
  - Monthly limit input
  - Active/inactive toggle
- [ ] Budget dashboard:
  - Progress bars (spent / limit)
  - Color coding (green/yellow/red)
  - Alerts when over budget
- [ ] AI advisor chat interface:
  - Input: "How can I save more?"
  - Output: GPT-4 response with actionable tips
  - Context: Last 3 months spending
- [ ] Category management:
  - Create custom categories
  - Merge categories
  - Bulk categorize
- [ ] Export button (CSV download)

**Meta Week 3:** App tiene features competitivas vs Mint/YNAB

---

### **Week 4 (Jan 4-10)** - Polish & Launch
**Goal:** Production-ready app deployed

#### Testing (15-20 hrs):
- [ ] Write E2E tests (Playwright):
  - Complete user journey
  - Upload → Parse → Categorize → Review
  - Budget creation → Tracking
- [ ] Security audit:
  - SQL injection tests
  - XSS tests
  - CSRF protection
  - Rate limiting
- [ ] Performance tests:
  - Load test (100 concurrent users)
  - Large PDF handling (500+ transactions)
  - Query optimization
  - Response time <500ms p95

#### DevOps (10-15 hrs):
- [ ] GitHub Actions CI/CD:
  - Auto-deploy to staging on PR
  - Run tests on every commit
  - Auto-deploy to production on merge to main
- [ ] Monitoring:
  - Sentry (error tracking)
  - PostHog (analytics)
  - Uptime monitoring
- [ ] Database backups (daily)
- [ ] SSL certificates
- [ ] Custom domain (saldo.mx)

#### Documentation (5-10 hrs):
- [ ] API documentation (complete Swagger)
- [ ] User guide (video + written)
- [ ] Developer onboarding guide
- [ ] Deployment runbook

**Meta Week 4:** App live en producción, monitoreada, documentada

---

### **Weeks 5-8 (Jan 11-Feb 9)** - Beta Testing & Iteration
**Goal:** 50+ active users, 70%+ retention

#### Week 5 (Jan 11-17):
- [ ] Private beta launch (10 users)
- [ ] Collect feedback
- [ ] Fix critical bugs
- [ ] Improve onboarding

#### Week 6 (Jan 18-24):
- [ ] Public beta launch (social media, Product Hunt)
- [ ] User interviews (5-10 users)
- [ ] Analytics implementation
- [ ] Feature prioritization based on usage

#### Week 7 (Jan 25-31):
- [ ] Implement top 3 requested features
- [ ] Performance optimizations
- [ ] Mobile responsiveness improvements
- [ ] Email notifications (weekly summary)

#### Week 8 (Feb 1-9):
- [ ] Marketing push
- [ ] User acquisition campaigns
- [ ] Referral program
- [ ] Pricing model finalization (freemium)

**Target Feb 9, 2026:**
- 50+ active users
- 70%+ retention
- 4.0+ rating
- $0 MRR → $500 MRR (10 paying users @ $50/month)

---

## 📁 Estructura del Proyecto (Actualizada)

```
PROJECT/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py              # ✅ Settings
│   │   │   ├── database.py            # ✅ SQLAlchemy setup
│   │   │   └── security.py            # ✅ JWT + bcrypt
│   │   ├── models/
│   │   │   ├── user.py                # ✅ User ORM
│   │   │   ├── account.py             # ✅ Account ORM
│   │   │   ├── statement.py           # ✅ Statement ORM
│   │   │   └── transaction.py         # ✅ Transaction ORM
│   │   ├── schemas/
│   │   │   ├── user.py                # ✅ User Pydantic
│   │   │   ├── account.py             # ✅ Account Pydantic
│   │   │   ├── statement.py           # ✅ Statement Pydantic
│   │   │   └── transactions.py        # ✅ Transaction Pydantic
│   │   ├── api/
│   │   │   ├── deps.py                # ⏳ Dependencies (get_db, get_current_user)
│   │   │   └── v1/
│   │   │       ├── auth.py            # ⏳ Auth endpoints
│   │   │       ├── accounts.py        # ⏳ Account CRUD
│   │   │       ├── statements.py      # ⏳ Upload endpoint
│   │   │       └── transactions.py    # ⏳ Transaction endpoints
│   │   ├── services/
│   │   │   ├── transaction_service.py # ⏳ Transaction business logic
│   │   │   ├── statement_service.py   # ⏳ Statement + parse
│   │   │   └── account_service.py     # ⏳ Account CRUD
│   │   └── utils/
│   │       ├── pdf_parser.py          # ✅ BBVA parser
│   │       ├── date_helpers.py        # ⏳ Date parsing utilities
│   │       └── hash_helpers.py        # ⏳ Transaction hash
│   ├── tests/
│   │   ├── test_auth.py               # ⏳ Auth tests
│   │   ├── test_parser.py             # ⏳ Parser tests
│   │   ├── test_services.py           # ⏳ Service tests
│   │   └── test_integration.py        # ⏳ E2E tests
│   ├── main.py                        # ⏳ FastAPI app
│   ├── requirements.txt               # ✅ Dependencies
│   └── .env                           # ✅ Environment vars
│
├── frontend/                          # ⏳ Week 2
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/
│   │   │   │   ├── login/
│   │   │   │   └── register/
│   │   │   ├── (dashboard)/
│   │   │   │   ├── page.tsx           # Dashboard
│   │   │   │   ├── upload/            # Upload page
│   │   │   │   ├── transactions/      # Transaction list
│   │   │   │   └── budgets/           # Budget page
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── ui/                    # Shadcn components
│   │   │   ├── TransactionTable.tsx
│   │   │   ├── UploadDropzone.tsx
│   │   │   └── BudgetCard.tsx
│   │   ├── lib/
│   │   │   ├── api.ts                 # API client
│   │   │   └── utils.ts
│   │   └── styles/
│   │       └── globals.css
│   ├── public/
│   ├── package.json
│   └── tsconfig.json
│
└── docs/
    ├── CONTEXT.md                     # ✅ Este archivo
    ├── PROGRESS_LOG.md                # ✅ Log de progreso
    ├── PROJECT_STRUCTURE.md           # ✅ Estructura de archivos
    ├── ARCHITECTURE_DIAGRAM.md        # ✅ Diagramas técnicos
    ├── TECHNICAL_REVIEW.md            # ✅ Review técnico
    ├── EXECUTIVE_SUMMARY.md           # ✅ Resumen ejecutivo
    └── BUG_FIX_ROADMAP.md            # ✅ Roadmap de fixes
```

---

## 🚀 Frontend Stack Detallado (Week 2)

### **Core Technologies**
```json
{
  "framework": "Next.js 14 (App Router)",
  "language": "TypeScript 5",
  "styling": "Tailwind CSS 3",
  "components": "Shadcn/ui (Radix UI primitives)",
  "state": "Zustand (lightweight state management)",
  "data-fetching": "TanStack Query (React Query)",
  "forms": "React Hook Form + Zod validation",
  "charts": "Recharts or Chart.js",
  "icons": "Lucide React",
  "date": "date-fns"
}
```

### **Key Features**

**Authentication:**
- JWT stored in localStorage
- Protected routes with middleware
- Auto-refresh token logic
- Logout clears all state

**File Upload:**
- Drag & drop interface
- Client-side validation (type, size)
- Upload progress bar
- Preview before submit

**Transaction Management:**
- Virtualized list (react-window) for 500+ transactions
- Advanced filters (date, category, type, amount range)
- Bulk operations (categorize multiple)
- Export to CSV/Excel

**Real-time Updates:**
- WebSocket connection (optional Week 3)
- Optimistic UI updates
- Background sync

**Responsive Design:**
- Mobile-first approach
- Desktop: sidebar + main content
- Mobile: bottom navigation
- Tablet: optimized layouts

---

## 📊 Métricas de Éxito

### **Técnicas (Week 4)**
- ✅ 0 critical security vulnerabilities
- ✅ 99.5% uptime (Railway monitoring)
- ✅ <500ms API response time (p95)
- ✅ <3s page load (Lighthouse score >90)
- ✅ 80%+ test coverage

### **Producto (Week 8)**
- 🎯 50+ usuarios activos mensuales
- 🎯 70%+ retention (D7, D30)
- 🎯 4.0+ rating (user feedback)
- 🎯 10+ paying users ($500 MRR)
- 🎯 <5% error rate en parsing

### **Usuario (Week 8)**
- 🎯 80%+ recomendarían a un amigo (NPS)
- 🎯 "Me ahorró dinero" mencionado 5+ veces
- 🎯 Avg. 3 PDFs subidos por usuario
- 🎯 60%+ categorizan al menos 1 transacción

---

## 💡 Decisiones de Diseño Clave

### **1. Manual Upload vs API Automática**
**Decisión:** Manual upload MVP
**Razón:** Belvo no soporta México, validación de mercado primero
**Futuro:** Integrar API cuando tengamos 100+ usuarios pagando

### **2. Next.js App Router vs Pages Router**
**Decisión:** App Router (Next.js 14)
**Razón:** Server Components, mejor performance, futuro-proof
**Trade-off:** Curva de aprendizaje mayor

### **3. Monorepo vs Separate Repos**
**Decisión:** Separate repos (backend + frontend)
**Razón:** Deploy independiente, equipos pueden trabajar en paralelo
**Estructura:** /backend y /frontend en mismo PROJECT root

### **4. TypeScript en Frontend**
**Decisión:** Sí, mandatory
**Razón:** Type safety, mejor DX, menos bugs en producción
**Cost:** Setup inicial + learning curve

### **5. State Management: Zustand vs Redux**
**Decisión:** Zustand
**Razón:** Más simple, menos boilerplate, suficiente para MVP
**Alternativa:** Si app crece mucho, migrar a Redux Toolkit

### **6. Freemium Model**
**Decisión:** Free tier + Premium ($4.99/mes)
**Free:**
- 3 PDFs/mes
- Auto-classification básica
- Manual review
**Premium:**
- PDFs ilimitados
- ML personalizado (95%+ accuracy)
- AI financial advisor
- Export avanzado
- Multi-cuenta

---

## 🔑 Próximos Pasos Inmediatos

### **HOY (30 min):**
1. Fix AccountType enum case → uppercase
2. Add `needs_review` to parser dict
3. Create date_helpers.py
4. Create hash_helpers.py

### **Esta Semana (10-15 hrs):**
5. Create service layer (transaction, statement, account)
6. Build API endpoints (auth, accounts, upload, transactions)
7. Write integration tests
8. Deploy backend to Railway

### **Week 2 (20-30 hrs):**
9. Setup Next.js frontend
10. Build Auth UI
11. Build Upload + Transaction list
12. Connect frontend ↔ backend

---

## 📈 Diferencia: PROJECT_STRUCTURE vs ARCHITECTURE

### **PROJECT_STRUCTURE.md**
**Qué es:** Guía de *dónde está cada archivo*
**Para quién:** Nuevos developers, tú en 6 meses
**Contenido:**
- Estructura de carpetas
- Qué hace cada archivo
- Naming conventions
- Dónde poner nuevas features

**Ejemplo:**
```
"¿Dónde pongo mi nuevo endpoint?"
→ Ve a PROJECT_STRUCTURE.md
→ Dice: app/api/v1/
```

### **ARCHITECTURE_DIAGRAM.md**
**Qué es:** Guía de *cómo fluyen los datos*
**Para quién:** Tech leads, code reviewers
**Contenido:**
- Diagramas de flujo
- Data transformations
- Component dependencies
- Request → Response flow

**Ejemplo:**
```
"¿Cómo funciona el upload de PDF?"
→ Ve a ARCHITECTURE_DIAGRAM.md
→ Muestra: User → API → Parser → Service → DB
```

**Analogía:**
- **PROJECT_STRUCTURE** = Mapa de la ciudad (dónde está cada edificio)
- **ARCHITECTURE** = Diagrama de metro (cómo se conectan las estaciones)

---

## 🎓 Aprendizajes Clave

1. **Week 1 completada ≠ API funcional:** Falta service layer + endpoints
2. **Parser output ≠ DB input:** Necesitas transformación intermedia
3. **Frontend = 50% del trabajo:** No subestimar UI/UX
4. **Testing early = faster shipping:** Tests te dan confianza para iterar rápido
5. **Deploy early, deploy often:** No esperes a "perfecto"

---

**Última actualización:** 20 Dic 2025, 22:00 CST
**Estado actual:** Backend 85% completo, frontend 0%
**Blocker actual:** Bug fixes (30 min) → Service layer (3 hrs) → Endpoints (8 hrs)
**Target Week 1:** API funcional deployada a Railway
**Target Week 2:** Usuario puede usar app end-to-end
**Target Feb 9:** 50+ usuarios activos, $500 MRR
