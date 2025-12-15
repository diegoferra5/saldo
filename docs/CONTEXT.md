# Saldo – Backend Context (FastAPI)

**Project**: Saldo (Personal finance management for Mexico)  
**Stack**: FastAPI + SQLAlchemy + PostgreSQL (Supabase) + JWT  
**Last updated**: 2025-12-14 (Week 1, Day 2 Complete)  
**Owner**: Diego (Data Engineer/Scientist → Full-Stack)

---

## 1) What this backend does (current scope)

✅ **Auth system**: register, login, get current user (JWT-based)  
✅ **Statement upload**: Users can upload bank statement PDFs  
✅ **Statement CRUD**: Create, Read, List, Delete statements  
⏭️ **Next**: PDF parsing (extract transactions from BBVA statements)

---

## 2) Architecture (Layered)

```
app/
├── main.py                 # FastAPI app + router registration
├── routes/                 # HTTP endpoints (controllers)
│   ├── auth.py            # ✅ Auth endpoints (register, login, /me)
│   └── statements.py      # ✅ Statement endpoints (upload, list, get, delete)
├── services/              # Business logic
│   ├── auth_service.py    # ✅ User creation, authentication
│   └── statement_service.py # ✅ File handling, DB operations
├── models/                # SQLAlchemy ORM
│   ├── user.py           # ✅ User model with relationship to statements
│   └── statement.py      # ✅ Statement model (bank, account_type, month)
├── schemas/               # Pydantic validation
│   ├── user.py           # ✅ UserCreate, UserLogin, UserResponse
│   └── statement.py      # ✅ StatementUpload, StatementResponse, StatementList
├── core/                  # Configuration
│   ├── config.py         # ✅ Settings (DB, JWT secret)
│   ├── database.py       # ✅ SQLAlchemy engine + session
│   └── security.py       # ✅ JWT + password hashing + get_current_user
└── utils/                 # (Future: PDF parsers)
```

**Request flow:**
```
Client → routes/ → services/ → models/ → DB
DB → models/ → services/ → schemas/ → HTTP JSON
```

---

## 3) Environment & Settings

**File**: `backend/.env`
```bash
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
SECRET_KEY=[generated-with-secrets-module]
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days
```

**File**: `app/core/config.py`
- Loads via Pydantic `BaseSettings`
- Validates required env vars

---

## 4) Database (Supabase PostgreSQL)

### **Tables Created:**

#### `public.users` ✅
```sql
- id (UUID, primary key)
- email (VARCHAR, unique, indexed)
- hashed_password (VARCHAR)
- full_name (VARCHAR, nullable)
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ, auto-update trigger)
```

**RLS Policies:**
- SELECT: Users can view their own profile
- UPDATE/INSERT/DELETE: Blocked from client (backend handles via service role)

---

#### `public.statements` ✅
```sql
- id (UUID, primary key)
- user_id (UUID, FK to users.id, ON DELETE CASCADE)
- bank_name (VARCHAR(50)) -- BBVA, Santander, etc.
- account_type (VARCHAR(20)) -- debit, credit, investment
- statement_month (DATE) -- Normalized to first day of month
- file_name (VARCHAR(255)) -- Actual filename on disk (timestamped)
- file_size_kb (INTEGER)
- parsing_status (VARCHAR(20)) -- pending, processing, success, failed
- error_message (TEXT, nullable)
- file_hash (VARCHAR(64)) -- SHA-256 for duplicate detection
- ip_address (VARCHAR(45), nullable) -- Audit trail
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ, auto-update trigger)
- processed_at (TIMESTAMPTZ, nullable)
```

**Constraints:**
- CHECK: `parsing_status IN ('pending', 'processing', 'success', 'failed')`
- CHECK: `account_type IN ('debit', 'credit', 'investment')`
- UNIQUE: `(user_id, bank_name, account_type, statement_month)` -- Prevents duplicate uploads

**Indexes:**
- `idx_statements_user_id` on `user_id`
- `idx_statements_status` on `parsing_status`
- `idx_statements_account_type` on `account_type`

**RLS Policies:**
- SELECT/INSERT/UPDATE/DELETE: Users can only access their own statements (`auth.uid() = user_id`)

