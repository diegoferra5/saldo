# Tomorrow's Roadmap - API Endpoints
**Date:** December 21, 2025
**Session Goal:** Build all API endpoints (6-8 hours)
**Starting Point:** Service layer complete ✅

---

## 🎯 Session Overview

**What We Completed Today:**
- ✅ transaction_service.py (SAVEPOINT, batch insert, deduplication)
- ✅ statement_service.py (upload, parse pipeline, account linking)
- ✅ account_service.py (get-or-create, soft delete, normalization)
- ✅ Production-ready patterns (IntegrityError handling, security, race conditions)

**What We're Building Tomorrow:**
- API endpoints that expose service layer functionality
- Full HTTP layer: routes, dependencies, request/response schemas
- Manual testing to verify end-to-end flow works

---

## 📋 Step-by-Step Roadmap

### **Step 1: Setup Dependencies (30 min)**

**Goal:** Centralize auth and database dependencies

**Files to Create:**

1. `backend/app/dependencies.py`:
```python
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    """Extract user_id from JWT token."""
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id",
            )

        return UUID(user_id_str)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
```

2. Add missing schemas to `backend/app/schemas/statements.py`:
```python
class StatementUploadResponse(BaseModel):
    statement_id: UUID
    file_name: str
    bank_name: str
    account_type: str
    statement_month: date
    file_size_kb: int
    parsing_status: str
    created_at: datetime

    class Config:
        from_attributes = True

class StatementProcessResponse(BaseModel):
    statement_id: UUID
    status: str  # "success" | "failed"
    transactions_found_lines: int
    transactions_parsed: int
    transactions_inserted: int
    duplicates_skipped: int
```

**Test:** Import dependencies in Python REPL to verify no errors.

---

### **Step 2: Statement Endpoints (2-3 hrs)**

**Goal:** Upload, process, and query statements

**File:** `backend/app/routes/statements.py`

**Endpoints to Build:**

1. **POST /api/statements/upload**
   - Receives: UploadFile + Form fields (bank_name, account_type, statement_month)
   - Calls: `save_file_temporarily()` → `create_statement_record()`
   - Returns: `StatementUploadResponse`
   - Auth: Required (get_current_user)

2. **POST /api/statements/{id}/process**
   - Receives: statement_id (path param)
   - Calls: `process_statement()`
   - Returns: `StatementProcessResponse`
   - Auth: Required
   - Note: This is where PDF parsing happens

3. **GET /api/statements**
   - Query params: bank_name (optional), account_type (optional)
   - Calls: `get_user_statements()`
   - Returns: `List[StatementListResponse]`
   - Auth: Required

4. **GET /api/statements/{id}**
   - Receives: statement_id (path param)
   - Calls: `get_statement_by_id()`
   - Returns: `StatementResponse`
   - Auth: Required

5. **DELETE /api/statements/{id}**
   - Receives: statement_id (path param)
   - Calls: `delete_statement()`
   - Returns: 204 No Content
   - Auth: Required

**Test:** Use curl to upload a PDF and process it.

---

### **Step 3: Transaction Endpoints (2-3 hrs)**

**Goal:** Query and update transactions

**File:** `backend/app/routes/transactions.py`

**Endpoints to Build:**

1. **GET /api/transactions**
   - Query params:
     - account_id (optional)
     - start_date (optional)
     - end_date (optional)
     - movement_type (optional)
     - needs_review (optional)
     - limit (default 100, max 500)
     - offset (default 0)
   - Calls: `get_transactions_by_user()`
   - Returns: `List[TransactionListResponse]`
   - Auth: Required

2. **GET /api/transactions/{id}**
   - Receives: transaction_id (path param)
   - Calls: Direct DB query with user_id check
   - Returns: `TransactionResponse`
   - Auth: Required

3. **PATCH /api/transactions/{id}**
   - Receives: transaction_id (path param) + `TransactionUpdate` body
   - Calls: `update_transaction_classification()`
   - Returns: `TransactionResponse`
   - Auth: Required

4. **GET /api/transactions/stats**
   - Calls: `count_transactions_by_type()`
   - Returns: `{"CARGO": 45, "ABONO": 12, "UNKNOWN": 3}`
   - Auth: Required

**Test:** Query transactions, update a category, verify stats.

---

### **Step 4: Account Endpoints (1-2 hrs)**

**Goal:** Manage user accounts

**File:** `backend/app/routes/accounts.py`

**Endpoints to Build:**

1. **GET /api/accounts**
   - Query params: bank_name (optional), account_type (optional), is_active (optional)
   - Calls: `list_user_accounts()`
   - Returns: `List[AccountListResponse]`
   - Auth: Required

