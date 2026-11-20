from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.money import from_minor_units, to_minor_units
from app.db.base import Base


class RecurringRule(Base):
    """
    Stateful recurrence schedule attached to a PiggyBank.

    Calendar dates (`start_date`, `next_run_date`, `end_date`) are stored as ISO
    `YYYY-MM-DD` strings so timezone offsets never shift scheduled occurrences.
    """

    __tablename__ = "recurring_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    piggy_bank_id: Mapped[int] = mapped_column(Integer, ForeignKey("piggy_banks.id", ondelete="CASCADE"), nullable=False, index=True)

    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="expense")
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 'daily' | 'weekly' | 'monthly' | 'yearly'
    frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="monthly")
    interval: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    start_date: Mapped[str] = mapped_column(String(10), nullable=False)
    next_run_date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # 'active' | 'paused' | 'stopped'
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", server_default="active", index=True)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    piggy_bank = relationship("PiggyBank")
    executions = relationship("RecurringExecution", back_populates="rule", cascade="all, delete-orphan")

    @property
    def amount(self) -> float:
        return from_minor_units(self.amount_minor)

    @amount.setter
    def amount(self, value: float) -> None:
        self.amount_minor = to_minor_units(value)


class RecurringExecution(Base):
    """
    Idempotency ledger recording each executed occurrence of a RecurringRule.
    """

    __tablename__ = "recurring_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("recurring_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_date: Mapped[str] = mapped_column(String(10), nullable=False)
    transaction_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True
    )
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())

    rule = relationship("RecurringRule", back_populates="executions")

    __table_args__ = (
        UniqueConstraint("rule_id", "scheduled_date", name="uq_recurring_rule_date"),
    )
