"""Owner-chosen starting display rates; never rewrite a saved user rate."""

from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.currency_rate import CurrencyRate
from app.models.user import User


DEFAULT_SGD_TO_NTD = Decimal("24.00")


def add_missing_default_rates(db: Session) -> int:
    """Add the SGD default to accounts that have not set an SGD rate."""
    missing_user_ids = db.scalars(
        select(User.id)
        .outerjoin(CurrencyRate, and_(
            CurrencyRate.user_id == User.id,
            CurrencyRate.currency == "SGD",
        ))
        .where(CurrencyRate.id.is_(None))
    ).all()
    for user_id in missing_user_ids:
        db.add(CurrencyRate(
            user_id=user_id, currency="SGD", rate_to_ntd=DEFAULT_SGD_TO_NTD,
        ))
    if missing_user_ids:
        db.commit()
    return len(missing_user_ids)
