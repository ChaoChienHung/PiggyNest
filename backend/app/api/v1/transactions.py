from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.db.session import get_db
from app.models.transaction import Transaction
from app.models.piggy_bank import PiggyBank
from app.schemas.transaction import TransactionCreate, TransactionRead
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

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
    """Add a new transaction to a specific piggy bank"""
    get_user_piggy_bank(db, pb_id, current_user.id)
    
    transaction = Transaction(
        piggy_bank_id=pb_id,
        amount=payload.amount,
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
    """Get transactions for a specific piggy bank"""
    get_user_piggy_bank(db, pb_id, current_user.id)
    return db.query(Transaction).filter(Transaction.piggy_bank_id == pb_id).order_by(Transaction.date.desc()).all()


@router.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a transaction"""
    transaction = db.query(Transaction).join(PiggyBank).filter(
        Transaction.id == transaction_id,
        PiggyBank.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    db.delete(transaction)
    db.commit()
    return {"success": True}


@router.get("/piggy-banks/{pb_id}/balance")
def get_balance(
    pb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current balance of a piggy bank"""
    get_user_piggy_bank(db, pb_id, current_user.id)
    total = db.query(func.sum(Transaction.amount)).filter(Transaction.piggy_bank_id == pb_id).scalar()
    count = db.query(func.count(Transaction.id)).filter(Transaction.piggy_bank_id == pb_id).scalar()
    
    return {
        "balance": float(total or 0.0),
        "transaction_count": count or 0,
    }
