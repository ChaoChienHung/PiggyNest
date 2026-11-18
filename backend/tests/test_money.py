import pytest
from sqlalchemy import create_engine

from app.core.money import to_minor_units
from app.db.money_migration import migrate_money
from import_legacy_bookkeeping import LegacyRow, normalized_amount
from datetime import datetime
from decimal import Decimal


def test_minor_units_reject_sub_cent_values():
    assert to_minor_units("0.10") == 10
    assert to_minor_units("-0.02") == -2
    with pytest.raises(ValueError):
        to_minor_units("0.001")


def test_migrate_float_amounts_to_integer_minor_units():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE transactions (id INTEGER PRIMARY KEY, amount FLOAT NOT NULL)")
        connection.exec_driver_sql("INSERT INTO transactions (id, amount) VALUES (1, 0.1), (2, 0.2)")
    migrate_money(engine)
    migrate_money(engine)
    with engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT id, amount_minor FROM transactions ORDER BY id").all() == [(1, 10), (2, 20)]
        assert "amount" not in {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(transactions)")}


def test_legacy_ntd_float_artifact_normalizes_to_whole_dollars():
    row = LegacyRow("ChungHwaPost", "2021_transactions.csv", 3, datetime(2021, 1, 1),
                    Decimal("-15.007"), "Others", "Processing Fee", Decimal(0))
    assert normalized_amount(row) == Decimal("-15")
