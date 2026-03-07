from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Transaction(Base):
    """
    SQLAlchemy Model representing a financial transaction (income, expense, transfer).
    
    Attributes:
        id (int): Primary key.
        piggy_bank_id (int): Foreign key linking to the associated PiggyBank.
        amount (float): The absolute monetary value of the transaction.
        type (str): The transaction classification (e.g., 'expense', 'income', 'transfer').
        category (str): Optional categorical string tag.
        description (str): Optional user-provided context notes.
        date (DateTime): The user-defined or default real-world date of the transaction.
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    piggy_bank_id = Column(Integer, ForeignKey("piggy_banks.id"), nullable=False)
    
    amount = Column(Float, nullable=False)
    type = Column(String(50), nullable=False, default='expense')
    category = Column(String(100), nullable=True)
    description = Column(String(255), nullable=True)
    
    date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    piggy_bank = relationship("PiggyBank", back_populates="transactions")
