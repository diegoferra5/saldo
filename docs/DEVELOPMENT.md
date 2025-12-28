# Saldo - Development Guide

**Last Updated:** December 28, 2025

---

## Quick Start

```bash
# 1. Clone and navigate
cd /Users/diegoferra/Documents/ASTRAFIN/PROJECT/backend

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run backend server
uvicorn app.main:app --reload

# Server runs at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

---

## Environment Setup

### Prerequisites

- **Python:** 3.11.14 (required - using Python 3.11 features)
- **PostgreSQL:** Supabase hosted database
- **Git:** For version control

### Initial Setup

```bash
# 1. Create virtual environment (first time only)
cd backend
python3.11 -m venv venv

# 2. Activate virtual environment
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your actual values (see below)

# 5. Verify installation
python -c "import fastapi; print(fastapi.__version__)"
# Should print: 0.104.1
```

---

## Environment Variables

Create `backend/.env` with the following:

```bash
# Database (Supabase)
DATABASE_URL=postgresql://user:password@host:port/database

# Security
SECRET_KEY=your-secret-key-here-minimum-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# Application
DEBUG=False
ENVIRONMENT=development  # development | staging | production

# File Upload
MAX_UPLOAD_SIZE_MB=10
UPLOAD_DIR=/tmp/statements
```

**Security Notes:**
- ❌ NEVER commit `.env` to git (already in `.gitignore`)
- ✅ Use `.env.example` as a template (safe to commit)
- ✅ Rotate `SECRET_KEY` in production
- ✅ Use Supabase connection string from project settings

---

## Running the Backend

### Development Server (with auto-reload)

```bash
# From /backend/ directory
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Server starts at: http://localhost:8000
# API documentation: http://localhost:8000/docs (Swagger UI)
# Alternative docs: http://localhost:8000/redoc
```

**Auto-reload:** Server restarts automatically when you edit Python files.

### Production Server (no reload)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Running the PDF Parser (CLI)

The parser can be run standalone for testing:

### Normal Mode (minimal output)

```bash
python backend/app/utils/pdf_parser.py
```

**Output:**
```
Transactions: 34
Warnings: 0
Starting balance: 11028.46
Deposits: 47856.22
Charges: 56862.50
Final balance: 2022.18
```

### Debug Mode (verbose output)

```bash
python backend/app/utils/pdf_parser.py --debug
```

**Output:** Same as above, PLUS detailed classification logs.

### Custom PDF

```bash
python backend/app/utils/pdf_parser.py /path/to/statement.pdf
python backend/app/utils/pdf_parser.py /path/to/statement.pdf --debug
```

**More details:** See `docs/PDF_PARSER.md`

---

## Database Connection

### Using Supabase

1. Go to https://supabase.com/dashboard
2. Select your project
3. Navigate to: Settings → Database → Connection String
4. Copy the PostgreSQL connection string
5. Paste into `backend/.env` as `DATABASE_URL`

**Format:**
```
postgresql://postgres.[project-ref]:[password]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### Test Connection

```python
# In Python REPL
from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print(result.scalar())  # Should print: 1
```

---

## Project Structure

```
backend/
├── app/
│   ├── core/              # Configuration, database, security
│   │   ├── config.py      # Environment variables
│   │   ├── database.py    # SQLAlchemy setup
│   │   └── security.py    # JWT + bcrypt
│   ├── models/            # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── account.py
│   │   ├── statement.py
│   │   └── transaction.py
│   ├── schemas/           # Pydantic validation schemas
│   │   ├── user.py
│   │   ├── account.py
│   │   ├── statement.py
│   │   └── transactions.py
│   ├── routes/            # FastAPI endpoints
│   │   ├── auth.py
│   │   ├── statements.py
│   │   ├── transactions.py
│   │   └── accounts.py
│   ├── services/          # Business logic
│   │   ├── auth_service.py
│   │   ├── statement_service.py
│   │   ├── transaction_service.py
│   │   └── account_service.py
│   ├── utils/             # Helper functions
│   │   ├── pdf_parser.py
│   │   ├── date_helpers.py
│   │   └── hash_helpers.py
│   └── main.py            # FastAPI app entry point
├── tests/                 # Automated tests
├── venv/                  # Virtual environment (not in git)
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in git)
└── .env.example           # Template (safe to commit)
```

---

## Development Workflow

### Adding a New Feature

**Example:** Add budget tracking

```bash
# 1. Create database migration (if needed)
# Via Supabase UI or SQL script

# 2. Create ORM model
touch backend/app/models/budget.py

# 3. Create Pydantic schemas
touch backend/app/schemas/budget.py

# 4. Create service layer
touch backend/app/services/budget_service.py

# 5. Create API endpoints
touch backend/app/routes/budgets.py

# 6. Register router in main.py
# app.include_router(budgets.router, prefix="/api/budgets", tags=["budgets"])

# 7. Test manually via Swagger UI
# http://localhost:8000/docs

# 8. Write automated tests
touch backend/tests/test_budget.py
```

### Making Changes to Existing Code

