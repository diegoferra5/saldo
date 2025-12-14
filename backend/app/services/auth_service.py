from sqlalchemy.orm import Session
from typing import Optional

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get user by email.
    
    Args:
        db: Database session
        email: User's email
        
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session
        user: UserCreate schema with user data
        
    Returns:
        Created User object
    """
    # Hash the password
    hashed_password = get_password_hash(user.password)
    
    # Create user object
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    
    # Add to database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)  # Refresh to get generated fields (id, created_at)
    
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.
    
    Args:
        db: Database session
        email: User's email
        password: Plain text password
        
    Returns:
        User object if credentials are valid, None otherwise
    """
    # Get user from database
    user = get_user_by_email(db, email)
    
    if not user:
        return None  # User doesn't exist
    
    # Verify password
    if not verify_password(password, user.hashed_password):
        return None  # Wrong password
    
    return user