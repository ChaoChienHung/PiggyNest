from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PiggyBank(Base):
    """
    SQLAlchemy Model representing a user's PiggyBank (account).

    Attributes:
        id (int): Primary key.
        user_id (int): Foreign key linking to the User who owns this PiggyBank.
        name (str): The display name of the PiggyBank.
        currency (str): The currency identifier (default 'USD').
        is_pinned (bool): Whether this PiggyBank is pinned to the front of lists.
    """
    __tablename__ = "piggy_banks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_piggy_bank"),
    )

    # Relationships
    user = relationship("User", backref="piggy_banks")
    transactions = relationship("Transaction", back_populates="piggy_bank", cascade="all, delete-orphan")
