"""Audit or apply category consolidation in the configured database.

Maps Other -> Others, Transfer -> Others, and Withdraw/Withdrawal -> Withdrawals
for every user's transactions and category list.

Run from backend/: python consolidate_categories.py [--apply] [--audit PATH]
"""
import argparse
import json
from collections import Counter

from app.db.session import SessionLocal
from app.domain.category_names import consolidate_categories


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Persist the changes")
    parser.add_argument("--audit", help="Write before/after records to this JSON file")
    args = parser.parse_args()

    with SessionLocal() as db:
        try:
            changes = consolidate_categories(db)
            if args.apply:
                db.commit()
            else:
                db.rollback()
        except Exception:
            db.rollback()
            raise

    counts = Counter((c["before"], c["after"]) for c in changes["transactions"])
    print(f"Transactions {'updated' if args.apply else 'to update'}: {len(changes['transactions'])}")
    for (before, after), count in sorted(counts.items()):
        print(f"  {before} -> {after}: {count}")
    print(f"Category rows {'changed' if args.apply else 'to change'}: {len(changes['categories'])}")
    for record in changes["categories"]:
        print(f"  user {record['user_id']}: {record['before']} -> {record['after']} ({record['action']})")
    if args.audit:
        with open(args.audit, "w", encoding="utf-8") as f:
            json.dump(changes, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
