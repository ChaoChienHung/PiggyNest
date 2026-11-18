from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.db.session import get_db
from app.models.transaction import Transaction
from app.models.piggy_bank import PiggyBank
from app.schemas.transaction import TransactionCreate, TransactionRead, TransactionUpdate
from app.api.deps import get_current_user
from app.models.user import User
from app.domain.transfer_links import legacy_transfer_pairs

router = APIRouter()


def get_user_transaction(db: Session, transaction_id: int, user_id: int):
    transaction = db.query(Transaction).join(PiggyBank).filter(
        Transaction.id == transaction_id, PiggyBank.user_id == user_id,
    ).first()
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

def get_user_piggy_bank(db: Session, pb_id: int, user_id: int):
    pb = db.query(PiggyBank).filter(
        PiggyBank.id == pb_id, PiggyBank.user_id == user_id
    ).first()
    if not pb:
        raise HTTPException(status_code=404, detail="Piggy bank not found or not owned by user")
    return pb

@router.post("/piggy-banks/{pb_id}/transactions", response_model=TransactionRead)
def add_transaction(
    pb_id: int,
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a new localized financial transaction (expense, deposit, income) 
    to a specific PiggyBank owned by the user.
    """
    get_user_piggy_bank(db, pb_id, current_user.id)
    if payload.type == "transfer":
        raise HTTPException(status_code=400, detail="Use /transfers to create both transfer entries")
    if ((payload.type == "transfer_out" and payload.amount >= 0)
            or (payload.type == "transfer_in" and payload.amount <= 0)):
        raise HTTPException(status_code=400, detail="External transfer direction must match the signed amount")
    
    transaction = Transaction(
        piggy_bank_id=pb_id,
        amount=payload.amount,
        type=payload.type,
        category=payload.category,
        description=payload.description,
    )
    if payload.date:
        transaction.date = payload.date

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/piggy-banks/{pb_id}/transactions", response_model=List[TransactionRead])
def get_transactions(
    pb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all transactions (ordered chronologically descending) 
    for a specific PiggyBank owned by the user.
    """
    get_user_piggy_bank(db, pb_id, current_user.id)
    return db.query(Transaction).filter(Transaction.piggy_bank_id == pb_id).order_by(Transaction.date.desc()).all()


@router.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a specific transaction belonging to any nested PiggyBank owned by the User.
    """
    transaction = get_user_transaction(db, transaction_id, current_user.id)
    if transaction.transfer_group_id:
        pair = db.query(Transaction).join(PiggyBank).filter(
            Transaction.transfer_group_id == transaction.transfer_group_id,
            PiggyBank.user_id == current_user.id,
        ).all()
        for leg in pair:
            db.delete(leg)
    elif transaction.type == "transfer":
        banks = db.query(PiggyBank).filter(PiggyBank.user_id == current_user.id).all()
        transactions = db.query(Transaction).filter(
            Transaction.piggy_bank_id.in_([bank.id for bank in banks])
        ).all()
        counterpart_id = legacy_transfer_pairs(transactions, banks).get(transaction.id)
        if counterpart_id is None:
            raise HTTPException(status_code=409, detail="Legacy transfer has no unique pair; repair its transaction ID before deleting")
        db.delete(db.get(Transaction, counterpart_id))
        db.delete(transaction)
    else:
        db.delete(transaction)
    db.commit()
    return {"success": True}


@router.get("/transactions/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch one transaction by its numeric ID for the authenticated user."""
    return get_user_transaction(db, transaction_id, current_user.id)


@router.get("/piggy-banks/{pb_id}/balance")
def get_balance(
    pb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dynamically calculate and return the summation of all transactions 
    to determine the active numeric balance of a PiggyBank.
    """
    get_user_piggy_bank(db, pb_id, current_user.id)
    total = db.query(func.sum(Transaction.amount)).filter(Transaction.piggy_bank_id == pb_id).scalar()
    count = db.query(func.count(Transaction.id)).filter(Transaction.piggy_bank_id == pb_id).scalar()
    
    return {
        "balance": float(total or 0.0),
        "transaction_count": count or 0,
    }

@router.put("/transactions/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a specific transaction belonging to any nested PiggyBank owned by the User.
    """
    transaction = get_user_transaction(db, transaction_id, current_user.id)
    if transaction.transfer_group_id:
        pair = db.query(Transaction).join(PiggyBank).filter(
            Transaction.transfer_group_id == transaction.transfer_group_id,
            PiggyBank.user_id == current_user.id,
        ).all()
        debit = next((leg for leg in pair if leg.amount < 0), None)
        credit = next((leg for leg in pair if leg.amount > 0), None)
        if (len(pair) != 2 or debit is None or credit is None
                or debit.type != "transfer" or credit.type != "transfer"
                or debit.piggy_bank_id == credit.piggy_bank_id
                or abs(debit.amount + credit.amount) > 1e-8):
            raise HTTPException(status_code=409, detail="PiggyBank transfer entries are inconsistent")
        if payload.type is not None or "category" in payload.model_fields_set:
            raise HTTPException(status_code=400, detail="PiggyBank transfer type and directional categories cannot be changed")
        if payload.amount is not None:
            if payload.amount == 0 or (payload.amount > 0) != (transaction.amount > 0):
                raise HTTPException(status_code=400, detail="Amount must keep this transfer entry's direction")
            debit.amount = -abs(payload.amount)
            credit.amount = abs(payload.amount)
        if "description" in payload.model_fields_set:
            note = payload.description or ""
            debit.description = f"Transfer to {credit.piggy_bank.name}: {note}"
            credit.description = f"Transfer from {debit.piggy_bank.name}: {note}"
        if payload.date is not None:
            debit.date = payload.date
            credit.date = payload.date
        db.commit()
        db.refresh(transaction)
        return transaction
    if transaction.type == "transfer":
        raise HTTPException(status_code=409, detail="Repair this historical transfer before editing")
    updated_type = payload.type or transaction.type
    updated_amount = payload.amount if payload.amount is not None else transaction.amount
    if ((updated_type == "transfer_out" and updated_amount >= 0)
            or (updated_type == "transfer_in" and updated_amount <= 0)):
        raise HTTPException(status_code=400, detail="External transfer direction must match the signed amount")
        
    if payload.amount is not None:
        # If type is expense but amount is positive, or vice versa, let's keep consistency.
        # But normally the frontend sends negative for expense and positive for income.
        # Let's trust the frontend's raw amount.
        transaction.amount = payload.amount
    if payload.type is not None:
        transaction.type = payload.type
    if "category" in payload.model_fields_set:
        transaction.category = payload.category
    if "description" in payload.model_fields_set:
        transaction.description = payload.description
    if payload.date is not None:
        transaction.date = payload.date
        
    db.commit()
    db.refresh(transaction)
    return transaction
