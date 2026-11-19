from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class CurrencyRate(Base):
    """One user-supplied NTD quote for one unit of another currency."""

    __tablename__ = "currency_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    rate_to_ntd: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", backref="currency_rates")
    __table_args__ = (UniqueConstraint("user_id", "currency", name="uq_user_currency_rate"),)
