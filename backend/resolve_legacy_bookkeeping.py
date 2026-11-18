"""Link uniquely supported legacy PiggyBank transfers without inventing a leg.

Run from backend/ with --source pointing at the legacy piggy_banks directory.
Audit is read-only. --apply verifies the imported account still matches the safe
CSV rows, inserts linked transfer legs in one commit, and updates local reports.
"""

import argparse
import csv
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from app.core.config import LOCAL_DATA_DIR
from app.db.session import SessionLocal
from app.models.piggy_bank import PiggyBank
from app.models.transaction import Transaction
from app.models.user import User
from import_legacy_bookkeeping import CURRENCIES, load_rows, normalized_amount, partition_rows


def mentioned_bank(row):
    """Return a named counterparty, including legacy shorthand, when present."""
    description = re.sub(r"[^a-z0-9]", "", row.description.casefold())
    for name in CURRENCIES:
        if name.casefold() in description:
            return name
    if "ezlink" in description:
        return "EZLinkSG60"
    if "unitedoverseas" in description or description == "uob":
        return "UnitedOverseasBank"
    if description == "ludwig":
        return "LudwigTaiwan" if CURRENCIES[row.bank] == "NTD" else "LudwigSingapore"
    return None


def exact_transfer_pairs(pending, possible_matches):
    """Choose non-conflicting exact pairs, preferring an explicit named bank."""
    by_key = {row.key: row for row in pending}
    edges = {}
    neighbors = defaultdict(set)
    for row in pending:
        for other_key in possible_matches[row.key]:
            if other_key not in by_key:
                continue
            other = by_key[other_key]
            if (mentioned_bank(row) not in (None, other.bank)
                    or mentioned_bank(other) not in (None, row.bank)):
                continue
            key = tuple(sorted((row.key, other_key)))
            if key not in edges:
                score = int(mentioned_bank(row) == other.bank) + int(mentioned_bank(other) == row.bank)
                edges[key] = score
                neighbors[row.key].add(other_key)
                neighbors[other_key].add(row.key)

    chosen = []
    used = set()
    # A named destination resolves a same-day amount collision only when it is
    # the unique strongest option for both source rows.
    for pair, score in sorted(edges.items(), key=lambda item: (-item[1], item[0])):
        if score == 0 or any(key in used for key in pair):
            continue
        if all(score > max((edges[tuple(sorted((key, other)))] for other in neighbors[key]
                            if other != pair[1 - index]), default=-1)
               for index, key in enumerate(pair)):
            chosen.append(pair)
            used.update(pair)

    for pair in sorted(edges):
        if any(key in used for key in pair):
            continue
        if all(len(neighbors[key] - used) == 1 for key in pair):
            chosen.append(pair)
            used.update(pair)
    return chosen


def fingerprint(row):
    return (row.bank, row.date, normalized_amount(row), row.category, row.description)


def apply_pairs(safe, pending, pairs, report_path, resolved_path, username):
    source_by_key = {row.key: row for row in pending}
    expected_safe = Counter(fingerprint(row) for row in safe)
    with report_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        report_rows = list(reader)
        fieldnames = reader.fieldnames
    if {row["source_key"] for row in report_rows} != {row.key for row in pending}:
        raise ValueError("Pending report differs from the source audit; refusing to apply")
    if resolved_path.exists():
        raise ValueError("Resolved report already exists; refusing to apply twice")
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == username).one()
        banks = {bank.name: bank for bank in db.query(PiggyBank).filter(PiggyBank.user_id == user.id)}
        if set(banks) != set(CURRENCIES) or any(banks[name].currency != currency for name, currency in CURRENCIES.items()):
            raise ValueError("Imported PiggyBanks or currencies changed; review before resolving transfers")
        imported = db.query(Transaction).join(PiggyBank).filter(PiggyBank.user_id == user.id).all()
        actual = Counter((tx.piggy_bank.name, tx.date, Decimal(str(tx.amount)),
                          tx.category or "", tx.description or "") for tx in imported)
        if actual != expected_safe:
            raise ValueError("Imported transactions differ from the original safe set; refusing duplicate or stale resolution")
        inserted = []
        try:
            for first_key, second_key in pairs:
                first, second = source_by_key[first_key], source_by_key[second_key]
                debit, credit = (first, second) if first.amount < 0 else (second, first)
                if (debit.bank == credit.bank or CURRENCIES[debit.bank] != CURRENCIES[credit.bank]
                        or debit.date != credit.date or normalized_amount(debit) != -normalized_amount(credit)):
                    raise ValueError(f"Inconsistent pair: {first_key}, {second_key}")
                group_id = str(uuid4())
                for row, category, prefix in (
                    (debit, "Transfer Out", f"Transfer to {credit.bank}: "),
                    (credit, "Transfer In", f"Transfer from {debit.bank}: "),
                ):
                    note = "" if row.description == "Null" else row.description
                    tx = Transaction(
                        piggy_bank_id=banks[row.bank].id, amount=float(normalized_amount(row)),
                        type="transfer", category=category,
                        description=(prefix + note)[:255], date=row.date,
                        transfer_group_id=group_id,
                    )
                    db.add(tx)
                    db.flush()
                    inserted.append((row.key, tx.id, group_id))
            db.commit()
        except Exception:
            db.rollback()
            raise

    resolved_keys = {key for key, _, _ in inserted}
    with resolved_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("source_key", "new_transaction_id", "shared_transaction_id"))
        writer.writerows(inserted)
    with report_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(row for row in report_rows if row["source_key"] not in resolved_keys)
    return inserted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--pending-report", type=Path, default=LOCAL_DATA_DIR / "ludwig_import_pending.csv")
    parser.add_argument("--resolved-report", type=Path, default=LOCAL_DATA_DIR / "ludwig_transfer_resolved.csv")
    parser.add_argument("--username", default="Ludwig")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    rows, _, _ = load_rows(args.source)
    safe, pending, possible_matches, _ = partition_rows(rows)
    pairs = exact_transfer_pairs(pending, possible_matches)
    print(f"Exact, non-conflicting pairs: {len(pairs)} ({len(pairs) * 2} source transactions)")
    print(f"Remaining pending source transactions: {len(pending) - len(pairs) * 2}")
    if args.apply:
        inserted = apply_pairs(safe, pending, pairs, args.pending_report,
                               args.resolved_report, args.username)
        print(f"Imported {len(inserted)} linked transactions; updated {args.pending_report}")


if __name__ == "__main__":
    main()
