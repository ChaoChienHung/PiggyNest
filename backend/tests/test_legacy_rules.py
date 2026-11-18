from dataclasses import replace
from datetime import datetime
from decimal import Decimal

from app.models.piggy_bank import PiggyBank
from app.models.transaction import Transaction
from app.models.user import User
from apply_legacy_rules import make_transfer
from import_legacy_bookkeeping import LegacyRow


def test_synthetic_leg_cannot_overwrite_colliding_source_id(db):
    user = User(username="legacy_collision", email="legacy_collision@example.com", hashed_password="test")
    db.add(user)
    db.flush()
    source_bank = PiggyBank(user_id=user.id, name="TaishinBank", currency="NTD")
    target_bank = PiggyBank(user_id=user.id, name="LudwigTaiwan", currency="NTD")
    db.add_all((source_bank, target_bank))
    db.flush()
    existing = Transaction(piggy_bank_id=target_bank.id, amount=-0.69,
                           type="expense", category="Transport", description="MRT",
                           date=datetime(2024, 1, 1))
    db.add(existing)
    db.flush()
    existing_id = existing.id
    debit = LegacyRow("TaishinBank", "2024_transactions.csv", 5, datetime(2024, 1, 1),
                      Decimal("-1000"), "Withdrawal", "Null", Decimal(0))
    mirror = replace(debit, bank="LudwigTaiwan", amount=Decimal("1000"),
                     description=f"Synthetic opposite leg of {debit.key}")
    log = []
    make_transfer(db, {source_bank.name: source_bank, target_bank.name: target_bank},
                  debit, mirror, lambda key: existing if key == mirror.key else None, log)
    db.flush()
    assert db.get(Transaction, existing_id).description == "MRT"
    assert db.get(Transaction, existing_id).amount_minor == -69
    assert db.query(Transaction).filter(Transaction.transfer_group_id.is_not(None)).count() == 2
    assert len(log) == 1 and log[0][0] == debit.key
