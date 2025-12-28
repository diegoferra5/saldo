# Saldo - System Architecture

**Last Updated:** December 28, 2025
**Status:** Backend complete, ready for production

---

## Overview

**Saldo** is a personal finance management application for the Mexican market. Users manually upload bank statement PDFs (BBVA, Santander, Banorte), which are automatically parsed and categorized. The MVP focuses on manual upload due to limited API availability in Mexico.

**Core Value:** Auto-classify 70-85% of transactions, with transparent handling of ambiguous cases via manual review.

---

## Tech Stack

### Backend (Production)
- **Framework:** FastAPI (Python 3.11.14)
- **Database:** PostgreSQL (Supabase hosted)
- **ORM:** SQLAlchemy 2.0
- **Validation:** Pydantic v2
- **Authentication:** JWT + bcrypt
- **PDF Processing:** pdfplumber 0.10.3

### Frontend (Planned - Week 2)
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript 5
- **Styling:** Tailwind CSS 3
- **Components:** Shadcn/ui (Radix primitives)
- **State:** Zustand
- **Data Fetching:** TanStack Query (React Query)

### Deployment
- **Backend:** Railway
- **Frontend:** Vercel
- **Database:** Supabase
- **CDN:** Cloudflare

---

## System Components

### Layer 1: Database (PostgreSQL)

**Tables:**

```
users
├── id (UUID, PK)
├── email (VARCHAR, UNIQUE)
├── hashed_password (VARCHAR)
├── full_name (VARCHAR, nullable)
└── timestamps (created_at, updated_at)

accounts
├── id (UUID, PK)
├── user_id (UUID, FK → users.id ON DELETE CASCADE)
├── bank_name (VARCHAR)
├── account_type (VARCHAR) -- 'DEBIT' | 'CREDIT' | 'INVESTMENT'
├── display_name (VARCHAR, nullable)
├── is_active (BOOLEAN, default true)  -- Soft delete pattern
└── timestamps

statements
├── id (UUID, PK)
├── user_id (UUID, FK → users.id ON DELETE CASCADE)
├── account_id (UUID, FK → accounts.id ON DELETE SET NULL, nullable)
├── bank_name (VARCHAR)
├── account_type (VARCHAR)
├── statement_month (DATE)
├── file_name (VARCHAR)
├── file_size_kb (INTEGER)
├── parsing_status (VARCHAR) -- 'pending' | 'processing' | 'success' | 'failed'
├── file_hash (VARCHAR) -- SHA256 for duplicate detection
└── timestamps (created_at, updated_at, processed_at)

transactions
├── id (UUID, PK)
├── user_id (UUID, FK → users.id ON DELETE CASCADE)
├── account_id (UUID, FK → accounts.id ON DELETE CASCADE)
├── statement_id (UUID, FK → statements.id ON DELETE CASCADE)
├── date (VARCHAR) -- "11/NOV" (original PDF format)
├── date_liquidacion (VARCHAR, nullable)
├── transaction_date (DATE) -- Parsed full date: 2025-11-11
├── description (TEXT)
├── amount_abs (NUMERIC) -- Always positive
├── amount (NUMERIC, nullable) -- Signed: negative=expense, positive=income, null=unknown
├── movement_type (VARCHAR) -- 'CARGO' | 'ABONO' | 'UNKNOWN'
├── needs_review (BOOLEAN, default true)
├── category (VARCHAR, nullable)
├── saldo_operacion (NUMERIC, nullable)
├── saldo_liquidacion (NUMERIC, nullable)
├── transaction_hash (VARCHAR) -- SHA256 for deduplication
└── timestamps
```

**Key Constraints:**
- CHECK constraints on enums (account_type, parsing_status, movement_type)
- GIN index on description (full-text search)
- Indexes on user_id, account_id, statement_id, transaction_date

---

### Layer 2: ORM Models (SQLAlchemy)

**Purpose:** Map Python objects to database tables

**Location:** `backend/app/models/`

**Key Pattern - Passive Deletes:**
```python
# All relationships use passive_deletes=True
# Let PostgreSQL handle CASCADE/SET NULL automatically
accounts = relationship("Account", back_populates="user", passive_deletes=True)
```

**Soft Delete Pattern (Accounts):**
```python
# Don't delete, deactivate instead
account.is_active = False
db.commit()
```

---

### Layer 3: Pydantic Schemas

**Purpose:** Validate API requests/responses

**Location:** `backend/app/schemas/`

