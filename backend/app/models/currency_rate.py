from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class CurrencyRate(Base):
    """One user-supplied NTD quote for one unit of another currency."""

    __tablename__ = "currency_rates"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    currency = Column(String(10), nullable=False)
    rate_to_ntd = Column(Numeric(18, 4), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", backref="currency_rates")
    __table_args__ = (UniqueConstraint("user_id", "currency", name="uq_user_currency_rate"),)
