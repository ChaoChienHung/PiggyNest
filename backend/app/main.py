from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from models.piggy_bank import PiggyBank

router = APIRouter()

@router.post("/piggy_banks/")
def create_piggy_bank(name: str, db: Session = Depends(get_db)):
    pb = PiggyBank(name=name)
    db.add(pb)
    db.commit()
    db.refresh(pb)
    return pb
