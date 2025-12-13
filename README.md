# 💰 Saldo

> Personal finance control for Mexico - In development

Saldo is an application that helps Mexicans manage their personal finances through automatic analysis of bank statements.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python)](https://www.python.org)
[![Status](https://img.shields.io/badge/Status-In%20Development-yellow)](https://github.com/diegoferra5/saldo)

---

## 🎯 What is Saldo?

A personal finance app that:
- 📄 **Analyzes PDF bank statements** from Mexican banks (BBVA, Santander, Banorte)
- 🤖 **Automatically categorizes transactions** (food, transport, entertainment)
- 📊 **Tracks budgets** by category
- 💬 **Provides financial advice** with AI (GPT-4)

**Why?** Most finance apps are designed for USA/Europe. Saldo is built for the Mexican banking ecosystem.

---

## 🚀 Current Status

**Phase:** MVP Backend - Week 1 (14% complete)

**Completed:**
- ✅ Project structure
- ✅ FastAPI configured
- ✅ Basic API running
- ✅ Auto-generated documentation

**In Progress:**
- 🔄 Database (PostgreSQL/Supabase)
- 🔄 Authentication system (JWT)
- 🔄 BBVA PDF parser
- 🔄 Transaction endpoints

**Coming Soon:**
- 📋 Frontend (Next.js)
- 📋 Smart categorization
- 📋 Budget dashboard
- 📋 Mobile app

---

## 🛠️ Tech Stack

**Backend:**
- FastAPI (Python 3.11)
- PostgreSQL (Supabase)
- SQLAlchemy
- JWT Authentication
- pdfplumber (PDF extraction)
- OpenAI GPT-4 (financial advice)

**Frontend** *(planned)*:
- Next.js + React
- Tailwind CSS

---

## 💻 Quick Start
```bash
# Clone
git clone https://github.com/diegoferra5/saldo.git
cd saldo/backend

# Setup
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run
uvicorn app.main:app --reload
```

API available at: http://localhost:8000  
Documentation: http://localhost:8000/docs

---

## 📁 Project Structure
```
saldo/
├── backend/
│   ├── app/
│   │   ├── main.py          # API entry point
│   │   ├── core/            # Config, DB, Auth
│   │   ├── models/          # Database models
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   └── utils/           # PDF parser, helpers
│   └── requirements.txt
├── frontend/                 # (TODO)
└── docs/
```

---

## 🎯 Roadmap

### MVP (8 weeks - Feb 2026)
1. **Weeks 1-4:** Backend API
   - User authentication
   - Bank statement parser (BBVA)
   - Transaction & budget CRUD
   - GPT-4 integration

2. **Weeks 5-6:** Frontend
   - Transaction dashboard
   - Budget management
   - AI chat interface

3. **Weeks 7-8:** Beta Launch
   - Testing with 50 real users
   - Production deployment
   - Feedback & iteration

### Post-MVP
- Multi-bank support (Santander, Banorte, etc.)
- Mobile app (React Native)
- Real-time banking API (Belvo)
- Shared budgets
- Savings goals

---

## 🏦 Target Banks

| Bank | Status |
|------|--------|
| BBVA México | 🎯 Priority 1 |
| Santander | 📋 Planned |
| Banorte | 📋 Planned |
| HSBC | 📋 Planned |
| Banamex | 📋 Future |

---

## 👨‍💻 Author

**Diego Ferra**  
Data Engineer/Scientist 

[ferradiego5@gmail.com] • [www.linkedin.com/in/diego-ferra-b7b6082bb] 

---

## 📝 Notes

- This is a personal project in active development
- Not professional financial advice
- Designed specifically for the Mexican market
- Open source under MIT license

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

<div align="center">

**Status:** 🚧 Under active construction  
**Last updated:** December 2025

</div>