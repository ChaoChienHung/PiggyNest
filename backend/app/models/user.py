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
    token_version = Column(Integer, nullable=False, default=0, server_default="0")
    # Display preference: transactions shown per page in a PiggyBank; 0 means all.
    transactions_per_page = Column(Integer, nullable=False, default=20, server_default="20")
    # Display and input format for dates in every client; the API always uses ISO 8601.
    date_format = Column(String(10), nullable=False, default="YYYY-MM-DD", server_default="YYYY-MM-DD")
    display_currency = Column(String(10), nullable=False, default="NTD", server_default="NTD")
    net_worth_hidden = Column(Boolean, nullable=False, default=False, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
