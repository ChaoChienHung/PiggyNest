"""Audit or replace null-like transaction descriptions for every user.

Run from backend/: python clean_transaction_descriptions.py [--apply] [--audit PATH]
The audit contains one before/after record per changed transaction. A dry run is
the default. No transaction amount, date, category, or transfer link is changed.
"""

import argparse
import json
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.piggy_bank import PiggyBank
from app.models.transaction import Transaction


def is_null_like(value):
    return value is None or value.strip().casefold() in {"", "null"}


def replacement_for(transaction):
    category = (transaction.category or "").strip()
    if category and category.casefold() not in {"other", "others"}:
        return category, "category"
    if transaction.type == "transfer_in":
        return "Bank transfer in", "generic type: no specific counterparty or category"
    if transaction.type == "transfer_out":
        return "Bank transfer out", "generic type: no specific counterparty or category"
    if transaction.type == "income":
        return "Other income", "generic type: no specific source or category"
    if transaction.type == "expense":
        return "Other expense", "generic type: no specific merchant or category"
    return transaction.type.replace("_", " ").capitalize(), "generic type: no specific category"


def clean_descriptions(db):
    changes = []
    rows = db.execute(
        select(Transaction)
        .join(PiggyBank, Transaction.piggy_bank_id == PiggyBank.id)
        .order_by(PiggyBank.user_id, Transaction.id)
    ).scalars()
    for transaction in rows:
        if not is_null_like(transaction.description):
            continue
        after, basis = replacement_for(transaction)
        changes.append({
            "id": transaction.id,
            "user_id": transaction.piggy_bank.user_id,
            "piggy_bank_id": transaction.piggy_bank_id,
            "type": transaction.type,
            "category": transaction.category,
            "before": transaction.description,
            "after": after,
            "basis": basis,
        })
        transaction.description = after
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Persist description changes")
    parser.add_argument("--audit", type=Path, help="Write per-ID before/after JSON")
    args = parser.parse_args()

    with SessionLocal() as db:
        try:
            changes = clean_descriptions(db)
            if args.apply:
                db.commit()
            else:
                db.rollback()
        except Exception:
            db.rollback()
            raise

    if args.audit:
        args.audit.parent.mkdir(parents=True, exist_ok=True)
        args.audit.write_text(json.dumps(changes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Transactions {'updated' if args.apply else 'to update'}: {len(changes)}")
    generic = [change for change in changes if change["basis"].startswith("generic")]
    if generic:
        print(f"Generic descriptions (review the audit): {len(generic)}")
        print("IDs: " + ", ".join(str(change["id"]) for change in generic))


if __name__ == "__main__":
    main()
