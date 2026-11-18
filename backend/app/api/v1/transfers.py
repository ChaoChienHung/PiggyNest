from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4

from app.db.session import get_db
from app.models.transaction import Transaction
from app.models.piggy_bank import PiggyBank
from app.schemas.transaction import TransferCreate, TransactionRead
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("", response_model=dict)
def transfer_funds(
    payload: TransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transfer funds between two piggy banks"""
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Transfer amount must be positive")
    if payload.source_piggy_bank_id == payload.target_piggy_bank_id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same piggy bank")

    # Verify ownership of both piggy banks
    source_pb = db.query(PiggyBank).filter(
        PiggyBank.id == payload.source_piggy_bank_id, PiggyBank.user_id == current_user.id
    ).first()
    target_pb = db.query(PiggyBank).filter(
        PiggyBank.id == payload.target_piggy_bank_id, PiggyBank.user_id == current_user.id
    ).first()

    if not source_pb or not target_pb:
        raise HTTPException(status_code=404, detail="One or both piggy banks not found or not owned by user")
    cross_currency = source_pb.currency != target_pb.currency
    if cross_currency and payload.received_amount is None:
        raise HTTPException(status_code=400, detail="Received amount is required for different currencies")
    if not cross_currency and payload.received_amount is not None:
        raise HTTPException(status_code=400, detail="Received amount is only for different currencies")

    # Perform atomic transfer
    try:
        transfer_date = payload.date or datetime.utcnow()
        transfer_group_id = str(uuid4())
        # Debit source
        debit_tx = Transaction(
            piggy_bank_id=source_pb.id,
            amount=-payload.amount,
            type="transfer",
            category="Transfer Out",
            description=f"Transfer to {target_pb.name}: {payload.description}",
            date=transfer_date,
            transfer_group_id=transfer_group_id,
        )
        # Credit target
        credit_tx = Transaction(
            piggy_bank_id=target_pb.id,
            amount=payload.received_amount if cross_currency else payload.amount,
            type="transfer",
            category="Transfer In",
            description=f"Transfer from {source_pb.name}: {payload.description}",
            date=transfer_date,
            transfer_group_id=transfer_group_id,
        )

        db.add(debit_tx)
        db.add(credit_tx)
        db.commit()
        
        return {
            "success": True, 
            "transaction_id": transfer_group_id,
            "entry_ids": [debit_tx.id, credit_tx.id],
            "message": f"Successfully transferred {payload.amount} from {source_pb.name} to {target_pb.name}"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Transfer failed: {str(e)}")


@router.get("/{transfer_group_id}")
def get_transfer(
    transfer_group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return both legs of one owned PiggyBank transfer for editing."""
    pair = db.query(Transaction).join(PiggyBank).filter(
        Transaction.transfer_group_id == transfer_group_id,
        PiggyBank.user_id == current_user.id,
    ).all()
    if not pair:
        raise HTTPException(status_code=404, detail="Transfer not found")
    debit = next((leg for leg in pair if leg.amount_minor < 0), None)
    credit = next((leg for leg in pair if leg.amount_minor > 0), None)
    if len(pair) != 2 or debit is None or credit is None:
        raise HTTPException(status_code=409, detail="PiggyBank transfer entries are inconsistent")
    return {"debit": TransactionRead.model_validate(debit), "credit": TransactionRead.model_validate(credit)}
