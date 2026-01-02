from pydantic import BaseModel

class PiggyBankCreate(BaseModel):
    name: str


class PiggyBankRead(BaseModel):
    id: int
    account_id: int
    name: str

    class Config:
        orm_mode = True
