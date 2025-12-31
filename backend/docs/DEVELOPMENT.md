# 🛠️ Development Log - Saldo Backend

> **Purpose:** Track implementation decisions, bugs fixed, and learnings during development
> **Last updated:** 2025-12-31

---

## 📋 Index

- [Accounts Router Implementation](#accounts-router-implementation-31-dic-2025)
- [Technical Decisions](#technical-decisions)
- [Common Patterns](#common-patterns)
- [Bugs & Fixes](#bugs--fixes)
- [Learnings](#learnings)

---

## Accounts Router Implementation (31 dic 2025)

### Context
Implemented complete CRUD for `/api/accounts/*` router. Service layer already existed but router was missing.

### Implementation Details

**Files created/modified:**
1. `app/schemas/account.py` - Created Pydantic schemas
2. `app/routes/account.py` - Created router with 5 endpoints
3. `app/services/account_service.py` - Refactored `get_or_create_account()` return type
4. `app/services/statement_service.py` - Updated to handle tuple return
5. `app/main.py` - Registered router

**Endpoints implemented:**
```
GET    /api/accounts/              List with filters (bank_name, account_type, is_active)
POST   /api/accounts/              Create/get-or-create (201/200 status codes)
GET    /api/accounts/{id}          Get account by ID
PATCH  /api/accounts/{id}          Update display_name/is_active
DELETE /api/accounts/{id}          Soft delete (204 No Content)
```

### Technical Decisions Made

#### Decision 1: DELETE endpoint (soft delete alias)
**Problem:** Should we add DELETE if PATCH already allows `is_active=false`?

**Options considered:**
- A: Only PATCH (fewer endpoints)
- B: Add DELETE as alias (more RESTful)

**Decision:** ✅ Add DELETE endpoint

**Rationale:**
- RESTful semantics clearer for frontend ("eliminar cuenta" → DELETE, not PATCH)
- Standard market practice (Stripe, GitHub, Shopify use DELETE for soft-delete)
- Minimal cost (5 lines of code)
- Both approaches coexist without conflict

**Implementation:**
- Returns 204 No Content (no body)
- Idempotent (DELETE on already inactive account → still 204)
- Calls existing `deactivate_account()` service

#### Decision 2: POST status codes (201 vs 200)
**Problem:** Double query inefficiency - check existence, then call get_or_create

**Options considered:**
- A: Always return 201 (simpler, idempotent)
- B: Refactor service to return tuple (correct semantics, single query)

**Decision:** ✅ Refactor service to return `tuple[Account, bool]`

**Rationale:**
- Correct HTTP semantics (201 = created, 200 = already existed)
- Eliminates double query (better performance)
- Frontend can differentiate "created" vs "linked to existing"
- Standard pattern (Django `get_or_create()`, Rails `find_or_create_by`)

**Implementation:**
```python
# Before
def get_or_create_account(...) -> Account:
    # ...
    return account

# After
def get_or_create_account(...) -> tuple[Account, bool]:
    # ...
    return (account, created)  # created = True if new

# Router
account, created = account_service.get_or_create_account(...)
response.status_code = 201 if created else 200
```

#### Decision 3: AccountUpdate schema fields
**Problem:** Should `bank_name` and `account_type` be in AccountUpdate schema?

**Decision:** ✅ Keep in schema but service ignores them

**Rationale:**
- Service only updates `display_name` and `is_active` (immutable identity)
- Could remove from schema (cleaner) but requires extra maintenance
- For MVP: Schema shows all fields, service enforces immutability
- User can send them but they're silently ignored

**Future consideration:** Remove from schema post-MVP for clarity

---

## Technical Decisions

### Async vs Sync Functions

**Problem:** FastAPI supports `async def` but SQLAlchemy is synchronous.

**Decision:** Use `def` for all endpoint functions (not `async def`)

**Rationale:**
- SQLAlchemy core is synchronous (no native `await` support)
- Using `async def` without `await` is misleading
- FastAPI runs sync functions in thread pool automatically
- Semantic correctness > false promises

**Refactored:**
- `app/routes/account.py` - All 5 endpoints
- `app/routes/statements.py` - 5 endpoints

### Type Safety: UUID vs str

**Problem:** Passing `str(current_user.id)` to services expecting UUID

**Decision:** Always pass `current_user.id` directly (UUID type)

**Rationale:**
- Services typed to accept `UUID`, not `str`
- SQLAlchemy tolerates strings but breaks type safety
- Mypy/Pylance catch bugs if types are correct
- Explicit > implicit

**Refactored:**
- `app/routes/statements.py` - 5 occurrences fixed
- `app/routes/account.py` - 1 bug prevented during review

### Soft Delete Pattern

**Policy:** NEVER hard delete accounts (or statements/transactions)

**Implementation:**
- `is_active` flag on all models
- DELETE endpoint sets `is_active=False`
- GET endpoints default to `is_active=True` filter
- Preserves audit trail and historical data

**Documented in:**
- `app/models/account.py` docstring (lines 15-18)
- Service layer (`deactivate_account()`)

---

## Common Patterns

### Pattern 1: Ownership Validation
**All endpoints must filter by `user_id`**

```python
# Service layer
def get_account_by_id(db: Session, account_id: UUID, user_id: UUID) -> Account:
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == user_id  # ← Ownership check
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return account
```

**Why 404 instead of 403?**
- Avoids leaking existence of resources to unauthorized users
- Consistent behavior: "not found" = "doesn't exist OR not yours"

### Pattern 2: Get-or-Create
**Idempotent creation with automatic reactivation**

```python
def get_or_create_account(...) -> tuple[Account, bool]:
    account = db.query(Account).filter(...).first()

    if account:
        # Reactivate if soft-deleted
        if not account.is_active:
            account.is_active = True
        return (account, False)  # Existing

    # Create new
    new_account = Account(...)
    db.add(new_account)
    return (new_account, True)  # Created
```

**Benefits:**
- Prevents duplicates (unique constraint: user_id + bank_name + account_type)
- Handles soft-deleted accounts gracefully
- Returns semantic info (created vs existing)

### Pattern 3: Normalized Input
**Always normalize user input before DB operations**

```python
def _normalize_bank_name(bank_name: str) -> str:
    if not bank_name or not bank_name.strip():
        raise HTTPException(status_code=400, detail="bank_name is required")
    return bank_name.strip()

def _normalize_account_type(account_type: str) -> str:
    at = account_type.strip().upper()
    if at not in ALLOWED_ACCOUNT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid account_type")
    return at
```

**Why normalize in service layer (not schemas)?**
- Schemas validate format
- Services enforce business rules
- Normalization is business logic

---

## Bugs & Fixes

### Bug 1: Missing `.value` on Enum
**File:** `app/routes/account.py`
**Date:** 31 dic 2025
**Symptom:** POST endpoint would fail with `AttributeError: 'AccountType' object has no attribute 'strip'`

**Root cause:**
```python
# Wrong - passing Enum object
account_type=account_data.account_type

# Correct - extract string value
account_type=account_data.account_type.value
```

**Fix:** Add `.value` to extract string from Enum
**Prevented by:** Code review before testing

### Bug 2: Missing parameter to `db.refresh()`
**File:** `app/routes/account.py`
**Date:** 31 dic 2025
**Symptom:** Would fail with `TypeError: refresh() missing 1 required positional argument: 'instance'`

**Root cause:**
```python
# Wrong
db.refresh()

# Correct
db.refresh(account)
```

**Fix:** Pass account instance to refresh
**Prevented by:** Code review before testing

### Bug 3: Wrong user_id type in PATCH
**File:** `app/routes/account.py`
**Date:** 31 dic 2025
**Symptom:** Would fail with type error - service expects UUID, got User object

**Root cause:**
```python
# Wrong - passing entire User object
user_id=current_user

# Correct - extract UUID
user_id=current_user.id
```

**Fix:** Pass `current_user.id` instead of `current_user`
**Prevented by:** Code review before testing

### Bug 4: Missing `is_active` field in AccountUpdate
**File:** `app/schemas/account.py`
**Date:** 31 dic 2025
**Symptom:** PATCH endpoint returned 500 error - `AttributeError: 'AccountUpdate' object has no attribute 'is_active'`

**Root cause:**
- Schema had `bank_name`, `account_type`, `display_name`
- Service expected `is_active` parameter
- When field not sent in request, Pydantic doesn't create attribute

**Fix:**
```python
class AccountUpdate(BaseModel):
    bank_name: Optional[str] = None
    account_type: Optional[AccountType] = None
    display_name: Optional[str] = None
    is_active: Optional[bool] = None  # ← Added
```

**Also updated validator:**
```python
@model_validator(mode="after")
def check_at_least_one_field(self):
    if (self.bank_name is None and self.account_type is None and
        self.display_name is None and self.is_active is None):  # ← Added
        raise ValueError("At least one field must be provided")
    return self
```

**Found by:** Testing in Swagger
**Lesson:** Always test partial PATCH updates (not just full updates)

---

## Learnings

### Learning 1: Test endpoints immediately
**Context:** Bug 4 (`is_active` missing) only discovered during manual testing

**Lesson:**
- Code review catches logic errors
- Only runtime testing catches schema mismatches
- Test happy path + partial updates for PATCH endpoints

**Action:** Added comprehensive test cases to roadmap checklist

### Learning 2: Pydantic optional fields behavior
**Discovery:** When optional field is not in request, attribute doesn't exist on object

**Example:**
```python
# Schema
class AccountUpdate(BaseModel):
    display_name: Optional[str] = None
    is_active: Optional[bool] = None

# Request body
{"display_name": "foo"}

# In endpoint
update_data.display_name  # ✅ Works - "foo"
update_data.is_active     # ❌ AttributeError - attribute doesn't exist!
```

**Solution:** Always provide default values OR check with `getattr()`

### Learning 3: Status code semantics matter
**Context:** POST returning wrong status code (always 201)

**Learning:**
- 201 Created = "resource was created by this request"
- 200 OK = "request succeeded, resource already existed"
- Frontend can use this to show different messages
- Worth the small refactor to get semantics right

### Learning 4: Soft delete needs idempotent DELETE
**Context:** User can DELETE already-deleted account

**Options:**
- Return 404 (resource not found)
- Return 204 (idempotent success)

**Decision:** 204 idempotent

**Rationale:**
- DELETE is idempotent by HTTP spec
- User's intent: "make this account inactive"
- Already inactive = intent already satisfied
- Consistent with PUT/PATCH idempotence

---

## Next Steps

### Immediate (before next session)
- [ ] Git commit accounts router changes
- [ ] Test all 5 endpoints in Swagger
- [ ] Execute accounts testing checklist

### Short-term (this week)
- [ ] PDF cleanup + logging
- [ ] Complete testing checklist (all endpoints)
- [ ] README update

### Future considerations
- Remove `bank_name`/`account_type` from AccountUpdate schema (clarity)
- Add warning if DELETE account with recent transactions
- Implement reactivation endpoint (`POST /accounts/{id}/reactivate`)
- Consider batch operations (`POST /accounts/bulk`)

---

## Questions & Decisions Log

### Q: Should accounts be unique per (user, bank, type)?
**Answer:** Yes (MVP). Single account per bank+type prevents confusion.

**Rationale:**
- 80% users have 1 account per bank+type
- 15% freelancers might need multiple (track demand)
- 5% businesses need multi-account (out of scope for MVP)
- Decision: Keep constraint, implement multi-account if >5% users request

**Documented in:** Roadmap V2 business decisions section

### Q: Can user change bank_name or account_type?
**Answer:** No. These fields are immutable (define account identity).

**Rationale:**
- Changing would break unique constraint
- Better UX: Create new account, soft-delete old one
- Preserves data integrity

**Implementation:** Service ignores these fields in `update_account()`

---

**End of Development Log**
