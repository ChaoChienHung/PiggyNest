from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    piggy_bank_id = Column(Integer, ForeignKey("piggy_banks.id"), nullable=False)
    
    amount = Column(Float, nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(String(255), nullable=True)
    
    date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    piggy_bank = relationship("PiggyBank", back_populates="transactions")
