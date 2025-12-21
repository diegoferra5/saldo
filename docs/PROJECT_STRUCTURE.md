# Saldo - Project Structure Guide
**Purpose:** Reference guide for WHERE files are located and WHAT each file does
**Audience:** Future you, new developers, collaborators
**Last Updated:** December 20, 2025

---

## 🎯 Quick Navigation

**Looking for something specific?**
- New to the project? → Start with "High-Level Overview" below
- Need to add a feature? → Jump to "Where Do I Put..." section
- Want to understand data flow? → Check `ARCHITECTURE_DIAGRAM.md` instead
- Technical details? → See `TECHNICAL_REVIEW.md`

---

## 📚 Document Relationships

### This Document (PROJECT_STRUCTURE.md)
**What it is:** File system guide - WHERE things are
**Use when:** "Where do I put my new endpoint?"
**Example answer:** `backend/app/api/v1/auth.py`

### ARCHITECTURE_DIAGRAM.md
**What it is:** Data flow guide - HOW things connect
**Use when:** "How does PDF upload work?"
**Example answer:** Shows diagram: User → API → Parser → Service → DB

### TECHNICAL_REVIEW.md
**What it is:** Code quality analysis - WHAT needs fixing
**Use when:** "What bugs exist in my code?"
**Example answer:** Lists 3 critical issues with solutions

---

## 🏗️ High-Level Overview

```
/Users/diegoferra/Documents/ASTRAFIN/PROJECT/
├── backend/          # Server (FastAPI + Python) - Week 1
├── frontend/         # Client (Next.js + React) - Week 2
├── docs/             # Documentation you're reading now
├── .gitignore        # What Git ignores (secrets, dependencies)
└── README.md         # Quick start guide
```

**Current Focus:** Backend (Week 1)
**Next:** Frontend (Week 2)
**Both deployed:** Week 4

---

## 📂 Backend Structure (Detailed)

### Root Level (`/backend/`)

| File/Folder | Purpose | Status |
|-------------|---------|--------|
| `app/` | Main application code | ✅ Complete |
| `tests/` | Automated tests | ⏳ Week 1 |
| `uploads/` | Temporary PDF storage | Created |
| `venv/` | Virtual environment (Python packages) | ✅ Active |
| `main.py` | FastAPI entry point | ⏳ Week 1 |
| `requirements.txt` | Python dependencies list | ✅ Complete |
| `.env` | **SECRET** environment variables | ✅ Configured |
| `.env.example` | Template (safe to commit) | ✅ Created |
| `README.md` | Backend-specific docs | ⏳ Todo |

**Security Note:** `.env` is in `.gitignore` - never commit secrets!

---

### Core Configuration (`backend/app/core/`)

**Purpose:** Application-wide settings that everything else depends on

| File | What It Does | Key Functions | Status |
|------|-------------|---------------|--------|
| `config.py` | Loads environment variables | `Settings` class (DATABASE_URL, SECRET_KEY) | ✅ Done |
| `database.py` | Database connection setup | `engine`, `SessionLocal`, `get_db()` | ✅ Done |
| `security.py` | Authentication & encryption | `hash_password()`, `create_access_token()`, `get_current_user()` | ✅ Done |

**When to modify:**
- **config.py:** Adding new environment variables
- **database.py:** Changing connection pool settings
- **security.py:** Changing JWT expiration, adding 2FA

**Example usage:**
```python
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user

# In your endpoint:
@app.get("/protected")
def protected_route(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return {"user": user.email}
```

---

### Database Models (`backend/app/models/`)

**Purpose:** Define database table structure using SQLAlchemy ORM

**Philosophy:**
- Models ONLY map to existing database schema
- NO business logic here (that goes in services)
- NO validation here (that goes in Pydantic schemas)
- Database is source of truth (constraints enforced in DB)

| File | Table | Key Fields | Relationships | Status |
|------|-------|------------|---------------|--------|
| `user.py` | users | id, email, hashed_password, full_name | → accounts, statements, transactions | ✅ Done |
| `account.py` | accounts | id, user_id, bank_name, account_type, is_active | ← user, → statements, transactions | ✅ Done |
| `statement.py` | statements | id, user_id, account_id, file_name, parsing_status | ← user, account, → transactions | ✅ Done |
| `transaction.py` | transactions | id, user_id, account_id, statement_id, date, amount, movement_type | ← user, account, statement | ✅ Done |

