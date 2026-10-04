"""Account scoped Excel backups. Imports add new banks atomically."""
from collections import defaultdict
from datetime import datetime
from io import BytesIO
from math import isfinite
from uuid import uuid4
from zipfile import BadZipFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from openpyxl import Workbook, load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.domain.piggy_banks import NAME_PATTERN
from app.models.piggy_bank import PiggyBank
from app.models.transaction import Transaction
from app.models.user import User
from app.models.category import Category

router = APIRouter()
BANK_HEADERS = ("bank_id", "name", "currency")
TX_HEADERS = ("entry_id", "bank_id", "amount", "type", "category", "description", "date", "transaction_id")
OLD_TX_HEADERS = ("transaction_id", "bank_id", "amount", "type", "category", "description", "date", "transfer_group_id")
CATEGORY_HEADERS = ("name",)
MAX_BYTES = 10 * 1024 * 1024
MAX_ROWS = 100_000


def _text_cell(sheet, row, column, value):
    cell = sheet.cell(row, column, value)
    # User text beginning with '=' must stay data, never an Excel formula.
    cell.data_type = "s"


def _legacy_transfer_groups(transactions, banks):
    """Pair only unambiguous transfers made before transfer_group_id existed."""
    names = {bank.id: bank.name for bank in banks}
    old = [tx for tx in transactions if tx.type == "transfer" and not tx.transfer_group_id]
    candidates = {}
    for debit in old:
        if debit.amount >= 0 or debit.category != "Transfer Out":
            continue
        matches = [credit for credit in old if (
            credit.amount == -debit.amount
            and credit.date == debit.date
            and credit.piggy_bank_id != debit.piggy_bank_id
            and credit.category == "Transfer In"
            and (debit.description or "").startswith(f"Transfer to {names[credit.piggy_bank_id]}: ")
            and (credit.description or "").startswith(f"Transfer from {names[debit.piggy_bank_id]}: ")
            and debit.description.split(": ", 1)[1] == credit.description.split(": ", 1)[1]
        )]
        if len(matches) == 1:
            candidates[debit.id] = matches[0].id
    credits = defaultdict(list)
    for debit_id, credit_id in candidates.items():
        credits[credit_id].append(debit_id)
    result = {}
    for debit_id, credit_id in candidates.items():
        if len(credits[credit_id]) == 1:
            group = str(uuid4())
            result[debit_id] = group
            result[credit_id] = group
    return result


@router.get("/export")
def export_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    banks = db.query(PiggyBank).filter(PiggyBank.user_id == current_user.id).order_by(PiggyBank.id).all()
    transactions = (
        db.query(Transaction).join(PiggyBank)
        .filter(PiggyBank.user_id == current_user.id)
        .order_by(Transaction.id).all()
    )
    categories = db.query(Category).filter(Category.user_id == current_user.id).order_by(Category.name).all()
    legacy_groups = _legacy_transfer_groups(transactions, banks)
    workbook = Workbook()
    bank_sheet = workbook.active
    bank_sheet.title = "Piggy Banks"
    bank_sheet.append(BANK_HEADERS)
    bank_sheet.freeze_panes = "A2"
    for bank in banks:
        row = bank_sheet.max_row + 1
        bank_sheet.cell(row, 1, bank.id)
        _text_cell(bank_sheet, row, 2, bank.name)
        _text_cell(bank_sheet, row, 3, bank.currency)

    tx_sheet = workbook.create_sheet("Transactions")
    tx_sheet.append(TX_HEADERS)
    tx_sheet.freeze_panes = "A2"
    for tx in transactions:
        row = tx_sheet.max_row + 1
        tx_sheet.cell(row, 1, tx.id)
        tx_sheet.cell(row, 2, tx.piggy_bank_id)
        tx_sheet.cell(row, 3, tx.amount)
        _text_cell(tx_sheet, row, 4, tx.type)
        if tx.category is not None:
            _text_cell(tx_sheet, row, 5, tx.category)
        if tx.description is not None:
            _text_cell(tx_sheet, row, 6, tx.description)
        # Excel does not support timezone aware datetime cells.
        tx_sheet.cell(row, 7, tx.date.isoformat())
        logical_id = tx.transfer_group_id or legacy_groups.get(tx.id) or f"entry:{tx.id}"
        _text_cell(tx_sheet, row, 8, logical_id)

    category_sheet = workbook.create_sheet("Categories")
    category_sheet.append(CATEGORY_HEADERS)
    for category in categories:
        _text_cell(category_sheet, category_sheet.max_row + 1, 1, category.name)

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="piggynest-backup.xlsx"'},
    )


def _fail(message):
    raise HTTPException(status_code=400, detail=message)


