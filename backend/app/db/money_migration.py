"""Move legacy FLOAT ledger amounts to exact integer minor units."""

from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import text

from app.core.money import CENT


def migrate_money(engine):
    with engine.begin() as connection:
        columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(transactions)")}
        if "amount_minor" not in columns:
            connection.exec_driver_sql("ALTER TABLE transactions ADD COLUMN amount_minor BIGINT")
        if "amount" in columns:
            rows = connection.execute(text("SELECT id, amount, amount_minor FROM transactions")).all()
            for tx_id, old_amount, existing_minor in rows:
                if old_amount is None:
                    raise ValueError(f"Transaction {tx_id} has no amount")
                rounded = Decimal(str(old_amount)).quantize(CENT, rounding=ROUND_HALF_UP)
                minor = int(rounded * 100)
                if existing_minor is not None and existing_minor != minor:
                    raise ValueError(f"Transaction {tx_id} has conflicting amount columns")
                connection.execute(text("UPDATE transactions SET amount_minor = :minor WHERE id = :id"),
                                   {"minor": minor, "id": tx_id})
        missing = connection.execute(text("SELECT COUNT(*) FROM transactions WHERE amount_minor IS NULL")).scalar_one()
        if missing:
            raise ValueError(f"{missing} transactions have no minor-unit amount")
        if "amount" in columns:
            connection.exec_driver_sql("ALTER TABLE transactions DROP COLUMN amount")