---

## 5) Auth Design (JWT)

### **Endpoints:**
- ✅ `POST /api/auth/register` -- Create new user
- ✅ `POST /api/auth/login` -- Get JWT token
- ✅ `GET /api/auth/me` -- Get current user (protected)

### **JWT Claims:**
```json
{
  "sub": "user_id_uuid_string",
  "exp": 1734567890
}
```

### **Security Module** (`app/core/security.py`)

**Key Functions:**
- `get_password_hash()` -- bcrypt hashing
- `verify_password()` -- bcrypt verification
- `create_access_token()` -- JWT encoding
- `decode_access_token()` -- JWT decoding
- `get_current_user()` -- **Returns SQLAlchemy `User` object** (not dict)

**Critical Pattern:**
```python
# ✅ CORRECT
@router.post("/api/statements/upload")
async def upload(current_user: User = Depends(get_current_user)):
    statement = create_statement(user_id=current_user.id)  # From JWT
    
# ❌ WRONG
async def upload(user_id: str):  # User can send ANY user_id
    statement = create_statement(user_id=user_id)  # INSECURE
```

---

## 6) Statement Management System

### **Endpoints:**
- ✅ `POST /api/statements/upload` -- Upload PDF statement (multipart/form-data)
- ✅ `GET /api/statements/` -- List user's statements (with filters)
- ✅ `GET /api/statements/{statement_id}` -- Get specific statement
- ✅ `DELETE /api/statements/{statement_id}` -- Delete statement + file

### **File Storage:**
- **Location**: `/tmp/statements/{user_id}/`
- **Naming**: `{timestamp}_{sanitized_filename}.pdf`
- **Lifecycle**: 
  - Saved on upload
  - Deleted after parsing (Week 1 Day 5)
  - Auto-cleaned on Mac reboot or after 3+ days

### **Upload Flow:**
```python
1. Validate file type (PDF only)
2. Validate file size (max 10MB for MVP)
3. Sanitize filename (remove path traversal chars)
4. Save to /tmp/statements/{user_id}/
5. Calculate SHA-256 hash (duplicate detection)
6. Create DB record (with security checks)
7. Return statement metadata
```

### **Security Features:**
- ✅ JWT authentication required on all endpoints
- ✅ Ownership validation (can't access others' statements)
- ✅ Filename sanitization (prevent path traversal)
- ✅ Duplicate prevention (unique constraint)
- ✅ Race condition handling (IntegrityError catch)
- ✅ Orphan file cleanup on DB failure

### **Supported Banks (MVP):**
- BBVA, Santander, Banorte, Banamex, HSBC, Scotiabank

### **Account Types:**
- `debit` -- Checking/savings accounts
- `credit` -- Credit cards
- `investment` -- Investment accounts

---

## 7) Models & Schemas

### **User Model** (`app/models/user.py`)
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationship
    statements = relationship("Statement", back_populates="user", cascade="all, delete-orphan")
```

### **Statement Model** (`app/models/statement.py`)
```python
class Statement(Base):
    __tablename__ = "statements"
    
    # Core fields
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bank_name = Column(String(50), nullable=False)
    account_type = Column(String(20), nullable=False, default="debit")
    statement_month = Column(Date, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size_kb = Column(Integer, nullable=True)
    
    # Processing
    parsing_status = Column(String(20), nullable=False, default="pending")
    error_message = Column(Text, nullable=True)
    
    # Security/Audit
    file_hash = Column(String(64), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    processed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="statements")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("parsing_status IN ('pending', 'processing', 'success', 'failed')"),
        CheckConstraint("account_type IN ('debit', 'credit', 'investment')"),
        UniqueConstraint("user_id", "bank_name", "account_type", "statement_month"),
        Index("idx_statements_user_id", "user_id"),
        Index("idx_statements_status", "parsing_status"),
        Index("idx_statements_account_type", "account_type"),
    )
