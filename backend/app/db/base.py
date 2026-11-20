import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass

# Import all models here so that Base has them before being imported by Alembic or create_all
from app.models.user import User
from app.models.piggy_bank import PiggyBank
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.recovery import RecoveryChallenge
from app.models.currency_rate import CurrencyRate
from app.models.pending_transaction import PendingTransaction
from app.models.notification import Notification
from app.models.recurring_rule import RecurringRule, RecurringExecution

# Format database URL properly
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite"):
    # Ensure data directory exists
    data_dir = os.path.dirname(os.path.abspath(db_url.replace("sqlite:///", "")))
    if data_dir:
        os.makedirs(data_dir, exist_ok=True)
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(db_url)