```bash
# 1. Read the relevant docs first
cat docs/ARCHITECTURE.md
cat docs/PDF_PARSER.md

# 2. Make your changes
# Edit files in backend/app/

# 3. Test immediately
# Use Swagger UI or write a test

# 4. Verify no regressions
python -m pytest

# 5. Commit
git add .
git commit -m "feat: add budget tracking"
```

---

## Testing

### Manual Testing (Swagger UI)

```bash
# 1. Start server
uvicorn app.main:app --reload

# 2. Open browser
# http://localhost:8000/docs

# 3. Try endpoints
# - POST /api/auth/register (create test user)
# - POST /api/auth/login (get JWT token)
# - Use "Authorize" button (top right) to add token
# - POST /api/statements/upload (upload test PDF)
# - GET /api/transactions (verify transactions)
```

### Automated Testing (pytest)

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_parser.py

# Run with verbose output
python -m pytest -v

# Run with coverage
python -m pytest --cov=app
```

### Test PDF Files

**Location:** `/Users/diegoferra/Documents/ASTRAFIN/STATEMENTS/`

**Smoke Test PDF:**
- `BBVA_debit_dic25_diego.pdf` (34 transactions, 85% accuracy)

---

## Common Tasks

### Update Dependencies

```bash
# Add new package
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt

# Or manually edit requirements.txt and run:
pip install -r requirements.txt
```

### Database Migrations

**Using Supabase UI:**
1. Go to SQL Editor in Supabase dashboard
2. Write migration SQL
3. Execute

**Example - Add column:**
```sql
ALTER TABLE transactions
ADD COLUMN beneficiary VARCHAR(255);
```

### View Logs

```bash
# Backend logs (when running uvicorn)
# Logs appear in terminal

# Or redirect to file:
uvicorn app.main:app --log-config logging.conf > logs/app.log 2>&1
```

### Clear Upload Directory

```bash
# Remove all uploaded PDFs (development only)
rm -rf /tmp/statements/*

# In production, implement a cleanup job
```

---

## Debugging

### Enable Debug Mode

```python
# In app/core/config.py
class Settings(BaseSettings):
    DEBUG: bool = True  # Change to True

# Or in .env
DEBUG=True
```

### Print Debugging

```python
# Quick debugging (remove before commit)
print(f"DEBUG: {variable}")

# Better: Use logging
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Variable value: {variable}")
```

### Interactive Debugging (pdb)

```python
# Add breakpoint
import pdb; pdb.set_trace()

# When execution hits this line, you get an interactive shell
# Commands: n (next), c (continue), p variable (print), q (quit)
```

### Database Queries

```python
# Print SQL queries
from sqlalchemy import create_engine

engine = create_engine(DATABASE_URL, echo=True)
# Now all SQL queries are printed
```

---

## Code Style

### Formatting

```bash
# Install black (Python formatter)
pip install black

# Format all files
black backend/app/

# Check without changing
black --check backend/app/
```

### Linting

```bash
# Install flake8 (Python linter)
pip install flake8

# Run linter
flake8 backend/app/

# Or use VS Code with Python extension (auto-lints)
```

### Type Hints

```python
# Use type hints for better IDE support
def get_user(user_id: UUID) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"

**Solution:** Make sure you're in the correct directory and venv is activated:
```bash
cd /Users/diegoferra/Documents/ASTRAFIN/PROJECT/backend
source venv/bin/activate
```

### "Could not connect to database"

**Solution:** Check `DATABASE_URL` in `.env`:
```bash
# Print current value (without password)
python -c "from app.core.config import settings; print(settings.DATABASE_URL.split('@')[1])"

# Test connection
python -c "from app.core.database import engine; engine.connect()"
```

### "JWT token validation fails"

**Solution:** Make sure `SECRET_KEY` is the same as when token was created:
```bash
# Generate new secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### "File upload fails"

**Solution:** Check upload directory exists and has write permissions:
```bash
mkdir -p /tmp/statements
chmod 755 /tmp/statements
```

### "Parser returns 0 transactions"

**Solution:** See `docs/PDF_PARSER.md` troubleshooting section.

---

## Useful Commands

```bash
# Check Python version
python --version

# Check installed packages
pip list

# Find package location
pip show fastapi

# Activate venv (if not already)
source venv/bin/activate

# Deactivate venv
deactivate

# Start server (short version)
uvicorn app.main:app --reload

# Check server health
curl http://localhost:8000/health

# Format code
black backend/app/

# Run tests
pytest

# Run parser CLI
python backend/app/utils/pdf_parser.py --debug
```

---

## Git Workflow

```bash
# Check current branch
git branch

# Create feature branch
git checkout -b feature/budget-tracking

# Make changes, then:
git add .
git commit -m "feat: add budget tracking endpoints"

# Push to remote
git push origin feature/budget-tracking

# Merge to main (after review)
git checkout main
git merge feature/budget-tracking
```

---

## Next Steps

- **API Documentation:** http://localhost:8000/docs
- **System Architecture:** `docs/ARCHITECTURE.md`
- **Parser Details:** `docs/PDF_PARSER.md`

---

**Questions?** Check existing documentation or add notes to this file!