2. **GET /api/accounts/{id}**
   - Receives: account_id (path param)
   - Calls: `get_account_by_id()`
   - Returns: `AccountResponse`
   - Auth: Required

3. **PATCH /api/accounts/{id}**
   - Receives: account_id (path param) + `AccountUpdate` body
   - Calls: `update_account()`
   - Returns: `AccountResponse`
   - Auth: Required

4. **DELETE /api/accounts/{id}**
   - Receives: account_id (path param)
   - Calls: `deactivate_account()`
   - Returns: 204 No Content
   - Auth: Required

**Test:** List accounts, update display_name, soft delete.

---

### **Step 5: Router Registration (15 min)**

**Goal:** Wire up all routes in main app

**File:** `backend/app/main.py`

**Updates:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import statements, transactions, accounts

app = FastAPI(
    title="Saldo API",
    version="1.0.0",
    description="Personal finance management for Mexico",
)

# CORS (if needed for frontend later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(statements.router, prefix="/api/statements", tags=["statements"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])

@app.get("/")
def root():
    return {"message": "Saldo API v1.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Test:** Visit http://localhost:8000/docs to see all endpoints in Swagger UI.

---

### **Step 6: Manual API Testing (1-2 hrs)**

**Goal:** Verify end-to-end flow works

**Test Cases:**

1. **Upload Flow:**
   ```bash
   # Upload statement
   curl -X POST "http://localhost:8000/api/statements/upload" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@statement.pdf" \
     -F "bank_name=BBVA" \
     -F "account_type=DEBIT" \
     -F "statement_month=2025-11-01"

   # Get statement_id from response
   STATEMENT_ID="..."

   # Process statement
   curl -X POST "http://localhost:8000/api/statements/$STATEMENT_ID/process" \
     -H "Authorization: Bearer $TOKEN"

   # List transactions
   curl -X GET "http://localhost:8000/api/transactions" \
     -H "Authorization: Bearer $TOKEN"
   ```

2. **Update Transaction:**
   ```bash
   curl -X PATCH "http://localhost:8000/api/transactions/$TRANSACTION_ID" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"category": "Food", "needs_review": false}'
   ```

3. **Deduplication Test:**
   - Upload same PDF twice
   - Verify duplicates_skipped > 0 on second upload

4. **Error Cases:**
   - Upload non-PDF file (should fail)
   - Upload file > 10MB (should fail)
   - Try to access another user's statement (should 404)

**Success Criteria:**
- ✅ Can upload PDF
- ✅ Can process PDF (transactions inserted)
- ✅ Can list transactions with filters
- ✅ Can update transaction classification
- ✅ Deduplication works (same PDF twice = 0 new transactions)
- ✅ Security works (can't access other user's data)

---

## 🚨 Common Issues & Solutions

### Issue 1: "Module not found" errors
**Solution:** Make sure you're in the correct directory and venv is activated:
```bash
cd /Users/diegoferra/Documents/ASTRAFIN/PROJECT/backend
source venv/bin/activate
```

### Issue 2: Database connection fails
**Solution:** Check .env file has correct DATABASE_URL from Supabase.

### Issue 3: JWT token validation fails
**Solution:** Make sure SECRET_KEY in .env matches what was used to create the token.

### Issue 4: File upload fails
**Solution:** Check /tmp/statements/{user_id}/ directory has write permissions.

### Issue 5: CORS errors (when testing with frontend later)
**Solution:** Update `allow_origins` in CORS middleware to include frontend URL.

---

## 📝 Notes for Tomorrow

**Before Starting:**
- Read this document
- Check that service layer files exist (transaction_service.py, etc.)
- Have a test PDF ready (BBVA statement)
- Have Postman or curl ready for API testing

**During Development:**
- Test each endpoint as you build it (don't wait until the end)
- Use Swagger UI at /docs to test endpoints visually
- Keep error messages user-friendly (not technical stack traces)

**After Completion:**
- Update PROGRESS_LOG.md with completion status
- Update CONTEXT.md with "Week 1 Complete"
- Consider: Deploy to Railway for remote testing?

---

## 🎯 End Goal

By end of tomorrow (Dec 21), you should have:
- ✅ Functional API that can:
  - Accept PDF uploads
  - Parse transactions
  - Return transaction data
  - Update classifications
- ✅ All endpoints documented in Swagger
- ✅ Manual testing complete
- ✅ Ready for frontend integration (Week 2)

**Estimated Time:** 6-8 hours
**Blocking:** Frontend development

---

**Good luck! You got this.** 🚀
