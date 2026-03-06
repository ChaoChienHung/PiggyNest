from pydantic import BaseModel

class PiggyBankCreate(BaseModel):
    name: str

class PiggyBankRead(BaseModel):
    id: int
    name: str
    user_id: int

    class Config:
        from_attributes = True
