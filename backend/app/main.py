'''
Saldo API - Main application entry point

This file initializes the FastAPI application and defines the root endpoint.
Week 1: Basic setup and health check
'''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth
from app.routes import statements 

app = FastAPI(
    title= "Saldo Api",
    description= "API de Gestión Financiera Personal para México",
    version= "0.1.0",
    docs_url= "/docs",
    redoc_url= "/redoc"
)

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
@app.get("/health")
def health_check():
    """
    Detailed health check
    Future: Check database connection, external services
    """
    return {
        "status": "ok",
        "database": "not connected yet",  # Week 1: We'll add this
        "environment": "development",
        "app": "Saldo"
    }


# This runs when you execute: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)