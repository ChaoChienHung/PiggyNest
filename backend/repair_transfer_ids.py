"""Audit or repair transfer IDs in the configured database.

Run from backend/: python repair_transfer_ids.py [--apply] [--pair DEBIT_ID CREDIT_ID]
"""
import argparse

from app.db.session import SessionLocal
from app.domain.transfer_repair import link_confirmed_pair, mark_external_transfer, repair_legacy_transfers


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Persist safe repairs")
    parser.add_argument("--pair", nargs=2, type=int, action="append", metavar=("DEBIT_ID", "CREDIT_ID"),
                        help="Link a pair of legacy entries after manual review; requires --apply")
    parser.add_argument("--external", type=int, action="append", metavar="ENTRY_ID",
                        help="Mark a reviewed unlinked legacy entry as an external transfer; requires --apply")
    args = parser.parse_args()
    if (args.pair or args.external) and not args.apply:
        parser.error("--pair and --external require --apply")

    with SessionLocal() as db:
        try:
            for debit_id, credit_id in args.pair or []:
                link_confirmed_pair(db, debit_id, credit_id)
            for entry_id in args.external or []:
                mark_external_transfer(db, entry_id)
            matched, unresolved = repair_legacy_transfers(db, apply=args.apply)
            if args.apply:
                db.commit()
            else:
                db.rollback()
        except Exception:
            db.rollback()
            raise

    print(f"Unambiguous pairs {'linked' if args.apply else 'available to link'}: {len(matched)}")
    print(f"Unresolved legacy entry IDs: {unresolved}")
    if unresolved:
        print("Review each entry, then use --apply --pair DEBIT_ID CREDIT_ID or --apply --external ENTRY_ID.")


if __name__ == "__main__":
    main()
