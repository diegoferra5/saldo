# FinTwin Project Structure Guide

**Purpose**: This document explains every folder and file in the AstraFin project.  
**Audience**: Future you, collaborators, or anyone maintaining this codebase.  
**Last Updated**: December 13, 2025

---

## 🏗️ High-Level Overview
```
ASTRAFIN/PROJECT/
├── backend/          # Server-side application (FastAPI + Python)
├── frontend/         # Client-side application (Next.js + React) [Week 2+]
├── docs/             # Project documentation
├── .gitignore        # Files Git should ignore
└── README.md         # Project overview & quick start
```

---

## 📂 Backend Structure (Detailed)

### Root Level Files

| File | Purpose | Example Content |
|------|---------|-----------------|
| `requirements.txt` | Python dependencies list | `fastapi==0.104.1` |
| `.env` | **SECRET** environment variables | Database passwords, API keys |
| `.env.example` | Template for `.env` (safe to commit) | `DATABASE_URL=postgresql://...` |
| `README.md` | Backend-specific documentation | Setup instructions, API docs |

**🔒 Security Note**: `.env` contains secrets and is in `.gitignore`. Never commit it to Git!

---

### `backend/app/` - Main Application Code

This is where your FastAPI application lives.

#### `app/main.py` - 🚀 Application Entry Point

**What it does**: 
- Creates the FastAPI app instance
- Registers all route blueprints (auth, transactions, etc.)
- Configures middleware (CORS, security headers)
- Defines startup/shutdown events (database connections)

**Example code structure**:
```python
from fastapi import FastAPI
from app.routes import auth, transactions

app = FastAPI(title="AstraFin API")

app.include_router(auth.router)
app.include_router(transactions.router)

@app.get("/")
def root():
    return {"message": "AstraFin API is running"}
```

**When you modify it**: 
- Adding new route modules
- Changing API metadata (title, description)
- Adding global middleware

---

### `app/core/` - Core Configuration

**Purpose**: Application-wide settings and utilities that other modules depend on.

#### `core/config.py` - ⚙️ Settings & Environment Variables

**What it does**:
- Loads environment variables from `.env`
- Defines app configuration (database URL, secret keys)
- Provides typed settings using Pydantic

**Example**:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**When you modify it**: 
- Adding new environment variables
- Changing default values

---

#### `core/security.py` - 🔐 Authentication & Security

**What it does**:
- Password hashing (bcrypt)
- JWT token creation and validation
- Password verification
- Token decoding

**Example functions**:
```python
def hash_password(password: str) -> str:
    """Convert plain password to bcrypt hash"""
    
def verify_password(plain: str, hashed: str) -> bool:
    """Check if password matches hash"""
    
def create_access_token(user_id: str) -> str:
    """Generate JWT token for authenticated user"""
```

**When you modify it**: 
- Changing token expiration time
- Adding refresh token logic
- Implementing 2FA

---

#### `core/database.py` - 🗄️ Database Connection

**What it does**:
- Creates SQLAlchemy engine (connection to PostgreSQL)
- Defines SessionLocal (database session factory)
- Provides `get_db()` dependency for routes

