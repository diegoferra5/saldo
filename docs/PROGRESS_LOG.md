# Saldo - Progress Log
**Project:** Saldo - Personal Finance Management App for Mexico
**Developer:** Diego
**Started:** December 13, 2025
**Current Status:** Week 1, Day 7 - Backend 85% Complete ✅

---

## 📊 Overall Progress

| Component | Status | Progress | Time Spent |
|-----------|--------|----------|------------|
| **Database** | ✅ Complete | 100% | 4 hrs |
| **ORM Models** | ✅ Complete | 100% | 3 hrs |
| **Pydantic Schemas** | ✅ Complete | 100% | 4 hrs |
| **Core & Security** | ✅ Complete | 100% | 2 hrs |
| **PDF Parser** | ✅ Complete | 100% | 8 hrs |
| **Service Layer** | ✅ Complete | 100% | 4 hrs |
| **API Endpoints** | ⏳ Next | 0% | 6-8 hrs estimated |
| **Frontend** | ⏳ Not Started | 0% | 30 hrs estimated |
| **Deployment** | ⏳ Not Started | 0% | 4 hrs estimated |

**Total Time Invested:** ~25 hours
**Remaining to MVP:** ~40 hours
**Target Launch:** Week 4 (Jan 4-10, 2026)

---

## ✅ Completed - Week 1 (Dec 13-20)

### Day 1 (Dec 13) - Environment Setup
**Time:** 2 hours

- [x] Installed Python 3.11.14 via Homebrew
- [x] Created virtual environment at `backend/venv/`
- [x] Installed all dependencies from `requirements.txt`
- [x] Configured VS Code to use venv interpreter
- [x] Created complete folder structure
- [x] Created `.gitignore`, `.env`, `.env.example`
- [x] Created FastAPI app with root + health check endpoints
- [x] Tested server at localhost:8000
- [x] Auto-generated Swagger docs at /docs
- [x] Renamed project from AstraFin to Saldo

**Deliverable:** Development environment ready ✅

---

### Days 2-3 (Dec 14-15) - Database & Models
**Time:** 7 hours

#### Database Setup (Supabase):
- [x] Created Supabase account
- [x] Created new project
- [x] Created 4 tables:
  - users (id, email, hashed_password, full_name, timestamps)
  - accounts (id, user_id, bank_name, account_type, is_active, timestamps)
  - statements (id, user_id, account_id, file info, parsing_status, timestamps)
  - transactions (id, user_id, account_id, statement_id, dates, amounts, classification, timestamps)
- [x] Set up Foreign Keys:
  - user_id → ON DELETE CASCADE
  - account_id → ON DELETE CASCADE (transactions), SET NULL (statements)
  - statement_id → ON DELETE CASCADE
- [x] Added CHECK constraints:
  - account_type IN ('DEBIT', 'CREDIT', 'INVESTMENT')
  - parsing_status IN ('pending', 'processing', 'success', 'failed')
  - movement_type IN ('CARGO', 'ABONO', 'UNKNOWN')
  - amount_abs >= 0
- [x] Created indexes on user_id, account_id, statement_id, transaction_date
- [x] Added GIN index on description (full-text search)
- [x] Set up Row Level Security policies

#### SQLAlchemy Models:
- [x] Created `app/core/database.py`:
  - SQLAlchemy engine
  - SessionLocal factory
  - get_db() dependency
- [x] Created `app/models/user.py`:
  - UUID primary key
  - Email unique constraint
  - Relationships: accounts, statements, transactions
  - passive_deletes=True
- [x] Created `app/models/account.py`:
  - Soft delete pattern (is_active)
  - Relationships: user, statements, transactions
- [x] Created `app/models/statement.py`:
  - File metadata tracking
  - Parsing status workflow
  - Relationships: user, account, transactions
- [x] Created `app/models/transaction.py`:
  - 3-way foreign keys (user, account, statement)
  - Date fields (original + parsed)
  - Amount fields (abs + signed)
  - Classification (movement_type, needs_review, category)
  - Deduplication (transaction_hash)

**Deliverable:** Database schema ready, ORM models complete ✅

---

### Days 4-5 (Dec 16-17) - Pydantic Schemas & Security
**Time:** 6 hours