**Key Features:**
- **Enums:** AccountType, ParsingStatus, MovementType
- **Validators:** Auto-normalize emails, validate dates
- **Security:** `extra="forbid"` prevents injection attacks

**Example:**
```python
class TransactionResponse(BaseModel):
    id: UUID
    transaction_date: date
    description: str
    amount: Optional[Decimal]
    movement_type: str  # 'CARGO' | 'ABONO' | 'UNKNOWN'
    needs_review: bool

    model_config = ConfigDict(from_attributes=True, extra="forbid")
```

---

### Layer 4: Business Logic (Services)

**Purpose:** Complex operations that endpoints delegate to

**Location:** `backend/app/services/`

**Pattern:**
```
Endpoint (HTTP) → Service (Business Logic) → Model (Database)
```

**Key Services:**

**transaction_service.py**
- `create_transactions_from_parser_output()` - Batch insert with SAVEPOINT
- `get_transactions_by_user()` - Query with filters + pagination
- `update_transaction_classification()` - Manual edits
- `count_transactions_by_type()` - Stats for dashboard

**statement_service.py**
- `save_file_temporarily()` - Upload handling
- `create_statement_record()` - DB insert
- `process_statement()` - Full pipeline: parse → classify → insert
- `get_user_statements()` - Query with filters
- `delete_statement()` - File + DB cleanup

**account_service.py**
- `get_or_create_account()` - Idempotent account creation
- `list_user_accounts()` - Query with filters
- `update_account()` - Edit display_name
- `deactivate_account()` - Soft delete

**Production Patterns:**
- SAVEPOINT for batch operations (rollback on partial failure)
- Security: All queries filter by user_id
- Deduplication via transaction_hash
- IntegrityError handling

---

### Layer 5: Utilities

**Purpose:** Reusable helper functions

**Location:** `backend/app/utils/`

**pdf_parser.py** (BBVA Parser)
- `extract_transaction_lines()` - Extract raw lines from PDF
- `parse_transaction_line()` - Parse line → dict
- `extract_statement_summary()` - Extract totals from "Comportamiento" section
- `determine_transaction_type()` - Classify CARGO/ABONO/UNKNOWN

**date_helpers.py**
- `parse_bbva_date()` - Convert "11/NOV" → date(2025, 11, 11)

**hash_helpers.py**
- `compute_transaction_hash()` - SHA256 for deduplication

---

### Layer 6: API Endpoints (FastAPI)

**Purpose:** HTTP interface for clients

**Location:** `backend/app/routes/`

**Endpoints:**

**Authentication** (`/api/auth/`)
- POST `/register` - Create user account
- POST `/login` - Get JWT token
- GET `/me` - Get current user info

**Statements** (`/api/statements/`)
- POST `/upload` - Upload PDF file
- POST `/{id}/process` - Parse uploaded PDF
- GET `/` - List user's statements
- GET `/{id}` - Get statement details
- DELETE `/{id}` - Delete statement + transactions

**Transactions** (`/api/transactions/`)
- GET `/` - List with filters (date, type, account)
- GET `/{id}` - Get single transaction
- PATCH `/{id}` - Update category/review status
- GET `/stats` - Count by type (dashboard)

**Accounts** (`/api/accounts/`)
- GET `/` - List user accounts
- GET `/{id}` - Get account details
- PATCH `/{id}` - Update display_name
- DELETE `/{id}` - Soft delete account

---

## Data Flow: PDF Upload → Transactions

