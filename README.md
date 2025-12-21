# 💰 Saldo

> Personal finance control for Mexico — **MVP in development**

**Saldo** is a personal finance web application built for the **Mexican banking ecosystem**.  
It helps users understand, organize, and improve their finances by **automatically analyzing bank statements**.

Built with a **backend-first MVP approach**, focused on correctness, performance, and real-world constraints.

---

## 🎯 What is Saldo?

Saldo allows users to:

- 📄 **Upload bank statements (PDF)** from Mexican banks (BBVA, Santander, Banorte)
- 🧠 **Automatically parse and classify transactions**
- 📊 **Track spending and budgets by category**
- 🤖 **Receive financial insights via AI (LLM-powered)**

**Why Saldo?**  
Most personal finance tools are built for the US or Europe. Mexican users face:
- different bank formats
- limited API availability
- poor local support

Saldo is designed **specifically for Mexico**, starting with real bank PDFs.

---
## 🚀 Current Status

**Phase:** MVP Backend — Week 1  
**Progress:** Models & DB architecture completed ✅

### Completed
- ✅ Project structure
- ✅ FastAPI setup
- ✅ PostgreSQL schema (Supabase)
- ✅ SQLAlchemy models (mapping-only)
- ✅ BBVA PDF parser (≈85% accuracy on modern statements)

### In Progress
- 🔄 Pydantic schemas
- 🔄 Authentication (JWT)
- 🔄 Statement upload & parsing endpoints

### Next
- 📋 Frontend MVP (Next.js)
- 📋 Transaction dashboard
- 📋 Budget tracking
- 📋 AI-powered insights

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** (Python 3.11)
- **PostgreSQL** (Supabase)
- **SQLAlchemy** (mapping-only ORM)
- **JWT authentication**
- **pdfplumber** (PDF extraction)
- **LLM integration** (financial insights)

### Frontend *(planned)*
- Next.js
- React
- Tailwind CSS

---

## 🧠 Architectural Principles

- **Database = Source of Truth**
  - Constraints and indexes live in PostgreSQL
  - ORM only maps existing schema
- **Soft delete for financial data**
  - Accounts are never hard-deleted
- **Passive deletes**
  - Database handles cascades
- **Conservative parsing**
  - `UNKNOWN` is preferred over incorrect classification
- **MVP-first**
  - Simple, explicit, extensible

---

## 💻 Quick Start

```bash
# Clone repository
git clone https://github.com/diegoferra5/saldo.git
cd saldo/backend

# Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run API
uvicorn app.main:app --reload
````

* API: [http://localhost:8000](http://localhost:8000)
* Docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📁 Project Structure

```
saldo/
├── app/
│   ├── main.py            # FastAPI entry point
│   ├── core/              # DB, config, security
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── api/               # API routes
│   ├── services/          # Business logic
│   └── parsers/           # Bank PDF parsers
├── tests/                 # (planned)
├── .env
├── requirements.txt
└── README.md
```

---

## 🏦 Supported Banks

| Bank        | Status      |
| ----------- | ----------- |
| BBVA México | ✅ Supported |
| Santander   | 🛠 Planned  |
| Banorte     | 🛠 Planned  |
| HSBC        | 📋 Future   |
| Banamex     | 📋 Future   |

---

## 🗺️ Roadmap

### MVP (8 weeks — Feb 2026)

**Weeks 1–4**

* Backend API
* Authentication
* Statement parsing
* Transaction & budget logic

**Weeks 5–6**

* Frontend MVP
* Dashboard & visualizations
* AI insights UI

**Weeks 7–8**

* Closed beta (50 users)
* Feedback & iteration
* Production deployment

### Post-MVP

* Multi-bank support
* Recurring expense detection
* Personalized ML models
* Mobile app
* Banking API integration (Belvo or similar)

---

## 👨‍💻 Author

**Diego Ferra**
Data Scientist / Engineer

📧 [ferradiego5@gmail.com](mailto:ferradiego5@gmail.com)
🔗 [https://www.linkedin.com/in/diego-ferra-b7b6082bb](https://www.linkedin.com/in/diego-ferra-b7b6082bb)

---

## ⚠️ Disclaimer

* This is an experimental personal finance tool
* Not professional financial advice
* Designed for educational and informational purposes
* Open source under MIT License

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

**Status:** 🚧 Actively under development
**Last updated:** December 2025