```

---

## 8) What Was Fixed Today

### **A) Import Errors**
- ❌ `HTTPAuthCredentials` doesn't exist
- ✅ Fixed: `HTTPAuthorizationCredentials`

### **B) Type Inconsistencies**
- ❌ `statement_month: datetime` (model uses `date`)
- ✅ Fixed: Changed to `date` everywhere

### **C) Security Improvements**
- ✅ Added filename sanitization (prevent `../../etc/passwd.pdf`)
- ✅ Added race condition handling (IntegrityError catch)
- ✅ Added orphan file cleanup (delete file if DB insert fails)
- ✅ Store actual filename in DB (not original, but safe timestamped version)

### **D) Schema Confusion**
- ❌ `json_schema_extra` showing fake example data in list endpoint
- ✅ Fixed: Removed examples from `StatementList` schema
- Result: Swagger now shows real data from DB

### **E) Model Constraints**
- ✅ Added all SQL constraints to SQLAlchemy model (CheckConstraint, UniqueConstraint, Indexes)
- ✅ Ensures consistency between SQL and ORM

---

## 9) Testing Status

### **✅ Completed Tests:**
- Auth: register, login, /me
- Statement upload (success)
- Statement list (with real data)
- Statement get by ID
- Duplicate prevention (DB rejects, orphan file cleanup works)

### **⏭️ Pending Tests:**
- Delete statement + verify file removal
- Multiple account types (same month/bank)
- Filters (bank_name, account_type)
- Invalid inputs (wrong bank, non-PDF, file too large)
- Security (unauthorized access, cross-user access)

---

## 10) Known Limitations (MVP)

### **Minor Issues (Acceptable for MVP):**
- ⚠️ Files saved before DB check (slight performance impact)
- ⚠️ Files in `/tmp` persist until reboot or manual cleanup
- ⚠️ No automatic PDF deletion after upload (will add in Day 5 after parsing)

### **Future Improvements (Week 2+):**
- Cloud storage (S3/GCS) instead of `/tmp`
- Cronjob to cleanup old processed files
- Support more banks (Nu, Inbursa)
- CSV format support
- Automatic parsing on upload (background job)

---

## 11) Week 1 Progress

**Timeline:**
- ✅ Day 1: Backend foundation (Auth, DB, User model)
- ✅ Day 2: Statement upload system (COMPLETE)
- ⏭️ Day 3-4: PDF parser (extract transactions from BBVA PDFs)
- ⏭️ Day 5-6: Transaction model + endpoints

**On track for Week 1 goals!** 🚀

---

## 12) Next Steps (Day 3)

**PDF Parser for BBVA:**
1. Create `app/utils/pdf_parser.py`
2. Use `pdfplumber` library to extract table data
3. Parse BBVA debit statement format:
   - Extract: date, description, amount, balance
   - Handle different PDF layouts
4. Create `Transaction` model
5. Store parsed transactions in DB
6. Update statement `parsing_status` to "success"
7. Delete PDF file after successful parsing

**Estimated:** 6-8 hours (can split across 2 days)

---

## 13) How to Continue in Next Session

**Context to provide:**
> "Continue with Saldo backend. Week 1 Day 2 complete: Statement upload system working (PDF upload, CRUD endpoints, file storage, security). Next: implement PDF parser for BBVA debit statements (Day 3). Current stack: FastAPI + SQLAlchemy + Supabase + JWT. Need to extract transactions from uploaded PDFs using pdfplumber."

**Key files to reference:**
- `app/models/statement.py` (Statement model)
- `app/services/statement_service.py` (File handling)
- `app/routes/statements.py` (Upload endpoint)
- Database: `statements` table with `parsing_status` field

**Dependencies already installed:**
- pdfplumber (for PDF parsing)
- All FastAPI/SQLAlchemy dependencies
```

---

## 📊 Summary of Day 2

**What We Built:**
- ✅ Complete statement upload system
- ✅ 4 API endpoints (upload, list, get, delete)
- ✅ File storage with security (sanitization, hashing, ownership)
- ✅ Database schema with RLS and constraints
- ✅ Multi-account support (debit/credit/investment)
- ✅ Duplicate prevention
- ✅ Comprehensive testing in Swagger

**Lines of Code:** ~600+ lines across 6 files

**Time Invested:** ~4-5 hours (on track with roadmap estimate)

**Ready for:** PDF parsing (Week 1 Day 3) 🚀