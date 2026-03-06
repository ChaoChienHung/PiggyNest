from sqlalchemy.orm import Session
from app.models.piggy_bank import PiggyBank

class PiggyBankRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, name: str) -> PiggyBank:
        piggy_bank = PiggyBank(user_id=user_id, name=name)
        self.db.add(piggy_bank)
        self.db.commit()
        self.db.refresh(piggy_bank)
        return piggy_bank

    def list_by_user(self, user_id: int):
        return self.db.query(PiggyBank).filter(PiggyBank.user_id == user_id).all()

    def get_by_name(self, user_id: int, name: str):
        return self.db.query(PiggyBank).filter(
            PiggyBank.user_id == user_id, PiggyBank.name == name
        ).first()

    def get_by_id(self, user_id: int, pb_id: int):
        return self.db.query(PiggyBank).filter(
            PiggyBank.user_id == user_id, PiggyBank.id == pb_id
        ).first()

    def delete(self, piggy_bank: PiggyBank):
        self.db.delete(piggy_bank)
        self.db.commit()