#### Pydantic Schemas:
- [x] Created `app/schemas/user.py`:
  - UserBase (email, full_name)
  - UserCreate (+ password validation min 8 chars)
  - UserLogin (email, password)
  - UserResponse (public data, no password)
  - UserInDB (internal, with hashed_password)
  - Token, TokenWithUser
  - Field validators (normalize_full_name)
  - extra="forbid" for security
- [x] Created `app/schemas/account.py`:
  - AccountType enum (DEBIT, CREDIT, INVESTMENT)
  - AccountBase, AccountCreate, AccountUpdate, AccountResponse, AccountList
  - Field validators (normalize bank_name, display_name)
  - Model validators (at least one field for updates)
- [x] Created `app/schemas/statement.py`:
  - ParsingStatus enum (pending, processing, success, failed)
  - StatementUploadForm (Form-data parser)
  - StatementResponse (complete data)
  - StatementList (summarized data)
  - JSON schema examples
- [x] Created `app/schemas/transactions.py`:
  - MovementType enum (CARGO, ABONO, UNKNOWN)
  - TransactionResponse (complete data)
  - TransactionList (summarized data)
  - TransactionUpdate (manual edits)
  - Model validator (at least one field for updates)

#### Core & Security:
- [x] Created `app/core/config.py`:
  - Pydantic Settings for environment variables
  - DATABASE_URL, SECRET_KEY, ALGORITHM
  - PROJECT_NAME, VERSION, API_PREFIX
- [x] Created `app/core/security.py`:
  - Password hashing (bcrypt)
  - JWT token creation (7 days expiration)
  - JWT token decoding
  - get_current_user() dependency
  - HTTPBearer authentication
  - Password verification

**Deliverable:** Schemas + Security ready for endpoints ✅

---

### Days 6-7 (Dec 18-20) - BBVA PDF Parser
**Time:** 8 hours

#### Parser Development:
- [x] Created `app/utils/pdf_parser.py`
- [x] Implemented `extract_transaction_lines()`:
  - Scans all PDF pages
  - Finds "Detalle de Movimientos" section
  - Extracts lines matching: DD/MMM DD/MMM ...
  - Skips header and detail lines
  - Returns raw transaction strings
- [x] Implemented `parse_transaction_line()`:
  - Regex matching for dates (DD/MMM)
  - Parses amounts from right-to-left (always last)
  - Extracts description (middle tokens)
  - Returns dict with: date, date_liquidacion, description, amount_abs, saldos
  - Handles incomplete transactions (missing balances)
- [x] Implemented `extract_statement_summary()`:
  - Finds "Comportamiento" section
  - Extracts: starting_balance, deposits_amount, charges_amount, final_balance
  - Mathematical validation: starting + deposits - charges = final
  - Raises ValueError if summary incomplete or invalid
- [x] Implemented `determine_transaction_type()`:
  - Case A: Uses saldo_liquidacion (high confidence)
    - Balance up = ABONO
    - Balance down = CARGO
    - Balance same = use keywords or UNKNOWN
  - Case B: Uses keywords (lower confidence)
    - ABONO keywords: SPEI RECIBIDO, DEPOSITO, ABONO, REEMBOLSO, INTERESES
    - CARGO keywords: SPEI ENVIADO, RETIRO CAJERO, PAGO TARJETA, COMISION
    - No match = UNKNOWN (needs_review = True)
  - Validation: compares totals vs summary
  - Reports classification results

#### Testing:
- [x] Tested with Nov 2025 BBVA PDF: 34 transactions, 85% auto-classified
- [x] Tested with Aug 2023 BBVA PDF: 78 transactions, 45% auto-classified (older format)
- [x] Verified mathematical accuracy (totals match summary)
- [x] Confirmed UNKNOWN transactions flagged correctly

**Deliverable:** BBVA parser complete, 85% accuracy on modern PDFs ✅

---

### Day 7 (Dec 20 PM) - Service Layer Complete
**Time:** 4 hours