def _id(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        _fail(f"{label} must be a positive integer")
    return value


def _string(value, label, maximum, required=False):
    if value is None and not required:
        return None
    if not isinstance(value, str) or (required and not value) or len(value) > maximum:
        _fail(f"{label} is invalid")
    return value


def _rows(workbook, name, headers):
    if name not in workbook:
        _fail(f"Missing sheet: {name}")
    sheet = workbook[name]
    if sheet.max_column != len(headers) or tuple(cell.value for cell in sheet[1]) != headers:
        _fail(f"Invalid columns in {name}")
    if sheet.max_row - 1 > MAX_ROWS:
        _fail(f"Too many rows in {name}")
    for cells in sheet.iter_rows(min_row=2):
        if any(cell.data_type == "f" for cell in cells):
            _fail(f"Formulas are not allowed in {name}")
        values = tuple(cell.value for cell in cells)
        if any(value is not None for value in values):
            yield cells[0].row, values


def _parse(workbook):
    banks = {}
    names = set()
    for row, values in _rows(workbook, "Piggy Banks", BANK_HEADERS):
        bank_id = _id(values[0], f"Piggy Banks row {row} bank_id")
        name = _string(values[1], f"Piggy Banks row {row} name", 50, True)
        currency = _string(values[2], f"Piggy Banks row {row} currency", 10, True)
        if not NAME_PATTERN.fullmatch(name) or bank_id in banks or name in names:
            _fail(f"Duplicate or invalid piggy bank in row {row}")
        banks[bank_id] = (name, currency)
        names.add(name)

    transactions = []
    ids = set()
    groups = defaultdict(list)
    transaction_headers = tuple(cell.value for cell in workbook["Transactions"][1]) if "Transactions" in workbook else ()
    old_format = transaction_headers == OLD_TX_HEADERS
    for row, values in _rows(workbook, "Transactions", OLD_TX_HEADERS if old_format else TX_HEADERS):
        tx_id = _id(values[0], f"Transactions row {row} entry_id")
        bank_id = _id(values[1], f"Transactions row {row} bank_id")
        if tx_id in ids or bank_id not in banks:
            _fail(f"Duplicate transaction or unknown piggy bank in row {row}")
        ids.add(tx_id)
        amount = values[2]
        if isinstance(amount, bool) or not isinstance(amount, (float, int)) or not isfinite(amount):
            _fail(f"Invalid amount in row {row}")
        tx_type = _string(values[3], f"Transactions row {row} type", 50, True)
        category = _string(values[4], f"Transactions row {row} category", 100)
        description = _string(values[5], f"Transactions row {row} description", 255)
        date_value = values[6]
        try:
            date = date_value if isinstance(date_value, datetime) else datetime.fromisoformat(date_value)
        except (TypeError, ValueError):
            _fail(f"Invalid date in row {row}")
        logical_id = values[7] if not old_format else values[7] or f"entry:{tx_id}"
        logical_id = _string(logical_id, f"Transactions row {row} transaction_id", 64, True)
        if logical_id.startswith("entry:"):
            if logical_id != f"entry:{tx_id}":
                _fail(f"Invalid individual transaction ID in row {row}")
            group = None
        else:
            if tx_type != "transfer":
                _fail(f"Non-transfer transaction has shared transaction ID in row {row}")
            group = logical_id
        record = (bank_id, float(amount), tx_type, category, description, date, group)
        transactions.append(record)
        if group:
            groups[group].append(record)
    for group, pair in groups.items():
        if (len(pair) != 2 or pair[0][0] == pair[1][0]
                or abs(sum(item[1] for item in pair)) > 1e-8
                or not any(item[1] < 0 for item in pair)
                or not any(item[1] > 0 for item in pair)):
            _fail(f"Transfer group {group} must have matching debit and credit rows in different banks")
    categories = set()
    if "Categories" in workbook:
        for row, values in _rows(workbook, "Categories", CATEGORY_HEADERS):
            name = _string(values[0], f"Categories row {row} name", 100, True)
            if name in categories:
                _fail(f"Duplicate category in row {row}")
            categories.add(name)
    return banks, transactions, categories


@router.post("/import")
async def import_account(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        _fail("Choose a .xlsx backup file")
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        _fail("File exceeds 10 MB limit")
    try:
        workbook = load_workbook(BytesIO(data), read_only=True, data_only=False)
        banks, transactions, categories = _parse(workbook)
        workbook.close()
    except (InvalidFileException, BadZipFile, OSError, ValueError, KeyError, IndexError) as exc:
        _fail(f"Invalid Excel file: {exc}")

    existing = {bank.name for bank in db.query(PiggyBank).filter(PiggyBank.user_id == current_user.id)}
    conflicts = existing.intersection(name for name, _ in banks.values())
    if conflicts:
        _fail("Piggy bank already exists: " + ", ".join(sorted(conflicts)))

    try:
        bank_ids = {}
        for old_id, (name, currency) in banks.items():
            bank = PiggyBank(user_id=current_user.id, name=name, currency=currency)
            db.add(bank)
            db.flush()
            bank_ids[old_id] = bank.id
        group_ids = {}
        for old_bank_id, amount, tx_type, category, description, date, group in transactions:
            if group and group not in group_ids:
                group_ids[group] = str(uuid4())
            db.add(Transaction(
                piggy_bank_id=bank_ids[old_bank_id], amount=amount, type=tx_type,
                category=category, description=description, date=date,
                transfer_group_id=group_ids.get(group),
            ))
        existing_categories = {category.name for category in db.query(Category).filter(Category.user_id == current_user.id)}
        new_categories = categories - existing_categories
        for name in new_categories:
            db.add(Category(user_id=current_user.id, name=name))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"piggy_banks_imported": len(banks), "transactions_imported": len(transactions), "categories_imported": len(new_categories)}