**Example**:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """Dependency that provides database session to routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**When you modify it**: 
- Adding connection pooling settings
- Configuring database timeouts

---

### `app/models/` - 📊 Database Tables (SQLAlchemy ORM)

**Purpose**: Define what your database tables look like in Python code.

#### `models/user.py` - User Table

**What it does**: Defines the `users` table structure.

**Example**:
```python
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    created_at = Column(DateTime)
```

**Database equivalent**:
```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    full_name VARCHAR,
    created_at TIMESTAMP
);
```

**When you modify it**: 
- Adding new user fields (phone, avatar_url)
- Changing field types

---

#### `models/transaction.py` - Transaction Table

**What it does**: Stores individual bank transactions.

**Key fields**:
- `amount`: Transaction value (negative = expense, positive = income)
- `description`: Merchant name (e.g., "STARBUCKS COFFEE")
- `category`: Auto-assigned category (e.g., "Eating Out")
- `transaction_date`: When transaction occurred
- `user_id`: Foreign key to `users` table

**When you modify it**: 
- Adding receipt_url field
- Adding tags or notes

---

#### `models/statement.py` - Statement Upload Metadata

**What it does**: Tracks uploaded PDF bank statements.

**Key fields**:
- `bank_name`: "BBVA", "Santander", etc.
- `statement_month`: Month this statement covers
- `parsing_status`: "pending", "success", "failed"
- `file_name`: Original uploaded filename

**Why separate from transactions**: 
- One statement → many transactions
- Track parsing failures
- Allow re-parsing if needed

---

#### `models/budget.py` - User Budget Limits

**What it does**: Stores user-defined spending limits per category.

**Example**:
```python
class Budget(Base):
    __tablename__ = "budgets"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    category = Column(String)  # "Eating Out"
    monthly_limit = Column(Numeric(10, 2))  # 500.00
    is_active = Column(Boolean, default=True)
```

---

### `app/schemas/` - 📝 Data Validation (Pydantic)

**Purpose**: Define what data your API accepts and returns.

**Key Difference from Models**:
- **Models** = Database structure (SQLAlchemy)
- **Schemas** = API input/output validation (Pydantic)

#### `schemas/user.py` - User API Schemas

**Example**:
```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    """Data required to create a user"""
    email: EmailStr
    password: str
    full_name: str

class UserResponse(BaseModel):
    """Data returned when fetching a user (no password!)"""
    id: str
    email: str
    full_name: str
    created_at: datetime
```

**Why this matters**:
- Input validation: FastAPI rejects invalid emails automatically
- Security: Never return passwords in API responses
- Documentation: Auto-generates OpenAPI docs

---

#### `schemas/auth.py` - Authentication Schemas

**Example**:
```python
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

---

#### `schemas/transaction.py` - Transaction Schemas

**Example**:
```python
class TransactionResponse(BaseModel):
    id: str
    amount: float
    description: str
    category: str
    transaction_date: date
    
    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy model
```

---

### `app/routes/` - 🛣️ API Endpoints (FastAPI Routers)

**Purpose**: Define HTTP endpoints (URLs) that clients can call.

#### `routes/auth.py` - Authentication Endpoints

**Endpoints**:
```python
POST /api/auth/register  # Create new user account
POST /api/auth/login     # Get JWT token
GET  /api/auth/me        # Get current user info
```

**Example code**:
```python
from fastapi import APIRouter, Depends
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import authenticate_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, credentials.email, credentials.password)
    token = create_access_token(user.id)
    return {"access_token": token}
```

**When you modify it**: 
- Adding password reset
- Adding OAuth (Google login)

---

#### `routes/statements.py` - Statement Upload

**Endpoints**:
```python
POST /api/statements/upload  # Upload PDF bank statement
GET  /api/statements         # List user's uploaded statements
GET  /api/statements/{id}    # Get specific statement details
```

**Example**:
```python
@router.post("/upload")
async def upload_statement(
    file: UploadFile,
    bank: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Save file temporarily
    # Parse PDF
    # Store transactions
    # Return results
```

---

#### `routes/transactions.py` - Transaction Queries

**Endpoints**:
```python
GET /api/transactions              # List all user transactions
GET /api/transactions/{id}         # Get single transaction
PUT /api/transactions/{id}         # Update transaction (change category)
DELETE /api/transactions/{id}      # Delete transaction
```

---

#### `routes/budgets.py` - Budget Management

**Endpoints** (Week 3):
```python
POST   /api/budgets       # Create budget
GET    /api/budgets       # List budgets
PUT    /api/budgets/{id}  # Update budget
DELETE /api/budgets/{id}  # Delete budget
```

---

### `app/services/` - 🧠 Business Logic

**Purpose**: Complex operations that routes delegate to. Keeps routes clean.

**Analogy**: 
- Routes = Cashier (takes orders)
- Services = Chef (does the actual work)

#### `services/auth_service.py` - Authentication Logic

**Functions**:
```python
def register_user(db, email, password, full_name):
    """
    1. Check if email already exists
    2. Hash password
    3. Create user in database
    4. Return user object
    """

def authenticate_user(db, email, password):
    """
    1. Find user by email
    2. Verify password matches hash
    3. Return user if valid, raise error if not
    """
```

**Why separate from routes**: 
- Reusable (can call from multiple routes)
- Testable (test without HTTP)
- Clean separation of concerns

---

#### `services/parser_service.py` - PDF Parsing Orchestration

**Functions**:
```python
def parse_statement(file_path: str, bank: str):
    """
    1. Detect bank type
    2. Call appropriate parser (BBVA, Santander, etc.)
    3. Validate extracted transactions
    4. Return list of transactions
    """

def save_parsed_transactions(db, user_id, transactions):
    """
    1. Categorize each transaction
    2. Insert into database
    3. Update statement status
    """
```

---

#### `services/transaction_service.py` - Transaction CRUD

**Functions**:
```python
def get_user_transactions(db, user_id, filters):
    """Query transactions with optional filters (date range, category)"""

def update_transaction_category(db, transaction_id, new_category):
    """Allow user to correct auto-categorization"""

def calculate_spending_by_category(db, user_id, month):
    """Aggregate spending for budget tracking"""
```

---

#### `services/categorization.py` - Auto-Categorization

**What it does**: Assigns categories to transactions based on description.

**Example**:
```python
PATTERNS = {
    "Eating Out": ["STARBUCKS", "MCDONALDS", "RESTAURANTE"],
    "Groceries": ["WALMART", "SORIANA", "CHEDRAUI"],
    "Transport": ["UBER", "GASOLINA", "PEMEX"]
}

def categorize(description: str) -> str:
    for category, keywords in PATTERNS.items():
        if any(kw in description.upper() for kw in keywords):
            return category
    return "Other"
```

---

### `app/utils/` - 🔧 Utility Helpers

**Purpose**: Small, reusable functions that don't fit elsewhere.

#### `utils/pdf_parser.py` - BBVA PDF Extraction

**What it does**: Low-level PDF text extraction for BBVA statements.

**Example**:
```python
import pdfplumber

def extract_bbva_transactions(pdf_path: str):
    """
    1. Open PDF with pdfplumber
    2. Find transaction table
    3. Extract date, description, amount, balance
    4. Return list of dicts
    """
    transactions = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            # Parse table rows...
    return transactions
```

---

#### `utils/validators.py` - Custom Validation

**Example**:
```python
def is_valid_mexican_date(date_str: str) -> bool:
    """Validate DD/MM/YYYY format"""
    
def sanitize_amount(amount_str: str) -> float:
    """Convert '$1,234.56' to 1234.56"""
```

---

### `backend/tests/` - 🧪 Automated Tests

**Purpose**: Verify code works correctly and catch bugs early.

#### `tests/test_auth.py` - Authentication Tests

**Example**:
```python
def test_register_user():
    """Test user registration endpoint"""
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "secure123",
        "full_name": "Test User"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

---

#### `tests/test_parser.py` - PDF Parser Tests

**Example**:
```python
def test_bbva_parser():
    """Test BBVA PDF extraction"""
    transactions = parse_bbva_statement("test_statement.pdf")
    assert len(transactions) > 0
    assert transactions[0]["amount"] < 0  # Expense
```

---

### `backend/uploads/` - 📁 Temporary File Storage

**Purpose**: Store uploaded PDFs temporarily before parsing.

**Security**:
- Files deleted after 24 hours (Week 4 task)
- Not committed to Git (in `.gitignore`)
- Only accessible to authenticated users

**`.gitkeep`**: Empty file that forces Git to track the folder structure.

---

## 📋 Frontend Structure (Week 2+)
```
frontend/
├── src/
│   ├── app/              # Next.js 13+ app directory
│   ├── components/       # Reusable UI components
│   ├── lib/              # API clients, utilities
│   └── styles/           # CSS/Tailwind
├── public/               # Static assets (images, icons)
└── package.json          # JavaScript dependencies
```

---

## 🗂️ Docs Folder

| File | Purpose |
|------|---------|
| `PROJECT_STRUCTURE.md` | This file! Structure documentation |
| `API_DOCUMENTATION.md` | API endpoint reference (Week 2) |
| `DEPLOYMENT_GUIDE.md` | How to deploy to Railway (Week 4) |
| `USER_GUIDE.md` | End-user instructions (Week 5) |

---

## 🚫 .gitignore - What Git Ignores

**Categories**:
- **Secrets**: `.env`, API keys
- **Dependencies**: `venv/`, `node_modules/`
- **Build artifacts**: `__pycache__/`, `dist/`
- **User uploads**: `uploads/*` (except `.gitkeep`)
- **OS files**: `.DS_Store`, `Thumbs.db`

**Why this matters**: Prevents committing 5GB of dependencies or leaking passwords.

---

## 📖 README.md Files

### Root `README.md`
- Project overview
- Quick start guide
- Links to detailed docs

### `backend/README.md`
- Backend-specific setup
- API documentation link
- Development workflow

---

## 🎯 File Naming Conventions

| Pattern | Meaning | Example |
|---------|---------|---------|
| `snake_case.py` | Python files | `auth_service.py` |
| `PascalCase` | Classes | `class User(Base)` |
| `SCREAMING_CASE` | Constants | `SECRET_KEY` |
| `__init__.py` | Package marker | Makes folder a Python package |

---

## 🔄 Data Flow Example

**User uploads BBVA statement**:
```
1. User → POST /api/statements/upload (routes/statements.py)
2. Route → Save file to uploads/ folder
3. Route → Call parser_service.parse_statement()
4. Service → Call utils/pdf_parser.extract_bbva_transactions()
5. Utils → Extract transactions from PDF
6. Service → Call categorization.categorize() for each transaction
7. Service → Save to database via models/transaction.py
8. Route → Return success response to user
```

---

## 🆘 Quick Reference

**"Where do I put..."**

| Task | Location |
|------|----------|
| New API endpoint | `app/routes/` |
| Database table | `app/models/` |
| Business logic | `app/services/` |
| Input validation | `app/schemas/` |
| Helper function | `app/utils/` |
| Configuration | `app/core/config.py` |
| Security code | `app/core/security.py` |
| Tests | `backend/tests/` |

---

## 📚 Learning Resources

**Concepts to understand**:
- **MVC Pattern**: Models (data) → Services (logic) → Routes (presentation)
- **Dependency Injection**: FastAPI's `Depends()` for database sessions, auth
- **ORM**: SQLAlchemy translates Python ↔ SQL
- **Pydantic**: Validates data automatically

**Recommended reading**:
- FastAPI docs: https://fastapi.tiangolo.com
- SQLAlchemy docs: https://docs.sqlalchemy.org
- Clean Architecture: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html

---

**Last Updated**: December 13, 2025  
**Maintained By**: Diego (AstraFin Developer)  
**Questions?**: Add them to this doc as you learn!