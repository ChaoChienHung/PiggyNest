"""Apply reviewed Ludwig legacy transfer rules to the local imported account.

Run from backend/ with --source and --apply. Without --apply this is an audit.
The source CSVs and generated reports are private and must stay outside Git.
"""

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from app.core.config import LOCAL_DATA_DIR
from app.db.session import SessionLocal
from app.models.piggy_bank import PiggyBank
from app.models.transaction import Transaction
from app.models.user import User
from import_legacy_bookkeeping import CURRENCIES, load_rows, normalized_amount, partition_rows
from resolve_legacy_bookkeeping import fingerprint, mentioned_bank


FEE_PAIRS = (
    ("ChangHwaBank/2025_transactions.csv#6", "LudwigTaiwan/2025_transactions.csv#28"),
    ("ChangHwaBank/2025_transactions.csv#8", "LudwigTaiwan/2025_transactions.csv#33"),
    ("ChangHwaBank/2025_transactions.csv#10", "LudwigTaiwan/2025_transactions.csv#32"),
    ("ChangHwaBank/2025_transactions.csv#11", "LudwigTaiwan/2025_transactions.csv#47"),
    ("ChangHwaBank/2025_transactions.csv#12", "LudwigTaiwan/2025_transactions.csv#48"),
    ("LudwigTaiwan/2025_transactions.csv#21", "ChungHwaPost/2025_transactions.csv#8"),
    ("LudwigSingapore/2025_transactions.csv#84", "EZLinkSG60/2025_transactions.csv#2"),
)
CROSS_DATE_PAIRS = (
    ("TaishinBank/2023_transactions.csv#1", "LudwigTaiwan/2023_transactions.csv#82"),
    ("UnitedOverseasBank/2025_transactions.csv#91", "EZLinkSG60/2025_transactions.csv#59"),
)
# These source rows contradict a named destination or have multiple plausible legs.
GENERIC_FEE_KEYS = {
    "ChangHwaBank/2025_transactions.csv#2",
    "ChangHwaBank/2025_transactions.csv#3",
    "ChangHwaBank/2025_transactions.csv#4",
}
HOLD = set()


