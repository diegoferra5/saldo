# Saldo - Architecture & Data Flow
**Date:** December 20, 2025

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                          │
│                         (Next.js - Week 2+)                          │
│   • Upload PDF interface                                             │
│   • Transaction list/filtering                                       │
│   • Budget dashboard                                                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP/JSON
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           API LAYER                                  │
│                  FastAPI Endpoints (app/api/v1/)                     │
├─────────────────────────────────────────────────────────────────────┤
│  Auth:         POST   /api/auth/register                             │
│                POST   /api/auth/login                                │
│                GET    /api/auth/me                                   │
├─────────────────────────────────────────────────────────────────────┤
│  Accounts:     POST   /api/accounts                                  │
│                GET    /api/accounts                                  │
│                PATCH  /api/accounts/{id}                             │
├─────────────────────────────────────────────────────────────────────┤
│  Statements:   POST   /api/statements/upload                         │
│                GET    /api/statements                                │
│                GET    /api/statements/{id}                           │
├─────────────────────────────────────────────────────────────────────┤
│  Transactions: GET    /api/transactions?filters                      │
│                PATCH  /api/transactions/{id}                         │
│                GET    /api/transactions/{id}                         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      VALIDATION LAYER                                │
│                 Pydantic Schemas (app/schemas/)                      │
├─────────────────────────────────────────────────────────────────────┤
│  • UserCreate, UserLogin, UserResponse                               │
│  • AccountCreate, AccountUpdate, AccountResponse                     │
│  • StatementUploadForm, StatementResponse                            │
│  • TransactionResponse, TransactionUpdate                            │
│  • Enums: AccountType, ParsingStatus, MovementType                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       BUSINESS LOGIC LAYER                           │
│                   Services (app/services/)                           │
├─────────────────────────────────────────────────────────────────────┤
│  auth_service.py:                                                    │
│    • register_user()                                                 │
│    • authenticate_user()                                             │
│    • verify_token()                                                  │
├─────────────────────────────────────────────────────────────────────┤
│  statement_service.py:                                               │
│    • upload_and_parse_statement()                                    │
│    • update_parsing_status()                                         │
├─────────────────────────────────────────────────────────────────────┤
│  transaction_service.py:                                             │
│    • create_transaction_from_parser_dict()                           │
│    • get_transactions_with_filters()                                 │
│    • update_transaction_category()                                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
              ┌────────────────┴───────────────┐
              │                                │
              ▼                                ▼
┌──────────────────────────┐  ┌──────────────────────────────────────┐
│    PARSER UTILITIES      │  │       ORM LAYER                      │
│  app/utils/pdf_parser.py │  │  SQLAlchemy Models (app/models/)     │
├──────────────────────────┤  ├──────────────────────────────────────┤
│ • extract_transaction_   │  │  • User                              │
│   lines()                │  │  • Account                           │
│ • parse_transaction_     │  │  • Statement                         │
│   line()                 │  │  • Transaction                       │
│ • extract_statement_     │  │                                      │
│   summary()              │  │  Relationships:                      │
│ • determine_transaction_ │  │    User → Accounts (1:N)             │
│   type()                 │  │    User → Statements (1:N)           │
└──────────┬───────────────┘  │    User → Transactions (1:N)         │
           │                  │    Account → Statements (1:N)        │
           │                  │    Account → Transactions (1:N)      │
           │                  │    Statement → Transactions (1:N)    │
           └─────────────────→│                                      │
                              └──────────────┬───────────────────────┘
                                             │
                                             ▼
                              ┌──────────────────────────────────────┐
                              │      DATABASE LAYER                  │
                              │  PostgreSQL (Supabase)               │
                              ├──────────────────────────────────────┤
                              │  Tables:                             │
                              │    • users                           │
                              │    • accounts                        │
                              │    • statements                      │
                              │    • transactions                    │
                              │                                      │
                              │  Features:                           │
                              │    • Foreign Keys with CASCADE       │
                              │    • CHECK constraints               │
                              │    • Indexes for performance         │
                              │    • GIN index on description        │
                              │    • UUID primary keys               │
                              │    • Timezone-aware timestamps       │
                              └──────────────────────────────────────┘