**Key Patterns:**

**Soft Delete (Accounts):**
```python
# DON'T: db.delete(account)
# DO:
account.is_active = False
db.commit()
```

**Passive Deletes:**
```python
# All relationships have passive_deletes=True
# Let PostgreSQL handle CASCADE/SET NULL automatically
accounts = relationship("Account", passive_deletes=True)
```

**When to modify:**
- Adding new table → Create new model file
- Adding field to existing table → Update model + run migration

---

### API Schemas (`backend/app/schemas/`)

**Purpose:** Validate HTTP request/response data using Pydantic

**Difference from Models:**
- **Models (SQLAlchemy)** = Database structure
- **Schemas (Pydantic)** = API input/output validation

| File | Schemas Defined | Use Case | Status |
|------|----------------|----------|--------|
| `user.py` | UserCreate, UserLogin, UserResponse, Token | Auth endpoints | ✅ Done |
| `account.py` | AccountCreate, AccountUpdate, AccountResponse, AccountList | Account CRUD | ✅ Done |
| `statement.py` | StatementUploadForm, StatementResponse, StatementList | Upload endpoint | ✅ Done |
| `transactions.py` | TransactionResponse, TransactionUpdate, TransactionList | Transaction endpoints | ✅ Done |

**Key Features:**

**Enums:**
```python
# app/schemas/account.py
class AccountType(str, Enum):
    debit = "DEBIT"
    credit = "CREDIT"
    investment = "INVESTMENT"
```

**Validators:**
```python
# Auto-normalize input
@field_validator("email")
@classmethod
def lowercase_email(cls, v: str) -> str:
    return v.lower().strip()
```

**Security:**
```python
# Prevent extra fields (injection attack prevention)
model_config = ConfigDict(extra="forbid")
```

**When to modify:**
- Adding new endpoint → Create corresponding schemas
- Adding field validation → Add field_validator
- Changing API response → Update Response schemas

---

### API Endpoints (`backend/app/api/`)

**Purpose:** HTTP endpoints that clients call

**Structure:**
```
app/api/
├── deps.py           # Shared dependencies (get_db, get_current_user)
└── v1/               # API version 1
    ├── auth.py       # Authentication endpoints
    ├── accounts.py   # Account CRUD
    ├── statements.py # PDF upload
    └── transactions.py # Transaction management
```

**Endpoint Patterns:**

| HTTP Method | Pattern | Purpose | Example |
|-------------|---------|---------|---------|
| POST | `/resource` | Create | `POST /api/accounts` |
| GET | `/resources` | List all | `GET /api/accounts` |
| GET | `/resource/{id}` | Get one | `GET /api/accounts/uuid` |
| PATCH | `/resource/{id}` | Update | `PATCH /api/accounts/uuid` |
| DELETE | `/resource/{id}` | Delete | `DELETE /api/accounts/uuid` |

**Example Endpoint:**
```python
# app/api/v1/accounts.py
from fastapi import APIRouter, Depends
from app.schemas.account import AccountCreate, AccountResponse
from app.core.security import get_current_user

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])

@router.post("/", response_model=AccountResponse)
def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Business logic goes in services, not here
    return account_service.create_account(db, user.id, account)
```

**Status:**
- ⏳ **Not started** - Week 1 task (after service layer)

**When to modify:**
- Adding new feature → Create new endpoint
- Changing API behavior → Update endpoint logic
- Adding filters → Add query parameters

---

### Business Logic (`backend/app/services/`)

**Purpose:** Complex operations that endpoints delegate to

**Why separate from endpoints?**
- **Reusability:** Same logic can be called from multiple endpoints
- **Testability:** Test business logic without HTTP layer
- **Clean code:** Endpoints become thin wrappers

**Planned Services:**