#### Service Layer Development:
- [x] Created `app/services/transaction_service.py`:
  - `_to_decimal()` - Safe numeric conversion
  - `_movement_type_to_db_value()` - Validation helper
  - `_compute_signed_amount()` - Amount calculation logic
  - `create_transaction_from_parser_dict()` - Single insert with SAVEPOINT
  - `create_transactions_from_parser_output()` - Batch insert
  - `get_transactions_by_user()` - Query with filters + pagination + limit clamping
  - `update_transaction_classification()` - Manual edits + auto-commit
  - `count_transactions_by_type()` - Stats for dashboard
  - IntegrityError handling with rollback
  - Decimal precision handling (hash computed AFTER Decimal conversion)
  - Movement type validation (must not be None)

- [x] Created `app/services/statement_service.py`:
  - `sanitize_filename()` - Security helper
  - `calculate_file_hash()` - SHA256 for duplicate detection
  - `save_file_temporarily()` - Upload to /tmp with validation
  - `create_statement_record()` - DB insert with duplicate prevention
  - `get_user_statements()` - Query with filters
  - `get_statement_by_id()` - Security-checked fetch
  - `delete_statement()` - File + DB cleanup
  - `process_statement()` - Full pipeline:
    - Parse PDF
    - Classify transactions
    - Get-or-create Account
    - Link Statement to Account
    - Batch insert transactions
    - Update parsing status
    - Single commit for atomicity

- [x] Created `app/services/account_service.py`:
  - `ALLOWED_ACCOUNT_TYPES` constant (DEBIT, CREDIT)
  - `_normalize_bank_name()` - Validation helper
  - `_normalize_account_type()` - Validation helper
  - `get_or_create_account()` - Idempotent with reactivation
  - `list_user_accounts()` - Query with filters
  - `get_account_by_id()` - Security-checked fetch
  - `update_account()` - Edit display_name
  - `deactivate_account()` - Soft delete
  - Race condition handling

**Key Patterns:**
- SAVEPOINT (`begin_nested()`) for batch operations
- IntegrityError → rollback → retry pattern
- Security: ALL queries filter by user_id
- Normalization helpers for data consistency
- Soft delete (never hard delete financial data)
- Optional display_name auto-fill on get_or_create

**Deliverable:** Complete service layer ready for endpoints ✅

---

## ⏳ In Progress - Week 1 Remaining

---

### API Endpoints (6-8 hours)
**Status:** Next task (Tomorrow - Dec 21)
**Dependencies:** ✅ Service layer complete

#### Roadmap for Tomorrow:
**Priority 1: Setup (30 min)**
- [ ] Create `app/dependencies.py`:
  - Extract `get_current_user()` from security.py
  - Import `get_db()` from database.py
- [ ] Add missing Pydantic schemas:
  - `StatementUploadResponse`
  - `StatementProcessResponse`

**Priority 2: Statement Endpoints (2-3 hrs)**
- [ ] Create `app/routes/statements.py`:
  - POST /api/statements/upload (File + Form → StatementResponse)
  - POST /api/statements/{id}/process (Parse PDF → ProcessResponse)
  - GET /api/statements (→ List[StatementList])
  - GET /api/statements/{id} (→ StatementResponse)
  - DELETE /api/statements/{id} (soft delete)

**Priority 3: Transaction Endpoints (2-3 hrs)**
- [ ] Create `app/routes/transactions.py`:
  - GET /api/transactions (filters → List[TransactionList])
  - GET /api/transactions/{id} (→ TransactionResponse)
  - PATCH /api/transactions/{id} (TransactionUpdate → TransactionResponse)
  - GET /api/transactions/stats (→ count by type)

**Priority 4: Account Endpoints (1-2 hrs)**
- [ ] Create `app/routes/accounts.py`:
  - GET /api/accounts (→ List[AccountList])
  - GET /api/accounts/{id} (→ AccountResponse)
  - PATCH /api/accounts/{id} (AccountUpdate → AccountResponse)
  - DELETE /api/accounts/{id} (soft delete)

**Priority 5: Router Registration (15 min)**
- [ ] Update `app/main.py`:
  - Include all routers with `/api` prefix
  - CORS middleware (if needed)
  - Test endpoints with Postman/curl

**Priority 6: Testing (1-2 hrs)**
- [ ] Manual API tests:
  - Upload PDF → Process → List transactions
  - Update transaction classification
  - Verify deduplication works
  - Test error cases

