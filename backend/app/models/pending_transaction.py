from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.money import from_minor_units, to_minor_units
from app.db.base import Base


class PendingTransaction(Base):
    """
    A staged ("cart") transaction that has not yet settled on a PiggyBank ledger.

    Pending transactions do not affect PiggyBank balances, charts, or reports until
    confirmed, at which point a real Transaction row is created atomically.
    """

    __tablename__ = "pending_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    piggy_bank_id: Mapped[int] = mapped_column(Integer, ForeignKey("piggy_banks.id", ondelete="CASCADE"), nullable=False, index=True)

    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="expense")
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Optional ISO YYYY-MM-DD calendar date when the payment is expected to settle.
    expected_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # 'pending' | 'confirmed' | 'cancelled'
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", server_default="pending", index=True)
    confirmed_transaction_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    piggy_bank = relationship("PiggyBank")

    @property
    def amount(self) -> float:
        return from_minor_units(self.amount_minor)

    @amount.setter
    def amount(self, value: float) -> None:
        self.amount_minor = to_minor_units(value)