def make_transfer(db, banks, debit, credit, get_source, log):
    if CURRENCIES[debit.bank] != CURRENCIES[credit.bank] or debit.bank == credit.bank:
        raise ValueError("Transfer requires distinct same-currency PiggyBanks")
    if normalized_amount(debit) >= 0 or normalized_amount(credit) <= 0:
        raise ValueError("Transfer direction is inconsistent")
    if normalized_amount(debit) != -normalized_amount(credit):
        raise ValueError("Transfer principal is not balanced")
    group = str(uuid4())
    for row, category, prefix in (
        (debit, "Transfer Out", f"Transfer to {credit.bank}: "),
        (credit, "Transfer In", f"Transfer from {debit.bank}: "),
    ):
        # A synthetic leg inherits the old file number for provenance. That
        # number may collide with a real row in the destination PiggyBank.
        tx = None if row.description.startswith("Synthetic opposite leg of ") else get_source(row.key)
        if tx is None:
            tx = Transaction(piggy_bank_id=banks[row.bank].id, date=row.date)
            db.add(tx)
        tx.amount = normalized_amount(row)
        tx.type = "transfer"
        tx.category = category
        tx.description = (prefix + ("" if row.description == "Null" else row.description))[:255]
        tx.transfer_group_id = group
        db.flush()
        if row.key and not row.description.startswith("Synthetic opposite leg of "):
            log.append((row.key, tx.id, group, "linked"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--pending-report", type=Path, default=LOCAL_DATA_DIR / "ludwig_import_pending.csv")
    parser.add_argument("--resolved-report", type=Path, default=LOCAL_DATA_DIR / "ludwig_transfer_resolved.csv")
    parser.add_argument("--rule-log", type=Path, default=LOCAL_DATA_DIR / "ludwig_rule_resolution.csv")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows, _, _ = load_rows(args.source)
    source = {row.key: row for row in rows}
    safe, original_pending, _, _ = partition_rows(rows)
    pending_report = list(csv.DictReader(args.pending_report.open(encoding="utf-8-sig", newline="")))
    pending_keys = {row["source_key"] for row in pending_report}
    resolved_keys = {row["source_key"] for row in csv.DictReader(args.resolved_report.open(encoding="utf-8-sig", newline=""))}
    if pending_keys | resolved_keys != {row.key for row in original_pending} or pending_keys & resolved_keys:
        raise ValueError("Pending and resolved reports do not match source")
    if args.rule_log.exists():
        raise ValueError("Rule log already exists; refusing duplicate application")

    used = set(resolved_keys)
    pairs = []
    for debit_key, credit_key in FEE_PAIRS + CROSS_DATE_PAIRS:
        if debit_key in used or credit_key in used:
            raise ValueError("Rule pair overlaps resolved source")
        used.update((debit_key, credit_key))
        pairs.append((source[debit_key], source[credit_key]))
    mother = [row for row in rows if "mother" in row.description.casefold() and row.key not in used]
    used.update(row.key for row in mother)
    singles = []
    for row in rows:
        if row.key in used or row.key in HOLD:
            continue
        if row.category in {"Withdrawal", "Withdraw", "Transfer"} or mentioned_bank(row):
            target = mentioned_bank(row) or ("LudwigTaiwan" if CURRENCIES[row.bank] == "NTD" else "LudwigSingapore")
            if target == row.bank:
                continue
            singles.append((row, target))
            used.add(row.key)
    remaining = sorted((pending_keys - used) | (HOLD & {row.key for row in safe}))
    print(f"Fee pairs: {len(FEE_PAIRS)}; cross-date pairs: {len(CROSS_DATE_PAIRS)}; Mother: {len(mother)}; synthetic pairs: {len(singles)}; pending after: {len(remaining)}")
    for key in remaining:
        print("PENDING", key)
    if not args.apply:
        return

    with SessionLocal() as db:
        user = db.query(User).filter(User.username == "Ludwig").one()
        banks = {bank.name: bank for bank in db.query(PiggyBank).filter(PiggyBank.user_id == user.id)}
        if set(banks) != set(CURRENCIES):
            raise ValueError("PiggyBank set changed")
        original_safe = Counter(fingerprint(row) for row in safe)
        plain = defaultdict(list)
        for tx in db.query(Transaction).join(PiggyBank).filter(PiggyBank.user_id == user.id, Transaction.transfer_group_id.is_(None)):
            plain[(tx.piggy_bank.name, tx.date, Decimal(str(tx.amount)), tx.category or "", tx.description or "")].append(tx)
        if Counter({key: len(values) for key, values in plain.items()}) != original_safe:
            raise ValueError("Imported safe ledger changed; refusing stale resolution")
        mapped = {}
        for row in safe:
            mapped[row.key] = plain[fingerprint(row)].pop()
        def existing(key):
            return mapped.get(key)
        log = []
        try:
            for debit, credit in pairs:
                fee = -normalized_amount(debit) - normalized_amount(credit)
                if fee < 0 or (debit.key, credit.key) in CROSS_DATE_PAIRS and fee != 0:
                    raise ValueError("Invalid fee pair")
                if (debit.key, credit.key) in FEE_PAIRS and fee not in (Decimal(5), Decimal(15)):
                    raise ValueError("Unexpected fee")
                # The original debit included the fee; preserve its net effect.
                principal = normalized_amount(credit)
                if fee:
                    fee_tx = Transaction(piggy_bank_id=banks[debit.bank].id, amount=-fee,
                                         type="expense", category="Bank Fee",
                                         description=f"Transfer fee: {debit.key}", date=debit.date)
                    db.add(fee_tx)
                make_transfer(db, banks, replace(debit, amount=-principal), credit, existing, log)
            for row in mother:
                tx = existing(row.key)
                if tx is None:
                    tx = Transaction(piggy_bank_id=banks[row.bank].id, amount=normalized_amount(row),
                                     category=row.category, description=row.description, date=row.date)
                    db.add(tx)
                tx.type = "transfer_in" if normalized_amount(row) > 0 else "transfer_out"
                db.flush()
                log.append((row.key, tx.id, tx.transaction_id, "external Mother"))
            for row, target in singles:
                if CURRENCIES[row.bank] != CURRENCIES[target]:
                    raise ValueError(f"Cross-currency target: {row.key}")
                fee = Decimal(5) if row.key in GENERIC_FEE_KEYS else Decimal(0)
                if fee and normalized_amount(row) >= -fee:
                    raise ValueError(f"Invalid inferred source fee: {row.key}")
                principal_row = replace(row, amount=normalized_amount(row) + fee)
                if fee:
                    db.add(Transaction(piggy_bank_id=banks[row.bank].id, amount=-fee,
                                       type="expense", category="Bank Fee",
                                       description=f"Transfer fee: {row.key}", date=row.date))
                mirror = replace(row, bank=target, amount=-normalized_amount(principal_row),
                                 description=f"Synthetic opposite leg of {row.key}")
                if normalized_amount(principal_row) < 0:
                    make_transfer(db, banks, principal_row, mirror, existing, log)
                else:
                    make_transfer(db, banks, mirror, principal_row, existing, log)
            db.commit()
        except Exception:
            db.rollback()
            raise

    with args.rule_log.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("source_key", "transaction_id", "logical_id", "rule"))
        writer.writerows(log)
    with args.pending_report.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=pending_report[0].keys())
        writer.writeheader()
        writer.writerows(row for row in pending_report if row["source_key"] in remaining)
        for key in sorted(HOLD & {row.key for row in safe}):
            row = source[key]
            writer.writerow({"source_key": key, "bank": row.bank, "currency": CURRENCIES[row.bank],
                             "date": row.date.date(), "amount": str(row.amount),
                             "category": row.category, "description": row.description,
                             "source_balance": str(row.balance), "possible_counterpart_keys": "",
                             "review_reason": "ambiguous_imported_withdrawal"})


if __name__ == "__main__":
    main()
