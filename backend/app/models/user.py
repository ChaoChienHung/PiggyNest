from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    """
    SQLAlchemy Model representing an authenticated user.
    
    Attributes:
        id (int): Primary key.
        username (str): The chosen display name for the user.
        email (str): The user's secure contact email.
        hashed_password (str): Bcrypt encrypted password payload.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
