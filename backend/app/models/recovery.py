from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RecoveryChallenge(Base):
    __tablename__ = "recovery_challenges"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    code_digest: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reset_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    username_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