```

---

## Upload & Parse Flow (Detailed)

```
USER UPLOADS PDF
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. API ENDPOINT: POST /api/statements/upload                    │
│    • Validates JWT token → extracts user_id                     │
│    • Validates file type (PDF only)                             │
│    • Validates file size (< 10MB)                               │
│    • Extracts StatementUploadForm:                              │
│        - statement_month: date                                  │
│        - account_id: Optional[UUID]                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. SAVE PDF TEMPORARILY                                         │
│    • Generate unique filename                                   │
│    • Save to backend/uploads/                                   │
│    • Compute file hash (SHA256)                                 │
│    • Get file size                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. CREATE STATEMENT RECORD (DB)                                 │
│    Statement:                                                   │
│      user_id: from JWT                                          │
│      account_id: from form (optional)                           │
│      bank_name: "BBVA" (hardcoded for MVP)                      │
│      account_type: from form                                    │
│      statement_month: from form (e.g., 2025-12-01)              │
│      file_name: uploaded filename                               │
│      file_size_kb: computed                                     │
│      file_hash: SHA256                                          │
│      parsing_status: "processing" ← Important!                  │
│      created_at: now()                                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. PARSE PDF (BBVA Parser)                                      │
│                                                                 │
│    A. extract_transaction_lines(pdf_path)                       │
│       • Scans all pages                                         │
│       • Finds "Detalle de Movimientos" section                  │
│       • Extracts lines matching: DD/MMM DD/MMM ...              │
│       • Returns: list of raw strings                            │
│                                                                 │
│    B. parse_transaction_line(line) for each line                │
│       • Regex match dates: 11/NOV 11/NOV                        │
│       • Parse amounts from right-to-left                        │
│       • Extract description (middle tokens)                     │
│       • Returns dict:                                           │
│         {                                                       │
│           'date': '11/NOV',                                     │
│           'date_liquidacion': '11/NOV',                         │
│           'description': 'STARBUCKS COFFEE',                    │
│           'amount_abs': 150.00,                                 │
│           'movement_type': None,  ← Not set yet                 │
│           'saldo_operacion': 10948.46,                          │
│           'saldo_liquidacion': 10948.46                         │
│         }                                                       │
│                                                                 │
│    C. extract_statement_summary(pdf_path)                       │
│       • Finds "Comportamiento" section                          │
│       • Extracts:                                               │
│         - starting_balance                                      │
│         - deposits_amount, n_deposits                           │
│         - charges_amount, n_charges                             │
│         - final_balance                                         │
│       • Validates: starting + deposits - charges = final        │
│       • Returns summary dict                                    │
│                                                                 │
│    D. determine_transaction_type(transactions, summary)         │
│       • For each transaction:                                   │
│         IF has saldo_liquidacion:                               │
│           compare with previous balance                         │
│           → balance up = ABONO, balance down = CARGO            │
│         ELSE:                                                   │
│           check keywords in description                         │
│           → "SPEI RECIBIDO" = ABONO                             │
│           → "RETIRO CAJERO" = CARGO                             │
│           → no match = UNKNOWN (needs_review = True)            │
│       • Sets:                                                   │
│         - movement_type: "CARGO" | "ABONO" | "UNKNOWN"          │
│         - amount: -150.00 (cargo) | 150.00 (abono) | None       │
│         - needs_review: True/False                              │
│       • Validates totals vs summary                             │
│       • Returns: list of classified transaction dicts           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. TRANSFORM PARSER OUTPUT → ORM INSTANCES                      │
│    (transaction_service.create_transaction_from_parser_dict)    │
│                                                                 │
│    For each parser dict:                                        │
│                                                                 │
│      A. Compute transaction_date                                │
│         parse_bbva_date('11/NOV', statement_month)              │
│         → date(2025, 11, 11)                                    │
│                                                                 │
│      B. Compute transaction_hash                                │
│         hash(user_id + account_id + date + desc + amount)       │
│         → SHA256 hex string                                     │
│                                                                 │
│      C. Create Transaction ORM instance                         │
│         Transaction(                                            │
│           id: auto-generated UUID                               │
│           user_id: from JWT                                     │
│           account_id: from statement                            │
│           statement_id: from step 3                             │
│           date: '11/NOV' (original)                             │
│           date_liquidacion: '11/NOV'                            │
│           transaction_date: date(2025, 11, 11) ← computed       │
│           description: 'STARBUCKS COFFEE'                       │
│           amount_abs: 150.00                                    │
│           amount: -150.00                                       │
│           movement_type: 'CARGO'                                │
│           needs_review: False                                   │
│           category: None (for MVP)                              │
│           saldo_operacion: 10948.46                             │
│           saldo_liquidacion: 10948.46                           │
│           transaction_hash: 'a1b2c3...' ← computed              │
│           created_at: auto (DB)                                 │
│           updated_at: auto (DB)                                 │
│         )                                                       │
│                                                                 │
│      D. db.add(transaction)                                     │
│                                                                 │
│    db.commit() ← Bulk insert all transactions                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. UPDATE STATEMENT STATUS                                      │
│    statement.parsing_status = "success"                         │
│    statement.processed_at = now()                               │
│    db.commit()                                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. CONVERT TO RESPONSE SCHEMA                                   │
│    StatementResponse.from_orm(statement)                        │
│    Returns:                                                     │
│      {                                                          │
│        "id": "uuid...",                                         │
│        "user_id": "uuid...",                                    │
│        "bank_name": "BBVA",                                     │
│        "account_type": "DEBIT",                                 │
│        "statement_month": "2025-12-01",                         │
│        "file_name": "estado_cuenta.pdf",                        │
│        "parsing_status": "success",                             │
│        "created_at": "2025-12-20T10:30:00",                     │
│        "processed_at": "2025-12-20T10:35:00"                    │
│      }                                                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    JSON RESPONSE → FRONTEND
```

---

## Query Flow: GET /api/transactions

```
USER REQUESTS TRANSACTIONS
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. API ENDPOINT: GET /api/transactions                          │
│    Query params:                                                │
│      ?account_id=uuid (optional)                                │
│      ?start_date=2025-11-01 (optional)                          │
│      ?end_date=2025-11-30 (optional)                            │
│      ?movement_type=CARGO (optional)                            │
│      ?needs_review=true (optional)                              │
│      ?limit=50                                                  │
│      ?offset=0                                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. VALIDATE JWT → Extract user_id                              │
│    Security dependency: get_current_user()                      │
│    Returns: User instance                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. BUILD QUERY (transaction_service)                            │
│    query = db.query(Transaction)                                │
│             .filter(Transaction.user_id == user.id)             │
│                                                                 │
│    IF account_id provided:                                      │
│      query = query.filter(Transaction.account_id == account_id) │
│                                                                 │
│    IF start_date/end_date provided:                             │
│      query = query.filter(                                      │
│        Transaction.transaction_date >= start_date,              │
│        Transaction.transaction_date <= end_date                 │
│      )                                                          │
│                                                                 │
│    IF movement_type provided:                                   │
│      query = query.filter(                                      │
│        Transaction.movement_type == movement_type               │
│      )                                                          │
│                                                                 │
│    IF needs_review provided:                                    │
│      query = query.filter(                                      │
│        Transaction.needs_review == needs_review                 │
│      )                                                          │
│                                                                 │
│    query = query.order_by(Transaction.transaction_date.desc())  │
│    query = query.limit(limit).offset(offset)                   │
│                                                                 │
│    transactions = query.all()                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. CONVERT TO RESPONSE SCHEMAS                                  │
│    [TransactionList.from_orm(t) for t in transactions]          │
│                                                                 │
│    Returns:                                                     │
│    [                                                            │
│      {                                                          │
│        "id": "uuid...",                                         │
│        "account_id": "uuid...",                                 │
│        "transaction_date": "2025-11-11",                        │
│        "description": "STARBUCKS COFFEE",                       │
│        "amount_abs": 150.00,                                    │
│        "amount": -150.00,                                       │
│        "movement_type": "CARGO",                                │
│        "category": null,                                        │
│        "needs_review": false                                    │
│      },                                                         │
│      ...                                                        │
│    ]                                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    JSON RESPONSE → FRONTEND
```

---

## Data Transformation Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                          RAW PDF                                 │
│   "11/NOV 11/NOV STARBUCKS COFFEE 150.00 10948.46 10948.46"     │
└────────────────────────────┬────────────────────────────────────┘
                             │ pdf_parser.py
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PARSER OUTPUT (Dict)                         │
│   {                                                              │
│     'date': '11/NOV',                                            │
│     'date_liquidacion': '11/NOV',                                │
│     'description': 'STARBUCKS COFFEE',                           │
│     'amount_abs': 150.00,                                        │
│     'movement_type': 'CARGO',                                    │
│     'amount': -150.00,                                           │
│     'needs_review': False,                                       │
│     'saldo_operacion': 10948.46,                                 │
│     'saldo_liquidacion': 10948.46                                │
│   }                                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │ transaction_service.py
                             │ + date_helpers.py
                             │ + hash_helpers.py
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  ORM INSTANCE (Transaction)                      │
│   Transaction(                                                   │
│     id=UUID('...'),                                              │
│     user_id=UUID('...'),                                         │
│     account_id=UUID('...'),                                      │
│     statement_id=UUID('...'),                                    │
│     date='11/NOV',                                               │
│     date_liquidacion='11/NOV',                                   │
│     transaction_date=date(2025, 11, 11),  ← COMPUTED             │
│     description='STARBUCKS COFFEE',                              │
│     amount_abs=Decimal('150.00'),                                │
│     amount=Decimal('-150.00'),                                   │
│     movement_type='CARGO',                                       │
│     needs_review=False,                                          │
│     category=None,                                               │
│     saldo_operacion=Decimal('10948.46'),                         │
│     saldo_liquidacion=Decimal('10948.46'),                       │
│     transaction_hash='a1b2c3...',  ← COMPUTED                    │
│     created_at=datetime(...),                                    │
│     updated_at=datetime(...)                                     │
│   )                                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │ SQLAlchemy
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE ROW                                  │
│   PostgreSQL transactions table                                  │
│   All fields stored with proper types (UUID, Date, Numeric...)  │
└────────────────────────────┬────────────────────────────────────┘
                             │ SQLAlchemy query
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  ORM INSTANCE (read from DB)                     │
│   Same as above, but loaded from database                        │
└────────────────────────────┬────────────────────────────────────┘
                             │ Pydantic .from_orm()
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              RESPONSE SCHEMA (TransactionResponse)               │
│   {                                                              │
│     "id": "123e4567-e89b-12d3-a456-426614174000",                │
│     "user_id": "123e4567-e89b-12d3-a456-426614174001",           │
│     "account_id": "123e4567-e89b-12d3-a456-426614174002",        │
│     "statement_id": "123e4567-e89b-12d3-a456-426614174003",      │
│     "date": "11/NOV",                                            │
│     "date_liquidacion": "11/NOV",                                │
│     "transaction_date": "2025-11-11",  ← Serialized as string    │
│     "description": "STARBUCKS COFFEE",                           │
│     "amount_abs": 150.00,  ← Decimal → float                     │
│     "amount": -150.00,                                           │
│     "movement_type": "CARGO",                                    │
│     "needs_review": false,                                       │
│     "category": null,                                            │
│     "saldo_operacion": 10948.46,                                 │
│     "saldo_liquidacion": 10948.46,                               │
│     "transaction_hash": "a1b2c3d4...",                           │
│     "created_at": "2025-12-20T10:30:00",                         │
│     "updated_at": "2025-12-20T10:30:00"                          │
│   }                                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │ FastAPI JSONResponse
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        JSON (HTTP Response)                      │
│   Sent to frontend over HTTP                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Critical Dependencies

```
┌──────────────────────┐
│    PDF Upload        │
│    (Endpoint)        │
└─────────┬────────────┘
          │
          │ REQUIRES
          ├─────────────────────┐
          │                     │
          ▼                     ▼
