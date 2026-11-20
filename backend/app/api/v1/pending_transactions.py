from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.domain.category_names import canonical_category
from app.domain.notifications import create_notification
from app.models.pending_transaction import PendingTransaction
from app.models.piggy_bank import PiggyBank
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.pending_transaction import (
    PendingTransactionConfirm,
    PendingTransactionCreate,
    PendingTransactionRead,
    PendingTransactionUpdate,
)
from app.schemas.transaction import TransactionRead

router = APIRouter()


def _validate_transfer_direction(tx_type: str, amount: float) -> None:
    if (tx_type == "transfer_out" and amount >= 0) or (tx_type == "transfer_in" and amount <= 0):
        raise HTTPException(
            status_code=400,
            detail="External transfer direction must match the signed amount",
        )


def _get_user_bank(db: Session, pb_id: int, user_id: int) -> PiggyBank:
    pb = db.query(PiggyBank).filter(PiggyBank.id == pb_id, PiggyBank.user_id == user_id).first()
    if pb is None:
        raise HTTPException(status_code=404, detail="Piggy bank not found or not owned by user")
    return pb


def _get_user_pending(db: Session, pending_id: int, user_id: int) -> PendingTransaction:
    item = (
        db.query(PendingTransaction)
        .filter(PendingTransaction.id == pending_id, PendingTransaction.user_id == user_id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Pending transaction not found")
    return item


def _serialize(item: PendingTransaction, bank: Optional[PiggyBank] = None) -> PendingTransactionRead:
    pb = bank or item.piggy_bank
    return PendingTransactionRead(
        id=item.id,
        piggy_bank_id=item.piggy_bank_id,
        piggy_bank_name=pb.name if pb else None,
        piggy_bank_currency=pb.currency if pb else None,
        amount=item.amount,
        type=item.type,
        category=item.category,
        description=item.description,
        expected_date=item.expected_date,
        status=item.status,
        confirmed_transaction_id=item.confirmed_transaction_id,
        created_at=item.created_at,
        confirmed_at=item.confirmed_at,
    )


@router.get("", response_model=List[PendingTransactionRead])
def list_pending_transactions(
    status: Optional[str] = Query(default="pending"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List pending ("cart") transactions owned by the authenticated user."""
    query = db.query(PendingTransaction).filter(PendingTransaction.user_id == current_user.id)
    if status and status != "all":
        query = query.filter(PendingTransaction.status == status)
    items = query.order_by(PendingTransaction.created_at.desc(), PendingTransaction.id.desc()).all()
    banks = {
        pb.id: pb
        for pb in db.query(PiggyBank).filter(PiggyBank.user_id == current_user.id).all()
    }
    return [_serialize(item, banks.get(item.piggy_bank_id)) for item in items]


@router.post("", response_model=PendingTransactionRead)
def create_pending_transaction(
    payload: PendingTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stage a pending transaction in the user's confirmation cart."""
    bank = _get_user_bank(db, payload.piggy_bank_id, current_user.id)
    _validate_transfer_direction(payload.type, payload.amount)

    item = PendingTransaction(
        user_id=current_user.id,
        piggy_bank_id=bank.id,
        type=payload.type,
        category=canonical_category(payload.category),
        description=payload.description,
        expected_date=payload.expected_date,
        status="pending",
    )
    item.amount = payload.amount
    db.add(item)
    db.flush()

    label = item.description or item.category or item.type.title()
    sign = "+" if item.amount >= 0 else "-"
    expected_line = f"Expected date: {item.expected_date}\n" if item.expected_date else "Expected date: Undecided\n"
    create_notification(
        db,
        user_id=current_user.id,
        kind="pending_created",
        title=f"Added to Pending Cart: {label}",
        body=(
            f"A delayed transaction has been staged in your Pending Cart for {bank.name}.\n\n"
            f"Amount: {sign}{abs(item.amount):.2f} {bank.currency}\n"
            f"Category: {item.category or 'Uncategorized'}\n"
            f"{expected_line}"
            f"Open your Pending Cart when the charge settles to confirm the final date and post it to your ledger."
        ),
        event_key=f"pending_created:{item.id}",
    )

    db.commit()
    db.refresh(item)
    return _serialize(item, bank)


@router.put("/{pending_id}", response_model=PendingTransactionRead)
def update_pending_transaction(
    pending_id: int,
    payload: PendingTransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Edit a pending transaction before it is confirmed."""
    item = _get_user_pending(db, pending_id, current_user.id)
    if item.status != "pending":
        raise HTTPException(status_code=400, detail="Only pending transactions can be edited")

    data = payload.model_dump(exclude_unset=True)
    if "piggy_bank_id" in data and data["piggy_bank_id"] is not None:
        _get_user_bank(db, data["piggy_bank_id"], current_user.id)
        item.piggy_bank_id = data["piggy_bank_id"]

    next_type = data.get("type", item.type)
    next_amount = data.get("amount", item.amount)
    _validate_transfer_direction(next_type, next_amount)

    if "type" in data and data["type"] is not None:
        item.type = data["type"]
    if "amount" in data and data["amount"] is not None:
        item.amount = data["amount"]
    if "category" in data:
        item.category = canonical_category(data["category"])
    if "description" in data:
        item.description = data["description"]
    if "expected_date" in data:
        item.expected_date = data["expected_date"]

    db.commit()
    db.refresh(item)
    bank = _get_user_bank(db, item.piggy_bank_id, current_user.id)
    return _serialize(item, bank)


@router.post("/{pending_id}/confirm", response_model=TransactionRead)
def confirm_pending_transaction(
    pending_id: int,
    payload: PendingTransactionConfirm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Confirm a pending transaction, atomically posting it as a real Transaction."""
    item = _get_user_pending(db, pending_id, current_user.id)
    if item.status != "pending":
        raise HTTPException(status_code=400, detail="Pending transaction is already finalized")

    target_pb_id = payload.piggy_bank_id if payload.piggy_bank_id is not None else item.piggy_bank_id
    bank = _get_user_bank(db, target_pb_id, current_user.id)

    final_amount = payload.amount if payload.amount is not None else item.amount
    _validate_transfer_direction(item.type, final_amount)

    final_category = canonical_category(payload.category) if payload.category is not None else item.category
    final_description = payload.description if payload.description is not None else item.description
    if payload.date is not None:
        final_date = payload.date
    elif item.expected_date:
        final_date = datetime.fromisoformat(f"{item.expected_date}T00:00:00")
    else:
        final_date = datetime.now(timezone.utc).replace(tzinfo=None)

    tx = Transaction(
        piggy_bank_id=bank.id,
        type=item.type,
        category=final_category,
        description=final_description,
        date=final_date,
    )
    tx.amount = final_amount
    db.add(tx)
    db.flush()

    item.piggy_bank_id = bank.id
    item.amount = final_amount
    item.category = final_category
    item.description = final_description
    item.status = "confirmed"
    item.confirmed_transaction_id = tx.id
    item.confirmed_at = datetime.now(timezone.utc)

    label = tx.description or tx.category or tx.type.title()
    sign = "+" if tx.amount >= 0 else "-"
    create_notification(
        db,
        user_id=current_user.id,
        kind="pending_confirmed",
        title=f"Payment confirmed: {label}",
        body=(
            f"Your pending transaction has been confirmed and posted to {bank.name}.\n\n"
            f"Date: {tx.date.strftime('%Y-%m-%d')}\n"
            f"Amount: {sign}{abs(tx.amount):.2f} {bank.currency}\n"
            f"Category: {tx.category or 'Uncategorized'}\n"
            f"Transaction ID: #{tx.id}"
        ),
        event_key=f"pending_confirmed:{item.id}",
    )

    db.commit()
    db.refresh(tx)
    return tx


@router.delete("/{pending_id}")
def delete_pending_transaction(
    pending_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a pending transaction from the user's cart."""
    item = _get_user_pending(db, pending_id, current_user.id)
    db.delete(item)
    db.commit()
    return {"success": True}
