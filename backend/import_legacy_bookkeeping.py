"""Import unambiguous legacy CSV transactions; report possible PiggyBank transfers.

Run from backend/ with --source pointing at a user's piggy_banks directory.
The default mode only audits. --apply creates one user and imports safe rows in
one commit. PIGGYNEST_IMPORT_PASSWORD must be set for --apply.
"""

import argparse
import csv
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import or_

from app.core.security import get_password_hash
from app.core.config import LOCAL_DATA_DIR
from app.db.base import Base, engine
from app.db.money_migration import migrate_money
from app.db.session import SessionLocal
from app.models.category import Category
from app.models.piggy_bank import PiggyBank
from app.models.transaction import Transaction
from app.models.user import User


HEADERS = ("Transaction ID", "Date", "Amount", "Category", "Description", "Balance")
# The legacy CSVs have no currency column. Verify this mapping before applying.
CURRENCIES = {
    "ChangHwaBank": "NTD",
    "ChungHwaPost": "NTD",
    "FirstBank": "NTD",
    "LudwigTaiwan": "NTD",
    "TaishinBank": "NTD",
    "EZLinkSG60": "SGD",
    "LudwigSingapore": "SGD",
    "UnitedOverseasBank": "SGD",
}


def normalized_amount(row):
    """Discard known sub-cent Float residue in legacy ChungHwaPost NTD rows."""
    amount = row.amount
    if row.bank == "ChungHwaPost":
        whole = amount.to_integral_value()
        if Decimal(0) < abs(amount - whole) < Decimal("0.01"):
            amount = whole
    if amount * 100 != (amount * 100).to_integral_value():
        raise ValueError(f"Source amount has unsupported sub-cent precision: {row.key}")
    return amount

# User-confirmed corrections to dates mistyped in the 2013 source file.
DATE_CORRECTIONS = {
    ("TaishinBank", "2013_transactions.csv", 7): "2013-11-11",
    ("TaishinBank", "2013_transactions.csv", 8): "2013-12-21",
}


@dataclass(frozen=True)
class LegacyRow:
    bank: str
    file: str
    old_id: int
    date: datetime
    amount: Decimal
    category: str
    description: str
    balance: Decimal

    @property
    def key(self):
        return f"{self.bank}/{self.file}#{self.old_id}"


def load_rows(root: Path):
    banks = sorted(path for path in root.iterdir() if path.is_dir())
    names = {path.name for path in banks}
    if names != set(CURRENCIES):
        raise ValueError(f"Unexpected bank directories: missing={sorted(set(CURRENCIES)-names)}, extra={sorted(names-set(CURRENCIES))}")
    rows = []
    balance_warnings = []
    date_warnings = []
    for bank in banks:
        files = sorted((bank / "csv").glob("*_transactions.csv"))
        if not files:
            raise ValueError(f"No CSV files in {bank}")
        for path in files:
            year = path.name.split("_", 1)[0]
            seen = set()
            running = Decimal(0)
            mismatches = 0
            last_balance = None
            with path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                if tuple(reader.fieldnames or ()) != HEADERS:
                    raise ValueError(f"Unexpected CSV columns in {path}")
                for line, item in enumerate(reader, 2):
                    try:
                        old_id = int(item["Transaction ID"])
                        date = datetime.fromisoformat(item["Date"])
                        amount = Decimal(item["Amount"])
                        balance = Decimal(item["Balance"])
                    except (ValueError, InvalidOperation, TypeError) as exc:
                        raise ValueError(f"Invalid value in {path}:{line}") from exc
                    if (old_id <= 0 or old_id in seen
                            or not amount.is_finite() or not balance.is_finite()
                            or len(item["Category"]) > 100 or len(item["Description"]) > 255):
                        raise ValueError(f"Invalid or duplicate source row in {path}:{line}")
                    correction = DATE_CORRECTIONS.get((bank.name, path.name, old_id))
                    if correction:
                        date_warnings.append((bank.name, path.name, old_id, item["Date"], correction))
                        date = datetime.fromisoformat(correction)
                    if str(date.year) != year:
                        raise ValueError(f"Unresolved year mismatch in {path}:{line}")
                    seen.add(old_id)
                    row = LegacyRow(bank.name, path.name, old_id, date, amount,
                                    item["Category"], item["Description"], balance)
                    rows.append(row)
                    running += amount
                    last_balance = balance
                    if abs(running - balance) > Decimal("0.000001"):
                        mismatches += 1
            if last_balance is None:
                raise ValueError(f"Empty CSV file: {path}")
            if mismatches:
                balance_warnings.append((bank.name, path.name, mismatches))
            if abs(running - last_balance) > Decimal("0.000001"):
                raise ValueError(f"Final balance does not match summed amounts in {path}")
    return rows, balance_warnings, date_warnings


