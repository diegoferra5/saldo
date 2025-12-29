from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create database engine with Supabase-specific settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=300,    # Recycle connections after 5 minutes
    pool_size=5,         # Max pool size
    max_overflow=10,     # Max overflow connections
    echo=False,          # Don't log SQL queries
    connect_args={
        "sslmode": "require",       # Force SSL for Supabase
        "connect_timeout": 10,      # Timeout after 10 seconds
    },
)

# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()


# Dependency for FastAPI routes
def get_db():
    """
    Dependency that provides a database session.
    Automatically closes session after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()