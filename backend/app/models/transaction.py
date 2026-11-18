from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.money import from_minor_units, to_minor_units

class Transaction(Base):
    """
    SQLAlchemy Model representing a financial transaction (income, expense, transfer).
    
    Attributes:
        id (int): Primary key.
        piggy_bank_id (int): Foreign key linking to the associated PiggyBank.
        amount_minor (int): The signed monetary value in exact minor units.
        type (str): The transaction classification (e.g., 'expense', 'income', 'transfer').
        category (str): Optional categorical string tag.
        description (str): Optional user-provided context notes.
        date (DateTime): The user-defined or default real-world date of the transaction.
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    piggy_bank_id = Column(Integer, ForeignKey("piggy_banks.id"), nullable=False)
    
    amount_minor = Column(BigInteger, nullable=False)
    type = Column(String(50), nullable=False, default='expense')
    category = Column(String(100), nullable=True)
    description = Column(String(255), nullable=True)
    
    date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Both legs of a transfer share this stable identifier. Ordinary entries are null.
    transfer_group_id = Column(String(36), nullable=True, index=True)

    # Relationships
    piggy_bank = relationship("PiggyBank", back_populates="transactions")

    @property
    def amount(self):
        return from_minor_units(self.amount_minor)

    @amount.setter
    def amount(self, value):
        self.amount_minor = to_minor_units(value)

    @property
    def transaction_id(self):
        """One logical ID for both transfer legs; a unique ID for other entries."""
        return self.transfer_group_id or f"entry:{self.id}"