**Estimated Time:** 6-8 hours
**Target Completion:** End of Week 1 (Dec 21)
**Blocking:** Frontend development (Week 2)

---

## 🔮 Upcoming - Week 2-4

### Week 2 (Dec 21-27) - Frontend MVP
**Goal:** User can register, upload PDF, view transactions

#### Frontend Setup (Day 1-2):
- [ ] Create Next.js 14 project with TypeScript
- [ ] Setup Tailwind CSS + Shadcn/ui
- [ ] Configure API client (axios/fetch)
- [ ] Create Auth pages (login, register)
- [ ] Implement JWT storage (localStorage)
- [ ] Protected route wrapper

#### Upload & Parse (Day 3-4):
- [ ] Drag & drop PDF component
- [ ] File validation (PDF, <10MB)
- [ ] Upload progress bar
- [ ] Statement month picker
- [ ] Account selector
- [ ] Parsing status display

#### Transaction List (Day 5-6):
- [ ] Transaction table component
- [ ] Filters (date range, type, category)
- [ ] Search by description
- [ ] Sort by date/amount
- [ ] Pagination (50 per page)
- [ ] Transaction detail modal
- [ ] Edit category UI
- [ ] Mark as reviewed button

#### Dashboard (Day 7):
- [ ] Summary cards (income, expenses, needs review, balance)
- [ ] Simple chart (bar/line)
- [ ] Recent transactions widget
- [ ] Responsive design (mobile-first)

**Estimated Time:** 20-30 hours

---

### Week 3 (Dec 28-Jan 3) - Advanced Features
**Goal:** Budget tracking + AI advice + Multi-bank

#### Backend:
- [ ] Budget CRUD endpoints
- [ ] Budget vs actual calculation
- [ ] OpenAI GPT-4 integration endpoint
- [ ] Santander parser
- [ ] Banorte parser
- [ ] CSV export endpoint

#### Frontend:
- [ ] Budget creation UI
- [ ] Budget dashboard (progress bars)
- [ ] AI advisor chat interface
- [ ] Category management
- [ ] Bulk categorize
- [ ] Export button (CSV download)

**Estimated Time:** 25-35 hours

---

### Week 4 (Jan 4-10) - Testing & Deployment
**Goal:** Production-ready app deployed

#### Testing:
- [ ] E2E tests (Playwright)
- [ ] Security audit (SQL injection, XSS, CSRF)
- [ ] Performance tests (load testing, large PDFs)
- [ ] Response time optimization (<500ms p95)

#### DevOps:
- [ ] GitHub Actions CI/CD
- [ ] Deploy backend to Railway
- [ ] Deploy frontend to Vercel
- [ ] Setup monitoring (Sentry, PostHog)
- [ ] Database backups
- [ ] Custom domain (saldo.mx)
- [ ] SSL certificates

#### Documentation:
- [ ] Complete API documentation (Swagger)
- [ ] User guide (video + written)
- [ ] Developer onboarding guide
- [ ] Deployment runbook

**Estimated Time:** 30-40 hours

---

## 📈 Metrics & Goals

### Week 1 Target (Dec 13-20)
- ✅ Database schema complete
- ✅ ORM models complete
- ✅ Pydantic schemas complete
- ✅ Core & Security complete
- ✅ BBVA parser complete
- ⏳ Bug fixes (pending)
- ⏳ Service layer (pending)
- ⏳ API endpoints (pending)

**Progress:** 85% complete, 15% remaining (11 hrs)

---

### Week 2 Target (Dec 21-27)
- Backend deployed to Railway
- Frontend MVP deployed to Vercel
- User can: Register → Login → Upload PDF → View Transactions
- End-to-end flow working

---

### Week 4 Target (Jan 4-10)
- Production app live
- 10+ beta users testing
- Monitoring & analytics active
- Documentation complete

---

### Week 8 Target (Feb 9, 2026)
- 50+ active users
- 70%+ retention (D7, D30)
- 4.0+ rating
- 10+ paying users ($500 MRR)
- <5% error rate in parsing

---

## 🎓 Key Learnings

