from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.repositories.piggy_bank_repo import PiggyBankRepository
from app.domain.piggy_banks import create_piggy_bank, list_piggy_banks
from app.schemas.piggy_bank import PiggyBankCreate, PiggyBankRead
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("", response_model=PiggyBankRead)
def create(
    payload: PiggyBankCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = PiggyBankRepository(db)
    try:
        return create_piggy_bank(
            user_id=current_user.id,
            name=payload.name,
            repo=repo,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[PiggyBankRead])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = PiggyBankRepository(db)
    return list_piggy_banks(current_user.id, repo)