| File | Responsibility | Key Functions | Status |
|------|---------------|---------------|--------|
| `transaction_service.py` | Transaction operations | create_transaction_from_parser_dict(), get_transactions_by_user(), update_transaction_classification() | ⏳ Week 1 |
| `statement_service.py` | Statement + parsing | upload_and_parse_statement(), update_parsing_status() | ⏳ Week 1 |
| `account_service.py` | Account CRUD | create_account(), get_user_accounts(), soft_delete_account() | ⏳ Week 1 |

**Example Flow:**
```
Endpoint (HTTP layer)
  ↓ Validates input (Pydantic)
  ↓ Calls Service
     ↓ Performs business logic
     ↓ Calls Model (Database layer)
        ↓ Saves to PostgreSQL
     ↓ Returns ORM instance
  ↓ Converts to Response schema (Pydantic)
  ↓ Returns JSON
```

**When to create:**
- Logic spans multiple endpoints → Extract to service
- Operation involves multiple database queries → Service
- Need to test without HTTP → Service

---

### Utilities (`backend/app/utils/`)

**Purpose:** Small, reusable helper functions

| File | What It Does | Key Functions | Status |
|------|-------------|---------------|--------|
| `pdf_parser.py` | Extract data from BBVA PDFs | extract_transaction_lines(), parse_transaction_line(), determine_transaction_type() | ✅ Done |
| `date_helpers.py` | Date parsing utilities | parse_bbva_date('11/NOV', statement_month) | ⏳ Week 1 |
| `hash_helpers.py` | Transaction deduplication | compute_transaction_hash() | ⏳ Week 1 |

**Parser Functions Explained:**

```python
# 1. Extract raw lines from PDF
extract_transaction_lines(pdf_path)
→ Returns: ["11/NOV 11/NOV STARBUCKS 150.00 10948.46", ...]

# 2. Parse each line into dict
parse_transaction_line(line)
→ Returns: {
    'date': '11/NOV',
    'description': 'STARBUCKS',
    'amount_abs': 150.00,
    'saldo_liquidacion': 10948.46
}

# 3. Classify as CARGO/ABONO/UNKNOWN
determine_transaction_type(transactions, summary)
→ Modifies transactions in-place, sets:
    'movement_type': 'CARGO' | 'ABONO' | 'UNKNOWN'
    'amount': -150.00 (negative for expenses)
    'needs_review': True/False
```

**Parser Accuracy:**
- Modern PDFs (2024-2025): **85% auto-classified**
- Older PDFs (pre-2024): **45% auto-classified** (less balance info)

**When to modify:**
- Adding Santander parser → Create new file
- Improving BBVA accuracy → Modify pdf_parser.py
- Adding new utility → Create new file

---

### Tests (`backend/tests/`)

**Purpose:** Automated testing to catch bugs

**Planned Structure:**
```
tests/
├── test_auth.py          # Auth endpoint tests
├── test_parser.py        # PDF parser tests
├── test_services.py      # Service layer tests
├── test_date_helpers.py  # Utility tests
├── test_hash_helpers.py  # Utility tests
└── test_integration.py   # End-to-end tests
```

**Test Types:**

**Unit Tests:**
```python
def test_parse_bbva_date():
    """Test date parsing logic"""
    result = parse_bbva_date('11/NOV', date(2025, 11, 1))
    assert result == date(2025, 11, 11)
```

**Integration Tests:**
```python
def test_upload_and_parse_flow():
    """Test complete upload → parse → store flow"""
    # 1. Upload PDF
    # 2. Parse transactions
    # 3. Verify in database
```

**Status:** ⏳ Week 1-4 (tests written alongside code)

**When to write:**
- Before building feature (TDD) → Write test first
- After building feature → Write test immediately
- Fixing bug → Write failing test, then fix

---

## 📁 Frontend Structure (Week 2)

