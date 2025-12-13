# Saldo - Progress Log & Context

**Project:** Saldo - Personal Finance Management App for Mexico
**Developer:** Diego
**Started:** December 13, 2025
**Current Status:** Week 1 - Day 1 Complete ✅

---

## 🎯 Project Vision

**What:** Personal finance app that connects to Mexican banks (starting with BBVA) to help users manage their money through:
- Automatic transaction categorization
- Budget tracking
- AI-powered financial advice (GPT-4)
- PDF bank statement parsing (manual upload MVP approach)

**Why Manual Upload MVP:** Unblocks development immediately without API limitations, validates product-market fit before investing in banking APIs.

**Target Market:** Mexico (BBVA, Santander, Banorte, etc.)

**Timeline:** 8 weeks to production launch with 50+ users

**Name Decision:** Changed from AstraFin to **Saldo** (simple, clear, memorable for Mexican market)

---

## 💻 Tech Stack

### Backend (Current Focus - Week 1-4)
- **Framework:** FastAPI (Python 3.11.14)
- **Database:** Supabase (PostgreSQL)
- **Auth:** JWT tokens + bcrypt password hashing
- **PDF Parsing:** pdfplumber + PyPDF2
- **AI:** OpenAI GPT-4 (Week 3)
- **Deploy:** Railway

### Frontend (Week 2+)
- **Framework:** Next.js + React
- **Styling:** Tailwind CSS
- **Deploy:** Vercel

### Development Environment
- **OS:** macOS (M1/M2)
- **Python:** 3.11.14 (via Homebrew)
- **Virtual Env:** venv (located at `backend/venv/`)
- **Editor:** VS Code
- **Note:** Also has Conda (base) but using venv for this project

---

## 📁 Project Structure
```
~/Documents/ASTRAFIN/PROJECT/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # ✅ FastAPI entry point (DONE)
│   │   ├── core/                   # Core configurations
│   │   │   ├── config.py           # TODO: Environment vars
│   │   │   ├── security.py         # TODO: JWT + bcrypt
│   │   │   └── database.py         # TODO: SQLAlchemy connection
│   │   ├── models/                 # Database tables (SQLAlchemy ORM)
│   │   │   ├── user.py             # TODO
│   │   │   ├── transaction.py      # TODO
│   │   │   ├── statement.py        # TODO
│   │   │   └── budget.py           # TODO
│   │   ├── schemas/                # API validation (Pydantic)
│   │   │   ├── user.py             # TODO
│   │   │   ├── transaction.py      # TODO
│   │   │   └── auth.py             # TODO
│   │   ├── routes/                 # API endpoints
│   │   │   ├── auth.py             # TODO: register, login
│   │   │   ├── statements.py       # TODO: upload endpoint
│   │   │   ├── transactions.py     # TODO: CRUD
│   │   │   └── budgets.py          # TODO (Week 3)
│   │   ├── services/               # Business logic
│   │   │   ├── auth_service.py     # TODO
│   │   │   ├── parser_service.py   # TODO
│   │   │   └── categorization.py   # TODO (Week 3)
│   │   └── utils/                  # Helpers
│   │       └── pdf_parser.py       # TODO: BBVA extractor
│   ├── tests/                      # TODO (Week 4)
│   ├── uploads/                    # Temporary PDF storage
│   ├── venv/                       # Virtual environment ✅
│   ├── requirements.txt            # ✅ Dependencies installed
│   ├── .env                        # TODO: Add Supabase credentials
│   └── .env.example                # ✅ Template created
├── frontend/                       # TODO (Week 2+)
├── docs/
│   ├── PROJECT_STRUCTURE.md        # ✅ Complete structure guide
│   └── PROGRESS_LOG.md             # ✅ This file
├── .vscode/
│   └── settings.json               # ✅ Interpreter configured
├── .gitignore                      # ✅ Created
└── README.md
```

---

## ✅ Completed Tasks (Week 1 - Day 1)

### Environment Setup
- [x] Installed Python 3.11.14 via Homebrew
- [x] Created virtual environment at `backend/venv/`
- [x] Installed all dependencies from `requirements.txt`
- [x] Configured VS Code to use venv interpreter
- [x] Created `.vscode/settings.json` for workspace

### Project Structure
- [x] Created complete folder structure
- [x] All `__init__.py` files created
- [x] Created `.gitignore` with proper exclusions
- [x] Created `.env` and `.env.example`
- [x] Documented structure in `PROJECT_STRUCTURE.md`

### FastAPI Application
- [x] Created `backend/app/main.py` with:
  - FastAPI app instance
  - CORS middleware configured
  - Root endpoint (`GET /`)
  - Health check endpoint (`GET /health`)
- [x] Successfully ran server with `uvicorn app.main:app --reload`
- [x] Tested endpoints in browser (localhost:8000)
- [x] Auto-generated Swagger docs at `/docs`

### Branding
- [x] Renamed project from AstraFin to **Saldo**
- [x] Updated all API responses with new branding

---

## 🔧 Current Setup Details

