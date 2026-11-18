from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from app.db.base import Base


class RecoveryChallenge(Base):
    __tablename__ = "recovery_challenges"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    code_digest = Column(String(64), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    attempts = Column(Integer, nullable=False, default=0)
    reset_sent_at = Column(DateTime, nullable=True)
    username_sent_at = Column(DateTime, nullable=True)