```
frontend/
├── src/
│   ├── app/                    # Next.js 14 App Router
│   │   ├── (auth)/
│   │   │   ├── login/         # Login page
│   │   │   └── register/      # Register page
│   │   ├── (dashboard)/
│   │   │   ├── page.tsx       # Main dashboard
│   │   │   ├── upload/        # PDF upload page
│   │   │   ├── transactions/  # Transaction list
│   │   │   └── budgets/       # Budget management
│   │   ├── layout.tsx         # Root layout
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                # Shadcn/ui components (buttons, inputs, etc.)
│   │   ├── TransactionTable.tsx
│   │   ├── UploadDropzone.tsx
│   │   └── BudgetCard.tsx
│   ├── lib/
│   │   ├── api.ts             # API client (calls backend)
│   │   ├── utils.ts           # Helper functions
│   │   └── auth.ts            # JWT token management
│   └── styles/
│       └── globals.css
├── public/                     # Static assets (images, icons)
├── package.json               # JavaScript dependencies
├── tsconfig.json              # TypeScript config
└── tailwind.config.ts         # Tailwind CSS config
```

**Tech Stack:**
- **Framework:** Next.js 14 (App Router, Server Components)
- **Language:** TypeScript 5
- **Styling:** Tailwind CSS 3
- **Components:** Shadcn/ui (Radix UI primitives)
- **State:** Zustand (lightweight state management)
- **Data Fetching:** TanStack Query (React Query)
- **Forms:** React Hook Form + Zod validation
- **Charts:** Recharts
- **Icons:** Lucide React

**Key Pages:**

| Route | Component | Purpose | Week |
|-------|-----------|---------|------|
| `/login` | Login page | User authentication | 2 |
| `/register` | Register page | User signup | 2 |
| `/` | Dashboard | Summary cards, charts | 2 |
| `/upload` | Upload page | PDF upload interface | 2 |
| `/transactions` | Transaction list | View/filter/edit transactions | 2 |
| `/budgets` | Budget page | Create/track budgets | 3 |

**Status:** ⏳ Not started (Week 2)

---

## 📚 Documentation (`/docs/`)

| File | Purpose | Use When |
|------|---------|----------|
| `CONTEXT.md` | Current project state, roadmap, tech stack | "What's the overall status?" |
| `PROGRESS_LOG.md` | Detailed log of what's done/pending | "What did I complete today?" |
| `PROJECT_STRUCTURE.md` | This file! File system guide | "Where do I put X?" |
| `ARCHITECTURE_DIAGRAM.md` | Data flow diagrams | "How does X work?" |
| `TECHNICAL_REVIEW.md` | Code quality analysis (14 sections) | "What bugs exist?" |
| `EXECUTIVE_SUMMARY.md` | Quick 2-min review summary | "TL;DR of technical review?" |
| `BUG_FIX_ROADMAP.md` | Step-by-step bug fix guide | "How do I fix these bugs?" |
| `PDF_PARSER.md` | Parser details & performance | "How accurate is the parser?" |

---

## 🎯 Where Do I Put...?

### New API Endpoint
**Location:** `backend/app/api/v1/`
**Steps:**
1. Create function in appropriate file (auth.py, accounts.py, etc.)
2. Use router decorator: `@router.post("/path")`
3. Add to main.py: `app.include_router(router)`

### New Database Table
**Location:** `backend/app/models/`
**Steps:**
1. Create new model file (e.g., `budget.py`)
2. Define class inheriting from `Base`
3. Run migration: `alembic revision --autogenerate`

### Business Logic
**Location:** `backend/app/services/`
**Steps:**
1. Create service file (e.g., `budget_service.py`)
2. Define functions that endpoints will call
3. Import in endpoint file

### Helper Function
**Location:** `backend/app/utils/`
**Steps:**
1. Create utility file (e.g., `validators.py`)
2. Define function
3. Import where needed

### React Component
**Location:** `frontend/src/components/`
**Steps:**
1. Create .tsx file (e.g., `BudgetCard.tsx`)
2. Export component
3. Import in page

### New Page
**Location:** `frontend/src/app/`
**Steps:**
1. Create folder with page.tsx (e.g., `budgets/page.tsx`)
2. Implement component
3. Add navigation link

---

## 🔄 Typical Data Flows

