from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class PiggyBank(Base):
    """
    SQLAlchemy Model representing a user's PiggyBank (account).
    
    Attributes:
        id (int): Primary key.
        user_id (int): Foreign key linking to the User who owns this PiggyBank.
        name (str): The display name of the PiggyBank.
        currency (str): The currency identifier (default 'USD').
    """
    __tablename__ = "piggy_banks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(50), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_piggy_bank"),
    )

    # Relationships
    user = relationship("User", backref="piggy_banks")
    transactions = relationship("Transaction", back_populates="piggy_bank", cascade="all, delete-orphan")
