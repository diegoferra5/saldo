'''
Saldo API - Main application entry point

This file initializes the FastAPI application and defines the root endpoint.
Week 1: Basic setup and health check
'''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.logging_config import setup_logging

from app.routes import auth
from app.routes import statements
from app.routes import transactions
from app.routes import account


setup_logging(level="INFO")
logger = logging.getLogger(__name__)

app = FastAPI(
    title= "Saldo API",
    description= "API de Gestión Financiera Personal para México",
    version= "0.1.0",
    docs_url= "/docs",
    redoc_url= "/redoc"
) # cierre de app = FastAPI(...)

logger.info("FastAPI application initialized")


# Configure CORS (allows frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: ["https://saldo.mx"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(statements.router)
app.include_router(transactions.router)
app.include_router(account.router)

@app.on_event("startup")
def on_startup():
    logger.info("Saldo API startup complete | docs=/docs")


# Root endpoint - Health check
@app.get("/")
def root():
    """
    Health check endpoint
    Returns basic API info
    """
    return {
        "app": "Saldo",
        "message": "Saldo API is running",
        "status": "healthy",
        "version": "0.1.0",
        "tagline": "Tu control financiero personal",
        "docs": "http://localhost:8000/docs"
    }


# Health endpoint (useful for deployment monitoring)
@app.get("/health", tags=["system"])
def health_check():
    """
    Health check that safely verifies database connectivity.
    - Runs SELECT 1
    - Does NOT expose credentials or stack traces
    """
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "connected",
            "app": "Saldo API",
        }

    except Exception as e:
        # Do not leak the error to the client
        logger.warning(f"Health check DB unavailable | error={type(e).__name__}")
        return {
            "status": "degraded",
            "database": "unavailable",
            "app": "Saldo API",
        }
        

# This runs when you execute: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)