def partition_rows(rows):
    by_date_and_amount = defaultdict(list)
    for row in rows:
        by_date_and_amount[(CURRENCIES[row.bank], row.date, abs(normalized_amount(row)))].append(row)
    possible_matches = defaultdict(set)
    for group in by_date_and_amount.values():
        for index, first in enumerate(group):
            for second in group[index + 1:]:
                if first.bank != second.bank and normalized_amount(first) == -normalized_amount(second):
                    possible_matches[first.key].add(second.key)
                    possible_matches[second.key].add(first.key)
    pending = {row.key for row in rows if row.category == "Transfer"}
    pending.update(possible_matches)
    reference_reasons = {}
    for row in rows:
        if row.category not in {"Transfer", "Withdrawal", "Withdraw", "Savings"}:
            continue
        description = row.description.casefold()
        if any(name != row.bank and name.casefold() in description for name in CURRENCIES):
            reference_reasons[row.key] = "named_internal_transfer_without_exact_match"
        elif description == "ludwig":
            reference_reasons[row.key] = "ambiguous_account_reference"
    pending.update(reference_reasons)
    safe = [row for row in rows if row.key not in pending]
    return safe, [row for row in rows if row.key in pending], possible_matches, reference_reasons


def write_report(path, pending, possible_matches, reference_reasons, balance_warnings, date_warnings):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("source_key", "bank", "currency", "date", "amount", "category",
                         "description", "source_balance", "possible_counterpart_keys", "review_reason"))
        for row in pending:
            writer.writerow((row.key, row.bank, CURRENCIES[row.bank], row.date.date(), str(row.amount),
                             row.category, row.description, str(row.balance),
                             "; ".join(sorted(possible_matches[row.key])),
                             "possible_internal_transfer" if possible_matches[row.key]
                             else reference_reasons[row.key] if row.key in reference_reasons
                             else "unmatched_transfer_category"))
    print(f"Pending report: {path} ({len(pending)} rows)")
    for bank, file, count in balance_warnings:
        print(f"Source balance warning: {bank}/{file} has {count} intermediate running-balance mismatches")
    for bank, file, old_id, source_date, corrected_date in date_warnings:
        print(f"User-confirmed date correction: {bank}/{file}#{old_id} {source_date} -> {corrected_date}")


def import_safe_rows(rows, safe, username, email, password):
    Base.metadata.create_all(bind=engine)
    migrate_money(engine)
    with SessionLocal() as db:
        if db.query(User).filter(or_(User.username == username, User.email == email)).first():
            raise ValueError("Target user already exists; refusing to duplicate an import")
        try:
            user = User(username=username, email=email, hashed_password=get_password_hash(password))
            db.add(user)
            db.flush()
            banks = {}
            for name, currency in CURRENCIES.items():
                bank = PiggyBank(user_id=user.id, name=name, currency=currency)
                db.add(bank)
                db.flush()
                banks[name] = bank
            for name in sorted({row.category for row in rows}):
                db.add(Category(user_id=user.id, name=name))
            for row in safe:
                db.add(Transaction(
                    piggy_bank_id=banks[row.bank].id,
                    amount=float(normalized_amount(row)),
                    type="income" if normalized_amount(row) > 0 else "expense",
                    category=row.category,
                    description=row.description,
                    date=row.date,
                ))
            db.commit()
            return user.id
        except Exception:
            db.rollback()
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Legacy user's piggy_banks directory")
    parser.add_argument("--report", type=Path, default=LOCAL_DATA_DIR / "ludwig_import_pending.csv")
    parser.add_argument("--username", default="Ludwig")
    parser.add_argument("--email", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    rows, balance_warnings, date_warnings = load_rows(args.source)
    safe, pending, possible_matches, reference_reasons = partition_rows(rows)
    write_report(args.report, pending, possible_matches, reference_reasons, balance_warnings, date_warnings)
    print(f"Source: {len(rows)} transactions in {len(CURRENCIES)} PiggyBanks; safe: {len(safe)}; pending: {len(pending)}")
    if args.apply:
        password = os.environ.get("PIGGYNEST_IMPORT_PASSWORD")
        if not password:
            parser.error("PIGGYNEST_IMPORT_PASSWORD is required with --apply")
        user_id = import_safe_rows(rows, safe, args.username, args.email, password)
        print(f"Imported user ID {user_id}, {len(CURRENCIES)} PiggyBanks, {len(safe)} transactions")


if __name__ == "__main__":
    main()