### Technical Learnings:
1. **Database-first design:** Defining schema first made ORM modeling smooth
2. **Pydantic validation:** extra="forbid" prevents injection attacks
3. **Parser design:** Conservative (UNKNOWN > incorrect) better than aggressive
4. **Soft delete:** Never delete financial data, only deactivate
5. **Passive deletes:** Let PostgreSQL handle cascades efficiently

### Process Learnings:
1. **Documentation matters:** CONTEXT.md keeps project organized
2. **Technical review early:** Found 3 critical bugs before building endpoints
3. **Test parser first:** 8 hours on parser saved debugging time later
4. **Incremental progress:** 2 hours/day better than 14 hours once/week
5. **Clear roadmap:** BUG_FIX_ROADMAP.md prevents getting lost

### Business Learnings:
1. **MVP first:** Manual upload validates market before API investment
2. **85% accuracy acceptable:** Perfect is enemy of good for MVP
3. **Freemium from start:** Free tier for growth, premium for revenue
4. **Beta testing critical:** 10 users Week 5, 50 users Week 8
5. **Time estimates:** Always 1.5x what you think (21 hrs → 32 hrs actual)

---

## 🚧 Known Issues & Blockers

### Critical (Must Fix Before Endpoints):
1. **AccountType enum case mismatch** - DB expects lowercase, schema uses uppercase
2. **Parser missing `needs_review` in return dict** - determine_transaction_type() sets it but doesn't return
3. **No transaction_date computation** - Parser returns '11/NOV', model needs full date
4. **No transaction_hash computation** - Deduplication not working

**Status:** All documented in BUG_FIX_ROADMAP.md, fixes planned

---

### Non-Critical (Can Fix Later):
1. **No Santander parser** - Only BBVA supported for MVP
2. **No CSV export** - Week 3 feature
3. **No budget tracking** - Week 3 feature
4. **No AI advisor** - Week 3 feature
5. **No email notifications** - Week 7 feature

---

## 📝 Important Commands

### Development Server:
```bash
cd /Users/diegoferra/Documents/ASTRAFIN/PROJECT/backend
source venv/bin/activate
uvicorn app.main:app --reload
# Server: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Database:
```bash
# Connect to Supabase
psql $DATABASE_URL

# Run migrations (future)
alembic upgrade head
```

### Testing:
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_parser.py -v

# Run with coverage
pytest --cov=app tests/
```

### Deployment (Week 4):
```bash
# Deploy backend (Railway)
railway up

# Deploy frontend (Vercel)
vercel deploy --prod
```

---

## 🎯 Next Session Checklist

### Before Starting:
- [ ] Read CONTEXT.md (updated)
- [ ] Read BUG_FIX_ROADMAP.md
- [ ] Open VS Code
- [ ] Activate venv
- [ ] Review technical review findings

### Start With:
1. **Bug fixes (30 min):**
   - Fix AccountType enum
   - Add needs_review to parser
   - Create date_helpers.py
   - Create hash_helpers.py

2. **Service layer (2-3 hrs):**
   - transaction_service.py
   - statement_service.py
   - account_service.py

3. **API endpoints (6-8 hrs):**
   - Auth endpoints
   - Account endpoints
   - Statement upload
   - Transaction endpoints

**Target:** Functional API by end of Week 1

---

## 💪 Motivation & Progress

**What You've Built:**
- ✅ Production-ready database schema
- ✅ Clean ORM architecture
- ✅ Excellent Pydantic validation
- ✅ Secure JWT authentication
- ✅ 85% accurate PDF parser
- ✅ Comprehensive technical documentation

**What's Left for MVP:**
- 🎯 11 hours of backend work (bug fixes + service + endpoints)
- 🎯 30 hours of frontend work (Next.js app)
- 🎯 4 hours of deployment
- **Total:** ~45 hours to MVP

**Progress:** 32% complete (21/66 hours invested)

**You're on track for Week 4 launch!** 🚀

---

**Last Updated:** December 20, 2025, 22:30 CST
**Next Session:** Bug fixes → Service layer → Endpoints
**Target This Week:** Functional API deployed to Railway
**Target Week 2:** Frontend MVP deployed to Vercel
**Target Week 4:** Production launch with beta users
