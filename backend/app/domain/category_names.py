"""Canonical names for categories that used to exist under several spellings.

`Transfer` is retired as a category: a transaction's type (`transfer_in`,
`transfer_out`, or a PiggyBank `transfer`) already says it moves money, so a
bank transfer's category should describe its purpose and falls back to `Others`.
PiggyBank transfers keep their system-set `Transfer In` / `Transfer Out`
labels, which are not user categories.
"""
from typing import Optional

FALLBACK_CATEGORY = "Others"
WITHDRAWALS_CATEGORY = "Withdrawals"

_ALIASES = {
    "other": FALLBACK_CATEGORY,
    "others": FALLBACK_CATEGORY,
    "transfer": FALLBACK_CATEGORY,
    "withdraw": WITHDRAWALS_CATEGORY,
    "withdrawal": WITHDRAWALS_CATEGORY,
    "withdrawals": WITHDRAWALS_CATEGORY,
}

def canonical_category(name: Optional[str]) -> Optional[str]:
    """Return the canonical spelling of a category name; other names are unchanged."""
    if name is None:
        return None
    return _ALIASES.get(name.strip().lower(), name)


def consolidate_categories(db):
    """Rewrite old category spellings to their canonical names for every user.

    Changes only transaction categories and category rows; amounts, dates,
    descriptions, and transfer links are untouched. Returns before/after
    records; the caller commits or rolls back. Running it again finds nothing.
    """
    from app.models.category import Category
    from app.models.piggy_bank import PiggyBank
    from app.models.transaction import Transaction

    changes = {"transactions": [], "categories": []}
    for tx in db.query(Transaction).filter(Transaction.category.isnot(None)).order_by(Transaction.id):
        new = canonical_category(tx.category)
        if new != tx.category:
            user_id = db.query(PiggyBank.user_id).filter(PiggyBank.id == tx.piggy_bank_id).scalar()
            changes["transactions"].append(
                {"id": tx.id, "user_id": user_id, "type": tx.type, "before": tx.category, "after": new})
            tx.category = new

    names_by_user = {}
    for category in db.query(Category).order_by(Category.id):
        names_by_user.setdefault(category.user_id, set()).add(category.name)
    for category in db.query(Category).order_by(Category.id).all():
        new = canonical_category(category.name)
        if new == category.name:
            continue
        names = names_by_user[category.user_id]
        record = {"id": category.id, "user_id": category.user_id, "before": category.name, "after": new}
        names.discard(category.name)
        if new in names:
            record["action"] = "deleted duplicate"
            db.delete(category)
        else:
            record["action"] = "renamed"
            category.name = new
            names.add(new)
        changes["categories"].append(record)
    db.flush()
    return changes
