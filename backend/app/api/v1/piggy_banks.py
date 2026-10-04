from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.repositories.piggy_bank_repo import PiggyBankRepository
from app.domain.piggy_banks import create_piggy_bank, list_piggy_banks
from app.schemas.piggy_bank import PiggyBankCreate, PiggyBankRead
from app.api.deps import get_current_user
from app.models.user import User
from app.models.transaction import Transaction

router = APIRouter()

@router.post("", response_model=PiggyBankRead)
def create(
    payload: PiggyBankCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new PiggyBank account for the currently authenticated user.
    """
    repo = PiggyBankRepository(db)
    try:
        return create_piggy_bank(
            user_id=current_user.id,
            name=payload.name,
            currency=payload.currency,
            repo=repo,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[PiggyBankRead])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch all PiggyBank accounts owned by the currently authenticated user.
    """
    repo = PiggyBankRepository(db)
    return list_piggy_banks(current_user.id, repo)

@router.delete("/{pb_id}")
def delete_piggy_bank_api(
    pb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a specific PiggyBank account, cascading deletion to all its transactions.
    """
    repo = PiggyBankRepository(db)
    pb = repo.get_by_id(current_user.id, pb_id)
    if not pb:
        raise HTTPException(status_code=404, detail="Piggy bank not found")
    # The surviving leg becomes a standalone historical entry.
    groups = [group for (group,) in db.query(Transaction.transfer_group_id).filter(
        Transaction.piggy_bank_id == pb_id,
        Transaction.transfer_group_id.isnot(None),
    ).distinct()]
    if groups:
        db.query(Transaction).filter(
            Transaction.transfer_group_id.in_(groups),
            Transaction.piggy_bank_id != pb_id,
            Transaction.piggy_bank_id.in_(
                db.query(PiggyBank.id).filter(PiggyBank.user_id == current_user.id)
            ),
        ).update({Transaction.transfer_group_id: None}, synchronize_session=False)
    repo.delete(pb)
    return {"success": True}