### User Uploads PDF
```
1. Frontend: User drags PDF → UploadDropzone component
2. Frontend: Validates file (type, size)
3. Frontend: POST /api/statements/upload (multipart/form-data)
4. Backend: statements.py endpoint receives request
5. Backend: Calls statement_service.upload_and_parse_statement()
6. Service: Saves PDF to uploads/ folder
7. Service: Calls pdf_parser.extract_transaction_lines()
8. Parser: Returns list of transaction dicts
9. Service: Calls transaction_service.create_transaction_from_parser_dict() for each
10. Service: Updates statement.parsing_status = "success"
11. Backend: Returns StatementResponse (JSON)
12. Frontend: Shows success message + parsing results
```

### User Views Transactions
```
1. Frontend: GET /api/transactions?start_date=2025-11-01
2. Backend: transactions.py endpoint
3. Backend: Calls transaction_service.get_transactions_by_user(filters)
4. Service: Queries database with filters
5. Database: Returns Transaction ORM instances
6. Service: Returns list of Transactions
7. Backend: Converts to TransactionList schemas (Pydantic)
8. Backend: Returns JSON array
9. Frontend: TransactionTable renders data
```

---

## 🚫 .gitignore - What's Ignored

**Categories:**

**Secrets:**
- `.env` (contains DATABASE_URL, SECRET_KEY)
- `*.key`, `*.pem`

**Dependencies:**
- `venv/`, `node_modules/`
- `__pycache__/`, `*.pyc`

**Build Artifacts:**
- `dist/`, `build/`
- `.next/`

**User Files:**
- `uploads/*` (PDFs uploaded by users)
- `.DS_Store` (macOS)

**Why this matters:** Prevents committing 5GB of dependencies or leaking passwords

---

## 📝 Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Python files | snake_case.py | `transaction_service.py` |
| Python classes | PascalCase | `class User(Base)` |
| Python functions | snake_case | `def get_user_by_email()` |
| Constants | SCREAMING_CASE | `SECRET_KEY` |
| TypeScript files | PascalCase.tsx | `TransactionTable.tsx` |
| React components | PascalCase | `export function TransactionTable()` |

---

## 💡 Quick Tips

### Finding Things
- **Search by filename:** `cmd+p` in VS Code
- **Search by content:** `cmd+shift+f` in VS Code
- **Find function definition:** `cmd+click` on function name

### Understanding Code
1. **Start with schemas** (app/schemas/) → See what API accepts/returns
2. **Then check endpoint** (app/api/) → See how it processes requests
3. **Then check service** (app/services/) → See business logic
4. **Then check model** (app/models/) → See database structure

### Making Changes
1. **Read relevant docs first** (CONTEXT.md, ARCHITECTURE_DIAGRAM.md)
2. **Write test first** (tests/test_*.py)
3. **Make small changes** (one feature at a time)
4. **Test immediately** (`pytest`, manual testing)
5. **Update docs** (if needed)

---

## 🎓 Learning Resources

**Concepts:**
- **MVC Pattern:** Models (data) → Services (logic) → Routes (presentation)
- **Dependency Injection:** FastAPI's `Depends()` for database sessions, auth
- **ORM:** SQLAlchemy translates Python ↔ SQL
- **Pydantic:** Validates data automatically

**Documentation:**
- FastAPI: https://fastapi.tiangolo.com
- SQLAlchemy: https://docs.sqlalchemy.org
- Pydantic: https://docs.pydantic.dev
- Next.js: https://nextjs.org/docs
- Tailwind: https://tailwindcss.com/docs

---

## 📊 Project Status Summary

| Category | Status | Files | Progress |
|----------|--------|-------|----------|
| **Database** | ✅ Complete | 4 tables | 100% |
| **ORM Models** | ✅ Complete | 4 files | 100% |
| **Schemas** | ✅ Complete | 4 files | 100% |
| **Core** | ✅ Complete | 3 files | 100% |
| **Parser** | ✅ Complete | 1 file | 100% |
| **Services** | ⏳ Pending | 0/3 files | 0% |
| **API Endpoints** | ⏳ Pending | 0/4 files | 0% |
| **Frontend** | ⏳ Not Started | 0 files | 0% |

**Overall Backend:** 85% complete (21 hours invested)
**Remaining to MVP:** 45 hours (11 backend + 30 frontend + 4 deploy)

---

**Last Updated:** December 20, 2025, 23:00 CST
**Maintained By:** Diego
**Questions?** Add them to this doc as you learn!
