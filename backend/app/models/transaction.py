from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.money import from_minor_units, to_minor_units
from app.db.base import Base


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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    piggy_bank_id: Mapped[int] = mapped_column(Integer, ForeignKey("piggy_banks.id"), nullable=False)

    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="expense")
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Both legs of a transfer share this stable identifier. Ordinary entries are null.
    transfer_group_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    # Optional link to the recurring schedule that generated this transaction.
    recurring_rule_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("recurring_rules.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    piggy_bank = relationship("PiggyBank", back_populates="transactions")

    @property
    def amount(self) -> float:
        return from_minor_units(self.amount_minor)

    @amount.setter
    def amount(self, value: float) -> None:
        self.amount_minor = to_minor_units(value)

    @property
    def transaction_id(self) -> str:
        """One logical ID for both transfer legs; a unique ID for other entries."""
        return self.transfer_group_id or f"entry:{self.id}"