┌──────────────────┐  ┌──────────────────────┐
│  Statement       │  │  Account             │
│  (Model)         │  │  (Model)             │
│                  │  │                      │
│  - statement_month│◄─┤  - account_id        │
│  - account_id    │  │    (for linking)     │
└─────────┬────────┘  └──────────────────────┘
          │
          │ TRIGGERS
          ▼
┌──────────────────────┐
│   BBVA Parser        │
│   (pdf_parser.py)    │
│                      │
│  - extract_lines()   │
│  - parse_line()      │
│  - extract_summary() │
│  - classify_type()   │
└─────────┬────────────┘
          │
          │ REQUIRES
          ├──────────────────────────────┐
          │                              │
          ▼                              ▼
┌──────────────────┐          ┌──────────────────────┐
│  Date Helpers    │          │  Hash Helpers        │
│  (utils/)        │          │  (utils/)            │
│                  │          │                      │
│  parse_bbva_date()│         │  compute_hash()      │
│  → Converts      │          │  → Deduplication     │
│    '11/NOV'      │          │    SHA256            │
│    to full date  │          │                      │
└──────────────────┘          └──────────────────────┘
          │                              │
          │                              │
          └──────────────┬───────────────┘
                         │
                         │ CREATES
                         ▼
                ┌──────────────────────┐
                │   Transaction        │
                │   (ORM Instance)     │
                │                      │
                │  All fields mapped   │
                └──────────┬───────────┘
                           │
                           │ SAVES TO
                           ▼
                ┌──────────────────────┐
                │   PostgreSQL         │
                │   transactions table │
                └──────────────────────┘
