"""Audit and backfill shared IDs for unambiguous historical transfers."""
from collections import defaultdict
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domain.transfer_links import legacy_transfer_pairs
from app.models.piggy_bank import PiggyBank
from app.models.transaction import Transaction


def repair_legacy_transfers(db: Session, apply: bool = False):
    """Return (matched_pairs, unresolved_ids); optionally persist matched IDs.

    Each user's rows are considered independently. The caller owns the commit.
    """
    banks = db.query(PiggyBank).order_by(PiggyBank.id).all()
    by_user = defaultdict(list)
    for bank in banks:
        by_user[bank.user_id].append(bank)

    matched = []
    unresolved = []
    for user_banks in by_user.values():
        bank_ids = [bank.id for bank in user_banks]
        transactions = db.query(Transaction).filter(Transaction.piggy_bank_id.in_(bank_ids)).all()
        by_id = {tx.id: tx for tx in transactions}
        pairs = legacy_transfer_pairs(transactions, user_banks)
        for tx in transactions:
            if tx.type != "transfer" or tx.transfer_group_id:
                continue
            other_id = pairs.get(tx.id)
            if other_id is None:
                unresolved.append(tx.id)
            elif tx.id < other_id:
                matched.append((tx.id, other_id))
                if apply:
                    group_id = str(uuid4())
                    tx.transfer_group_id = group_id
                    by_id[other_id].transfer_group_id = group_id
    return matched, unresolved


def link_confirmed_pair(db: Session, first_id: int, second_id: int):
    """Link two explicitly reviewed legacy entries after checking invariants."""
    first = db.get(Transaction, first_id)
    second = db.get(Transaction, second_id)
    if (first is None or second is None or first.id == second.id
            or first.type != "transfer" or second.type != "transfer"
            or first.transfer_group_id or second.transfer_group_id
            or first.piggy_bank_id == second.piggy_bank_id
            or first.piggy_bank.user_id != second.piggy_bank.user_id
            or first.amount >= 0 or second.amount <= 0
            or abs(first.amount + second.amount) > 1e-8
            or first.date != second.date):
        raise ValueError("IDs must be an unlinked debit and credit with equal amount, date, and owner in different banks")
    group_id = str(uuid4())
    first.transfer_group_id = group_id
    second.transfer_group_id = group_id
    return group_id


def mark_external_transfer(db: Session, entry_id: int):
    """Classify a reviewed, unlinked historical transfer as a single external entry."""
    entry = db.get(Transaction, entry_id)
    if entry is None or entry.type != "transfer" or entry.transfer_group_id or entry.amount == 0:
        raise ValueError("ID must be an unlinked nonzero historical transfer")
    entry.type = "transfer_out" if entry.amount < 0 else "transfer_in"
    return entry.type
