from datetime import datetime

from clean_transaction_descriptions import clean_descriptions
from app.models.piggy_bank import PiggyBank
from app.models.transaction import Transaction
from app.models.user import User


def test_cleanup_audits_every_user_and_preserves_transfer_links(db):
    first = User(username="cleanup_first", email="cleanup_first@example.test", hashed_password="x")
    second = User(username="cleanup_second", email="cleanup_second@example.test", hashed_password="x")
    db.add_all([first, second])
    db.flush()
    source = PiggyBank(user_id=first.id, name="Source", currency="SGD")
    target = PiggyBank(user_id=first.id, name="Target", currency="SGD")
    other = PiggyBank(user_id=second.id, name="Other", currency="NTD")
    db.add_all([source, target, other])
    db.flush()
    date = datetime(2025, 1, 2)
    rows = [
        Transaction(piggy_bank_id=source.id, amount_minor=100, type="income", category="Interest", description="Null", date=date),
        Transaction(piggy_bank_id=other.id, amount_minor=-250, type="expense", category="Others", description=None, date=date),
        Transaction(piggy_bank_id=source.id, amount_minor=-500, type="transfer", category="Transfer Out", description=" ", date=date, transfer_group_id="pair-1"),
        Transaction(piggy_bank_id=target.id, amount_minor=500, type="transfer", category="Transfer In", description="Null", date=date, transfer_group_id="pair-1"),
        Transaction(piggy_bank_id=source.id, amount_minor=-300, type="transfer_out", category="Others", description="null", date=date),
        Transaction(piggy_bank_id=other.id, amount_minor=400, type="income", category="Prize", description="Already clear", date=date),
    ]
    db.add_all(rows)
    db.flush()
    original = {row.id: (row.amount_minor, row.date, row.category, row.transfer_group_id) for row in rows}

    changes = clean_descriptions(db)

    assert len(changes) == 5
    assert [row.description for row in rows] == [
        "Interest", "Other expense", "Transfer Out", "Transfer In", "Bank transfer out", "Already clear",
    ]
    assert {row.id: (row.amount_minor, row.date, row.category, row.transfer_group_id) for row in rows} == original
    assert all(change["id"] and "before" in change and change["after"] for change in changes)
    assert clean_descriptions(db) == []