```

---

## Missing Pieces (Before Endpoints)

1. **Utility Functions** (30 min)
   ```
   app/utils/date_helpers.py
     └── parse_bbva_date(date_str, statement_month) → date

   app/utils/hash_helpers.py
     └── compute_transaction_hash(...) → str
   ```

2. **Service Layer** (2-3 hours)
   ```
   app/services/transaction_service.py
     ├── create_transaction_from_parser_dict()
     ├── get_transactions_with_filters()
     └── update_transaction_category()

   app/services/statement_service.py
     ├── upload_and_parse_statement()
     └── update_parsing_status()
   ```

3. **Parser Update** (10 min)
   ```
   app/utils/pdf_parser.py
     parse_transaction_line() return dict:
       ✅ Add: 'needs_review': True/False
   ```

4. **Fix Enum Consistency** (10 min)
   ```
   Choose: Uppercase or lowercase for AccountType
   Update: DB constraints OR Pydantic enum
   ```

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js + React | UI (Week 2+) |
| **API** | FastAPI | REST endpoints |
| **Validation** | Pydantic v2 | Request/response schemas |
| **ORM** | SQLAlchemy | Database mapping |
| **Database** | PostgreSQL (Supabase) | Data persistence |
| **Auth** | JWT + bcrypt | Security |
| **PDF Parsing** | pdfplumber | Extract text from PDFs |
| **Deployment** | Railway (backend), Vercel (frontend) | Hosting |

---

**Status:** Architecture complete, ready for endpoint development after utility functions are added.