### Dependencies Installed (requirements.txt)
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
email-validator==2.1.0
pdfplumber==0.10.3
PyPDF2==3.0.1
python-dateutil==2.8.2
```

### How to Start Development Server
```bash
cd ~/Documents/ASTRAFIN/PROJECT/backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Server runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

### VS Code Issues Resolved
- **Issue:** Pylance not detecting FastAPI in venv
- **Solution:** Created `.vscode/settings.json` with explicit interpreter path
- **Issue:** Terminal not auto-activating venv
- **Solution:** Manual activation with `source venv/bin/activate` each time

### Important Notes for Tomorrow
- **DO NOT use the Run ▶️ button** - it uses wrong Python interpreter
- **Always activate venv first** in terminal before running commands
- **Use `uvicorn` command** for FastAPI, not `python main.py`
- Check `(venv)` appears in terminal prompt before working

---

## 🎯 Next Steps (Week 1 - Days 2-7)

### Immediate Priority (Day 2 - Tomorrow)

#### 1. Supabase Setup (1-2 hours)
**Goal:** Get PostgreSQL database running

Tasks:
- [ ] Create Supabase account (https://supabase.com)
- [ ] Create new project
- [ ] Get connection string from project settings
- [ ] Add to `backend/.env`:
```
  DATABASE_URL=postgresql://user:password@host:port/database
```
- [ ] Test connection

#### 2. Database Connection (1 hour)
**File:** `backend/app/core/database.py`

Tasks:
- [ ] Create SQLAlchemy engine
- [ ] Create SessionLocal factory
- [ ] Create `get_db()` dependency
- [ ] Test connection with simple query

#### 3. First Model - User (1 hour)
**File:** `backend/app/models/user.py`

Tasks:
- [ ] Define User table with SQLAlchemy
- [ ] Fields: id, email, hashed_password, full_name, created_at
- [ ] Run Alembic migration (or create tables directly)
- [ ] Verify table exists in Supabase dashboard

---

### Day 3: Authentication Endpoints (4-5 hours)

#### 1. Security Module
**File:** `backend/app/core/security.py`

- [ ] Password hashing functions (bcrypt)
- [ ] JWT token creation
- [ ] Token verification
- [ ] Get current user dependency

#### 2. Auth Schemas
**File:** `backend/app/schemas/auth.py`

- [ ] `UserCreate` schema (email, password, full_name)
- [ ] `UserLogin` schema (email, password)
- [ ] `TokenResponse` schema (access_token, token_type)
- [ ] `UserResponse` schema (id, email, full_name)

#### 3. Auth Service
**File:** `backend/app/services/auth_service.py`

- [ ] `register_user()` function
- [ ] `authenticate_user()` function
- [ ] `get_user_by_email()` function

#### 4. Auth Routes
**File:** `backend/app/routes/auth.py`

- [ ] `POST /api/auth/register` endpoint
- [ ] `POST /api/auth/login` endpoint
- [ ] `GET /api/auth/me` endpoint (requires auth)
- [ ] Test all endpoints with Postman/Thunder Client

---

### Day 4: PDF Upload Foundation (3-4 hours)

#### 1. Statement Routes
**File:** `backend/app/routes/statements.py`

- [ ] `POST /api/statements/upload` endpoint
- [ ] Accept PDF file upload
- [ ] Validate file type and size
- [ ] Save to `backend/uploads/` temporarily
- [ ] Return success response

#### 2. Statement Model
**File:** `backend/app/models/statement.py`

- [ ] Define Statement table
- [ ] Fields: id, user_id, bank_name, file_name, parsing_status, created_at
- [ ] Create migration

---

### Day 5: BBVA PDF Parser (4-6 hours)

#### 1. PDF Parser Utility
**File:** `backend/app/utils/pdf_parser.py`

- [ ] Function to extract BBVA transactions
- [ ] Use pdfplumber to read PDF tables
- [ ] Parse dates, descriptions, amounts, balances
- [ ] Return list of transaction dictionaries
- [ ] Test with real BBVA PDF

#### 2. Parser Service
**File:** `backend/app/services/parser_service.py`

- [ ] Orchestrate PDF parsing workflow
- [ ] Call pdf_parser utility
- [ ] Validate extracted data
- [ ] Save transactions to database
- [ ] Update statement parsing_status

#### 3. Transaction Model & Routes
**File:** `backend/app/models/transaction.py`

- [ ] Define Transaction table
- [ ] Fields: id, user_id, statement_id, amount, description, category, date, balance

**File:** `backend/app/routes/transactions.py`

- [ ] `GET /api/transactions` endpoint
- [ ] Filter by user_id (from JWT)
- [ ] Optional filters: date range, category
- [ ] Return transactions as JSON

---

### Days 6-7: Integration & Testing

- [ ] End-to-end test: Register → Login → Upload PDF → View Transactions
- [ ] Fix bugs
- [ ] Refine PDF parser accuracy
- [ ] Add error handling
- [ ] Update API documentation
- [ ] Code cleanup

---

## 🎯 Week 1 Success Criteria

By end of Week 1 (Dec 14), you should be able to:

1. ✅ **Create user account**
```bash
   POST /api/auth/register
   {
     "email": "diego@example.com",
     "password": "secure123",
     "full_name": "Diego"
   }
```

2. ✅ **Login and get JWT token**
```bash
   POST /api/auth/login
   {
     "email": "diego@example.com",
     "password": "secure123"
   }
   # Returns: {"access_token": "eyJ...", "token_type": "bearer"}
```

3. ✅ **Upload BBVA PDF**
```bash
   POST /api/statements/upload
   Headers: Authorization: Bearer eyJ...
   Body: [PDF file]
```

4. ✅ **View extracted transactions**
```bash
   GET /api/transactions
   Headers: Authorization: Bearer eyJ...
   # Returns: [{id, amount, description, date, ...}, ...]
```

**Deliverable:** Working API that parses BBVA statements and stores transactions.

---

## 📊 Database Schema (To Implement)

### Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  hashed_password VARCHAR NOT NULL,
  full_name VARCHAR,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Statements Table
```sql
CREATE TABLE statements (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  bank_name VARCHAR,
  statement_month DATE,
  file_name VARCHAR,
  parsing_status VARCHAR, -- 'pending', 'success', 'failed'
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Transactions Table
```sql
CREATE TABLE transactions (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  statement_id UUID REFERENCES statements(id),
  amount DECIMAL(10,2),
  description VARCHAR,
  category VARCHAR,
  transaction_date DATE,
  running_balance DECIMAL(10,2),
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Budgets Table (Week 3)
```sql
CREATE TABLE budgets (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  category VARCHAR,
  monthly_limit DECIMAL(10,2),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🐛 Known Issues & Quirks

### VS Code Python Interpreter
- VS Code sometimes doesn't auto-detect venv
- Bottom-right interpreter selector may show wrong Python
- **Workaround:** Always verify `(venv)` in terminal before working

### Conda vs Venv
- System has both Conda (base) and venv active
- Terminal shows `(venv) (base)` - this is normal
- Make sure commands use venv Python: `/Users/diegoferra/Documents/ASTRAFIN/PROJECT/backend/venv/bin/python`

---

## 💡 Key Learnings (For DS/DE Background)

### FastAPI Concepts Explained
- **FastAPI app** = Like SparkSession in PySpark (main entry point)
- **Endpoints (@app.get)** = Functions that respond to HTTP requests
- **HTTP Methods** = CRUD operations (GET=SELECT, POST=INSERT, PUT=UPDATE, DELETE=DELETE)
- **Middleware** = Pre-processing layer (like decorators or transformers)
- **Pydantic schemas** = Data validation (like dataclass but for APIs)
- **SQLAlchemy ORM** = Like pandas but for databases (DataFrame → SQL tables)

### Why FastAPI over Flask
- Auto-generates API documentation (Swagger/ReDoc)
- Built-in data validation (Pydantic)
- Async/await support (better performance)
- Type hints everywhere (better IDE support)

---

## 📝 Important Commands Reference

### Virtual Environment
```bash
# Activate venv
source venv/bin/activate

# Deactivate venv
deactivate

# Check which Python is active
which python
```

### Server Management
```bash
# Start development server
uvicorn app.main:app --reload

# Start on different port
uvicorn app.main:app --reload --port 8080

# Stop server
Ctrl+C
```

### Dependencies
```bash
# Install new package
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt

# Install from requirements.txt
pip install -r requirements.txt
```

### Database (Future)
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 🎓 Resources for Tomorrow

### Supabase
- Dashboard: https://supabase.com/dashboard
- Docs: https://supabase.com/docs
- Connection string format: `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`

### FastAPI Docs
- Official: https://fastapi.tiangolo.com
- Database tutorial: https://fastapi.tiangolo.com/tutorial/sql-databases/
- Security: https://fastapi.tiangolo.com/tutorial/security/

### SQLAlchemy
- ORM tutorial: https://docs.sqlalchemy.org/en/20/tutorial/
- Models: https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html

### JWT Authentication
- python-jose docs: https://python-jose.readthedocs.io/
- JWT debugger: https://jwt.io

---

## 🚨 Tomorrow's Checklist

Before starting:
- [ ] Read this entire document
- [ ] Open project in VS Code
- [ ] Activate venv: `source venv/bin/activate`
- [ ] Verify server still works: `uvicorn app.main:app --reload`
- [ ] Visit http://localhost:8000/docs to confirm
- [ ] Have Supabase tab open
- [ ] Have FastAPI docs open

Start with:
1. **Supabase account creation** (15 min)
2. **Database connection** (30 min)
3. **First model - User** (45 min)

---

## 💪 Motivation

**You've completed:** 
- ✅ Development environment setup (hardest part for beginners)
- ✅ Project structure (professional-grade)
- ✅ First working API
- ✅ Understanding of FastAPI fundamentals

**What's left:** 
- 🎯 7 more days of Week 1
- 🎯 Database + Auth (Day 2-3)
- 🎯 PDF parsing (Day 4-5)
- 🎯 Integration (Day 6-7)

**You're 14% done with Week 1. Keep going!** 🚀

---

**Last Updated:** December 13, 2025 01:50 AM
**Status:** Ready for Day 2
**Next Session:** Database setup with Supabase