from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TransactionCreate(BaseModel):
    amount: float
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None

class TransactionRead(BaseModel):
    id: int
    piggy_bank_id: int
    amount: float
    category: Optional[str]
    description: Optional[str]
    date: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class TransferCreate(BaseModel):
    source_piggy_bank_id: int
    target_piggy_bank_id: int
    amount: float
    description: Optional[str] = "Transfer"