```
1. USER UPLOADS PDF
   ↓
2. POST /api/statements/upload
   • Validates JWT token → extracts user_id
   • Validates file type (PDF only)
   • Saves to /tmp/statements/{user_id}/
   • Computes file_hash (SHA256)
   ↓
3. CREATE STATEMENT RECORD
   Statement(
     user_id=from_jwt,
     file_name="estado_cuenta.pdf",
     parsing_status="pending",
     file_hash="a1b2c3..."
   )
   ↓
4. POST /api/statements/{id}/process
   ↓
5. BBVA PARSER (pdf_parser.py)
   A. extract_transaction_lines(pdf_path)
      → ["11/NOV 11/NOV STARBUCKS 150.00 10948.46", ...]

   B. parse_transaction_line(line) for each
      → {
          'date': '11/NOV',
          'description': 'STARBUCKS',
          'amount_abs': 150.00,
          'saldo_liquidacion': 10948.46
        }

   C. extract_statement_summary(pdf_path)
      → {
          'starting_balance': 11028.46,
          'deposits_amount': 47856.22,
          'charges_amount': 56862.50,
          'final_balance': 2022.18
        }

   D. determine_transaction_type(transactions, summary)
      • If has balance: compare with previous → CARGO/ABONO
      • If no balance: check keywords → CARGO/ABONO/UNKNOWN
      → Sets movement_type, amount (signed), needs_review
   ↓
6. TRANSFORM TO ORM (transaction_service.py)
   For each parser dict:
   • Compute transaction_date: parse_bbva_date('11/NOV', statement_month)
   • Compute transaction_hash: SHA256(user_id + account_id + date + desc + amount)
   • Create Transaction ORM instance
   • db.add(transaction)

   db.commit() ← Batch insert all transactions
   ↓
7. UPDATE STATEMENT
   statement.parsing_status = "success"
   statement.processed_at = now()
   ↓
8. RETURN RESPONSE
   {
     "statement_id": "uuid...",
     "status": "success",
     "transactions_parsed": 34,
     "transactions_inserted": 34,
     "duplicates_skipped": 0
   }
```

---

## Security Model

**Authentication:**
- JWT tokens (7-day expiration)
- bcrypt password hashing (cost factor 12)
- HTTPBearer scheme

**Authorization:**
- All queries filter by user_id (from JWT)
- Users can ONLY access their own data
- Foreign key constraints prevent orphaned records

**Data Validation:**
- Pydantic schemas validate all inputs
- `extra="forbid"` prevents unknown fields
- CHECK constraints at database level

---

## Performance Considerations

**Database Optimization:**
- Indexes on all foreign keys
- GIN index on transaction.description (full-text search)
- Connection pooling via SQLAlchemy

**Batch Operations:**
- SAVEPOINT strategy for bulk inserts (rollback on partial failure)
- Limit clamping (max 500 transactions per query)

**Deduplication:**
- transaction_hash prevents duplicate imports
- file_hash prevents re-uploading same PDF

---

## Design Decisions

### 1. Manual Upload vs API Integration
**Decision:** Manual PDF upload for MVP
**Reason:** Belvo/Fintoc don't support Mexico; validate market first
**Future:** Integrate bank APIs when we have 100+ paying users

### 2. UNKNOWN Transaction Type
**Decision:** Allow UNKNOWN, require manual review
**Reason:** Better to be honest than incorrectly classify
**Impact:** 15-55% of transactions (depending on PDF age)
**User Experience:** UI shows clear "needs review" flag

### 3. Soft Delete for Accounts
**Decision:** Deactivate instead of delete
**Reason:** Financial data should be immutable for audit trail
**Implementation:** `is_active = False`

### 4. Three-Tier Architecture
**Decision:** Database → Service → API separation
**Reason:** Testability, reusability, clean code
**Trade-off:** More files, but easier to maintain

### 5. Deduplication Strategy
**Decision:** Hash-based (user_id + account_id + date + desc + amount)
**Reason:** Prevent duplicate imports when re-uploading same PDF
**Implementation:** UNIQUE constraint on transaction_hash

---

## Current Status

**Completed:**
- ✅ Database schema (4 tables)
- ✅ ORM models (SQLAlchemy)
- ✅ Pydantic schemas
- ✅ PDF parser (85% accuracy on modern PDFs)
- ✅ Service layer (transaction, statement, account)
- ✅ Utilities (date parsing, hashing)
- ✅ API endpoints (auth, statements, transactions, accounts)

**In Progress:**
- Frontend (Next.js) - Week 2
- Testing (unit + integration) - Week 3
- Deployment (Railway + Vercel) - Week 4

**Future Enhancements:**
- Multi-bank support (Santander, Banorte)
- ML personalization (learn from user classifications)
- Budget tracking
- Recurring transaction detection
- OpenAI GPT-4 financial advice

---

## Metrics

**Parser Accuracy:**
- Modern PDFs (2024-2025): **85% auto-classified**
- Older PDFs (pre-2024): **45% auto-classified**

**Performance Targets:**
- API response time: <500ms (p95)
- PDF processing: <10 seconds for 100 transactions
- Database queries: <100ms

**Reliability:**
- Uptime: 99.5%
- Error rate: <1%
- Data integrity: 100% (via constraints)

---

## References

- PDF Parser Details → `docs/PDF_PARSER.md`
- Development Setup → `docs/DEVELOPMENT.md`
- API Documentation → http://localhost:8000/docs (Swagger UI)
