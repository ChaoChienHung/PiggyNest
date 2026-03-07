from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TransactionCreate(BaseModel):
    """
    Schema for validating incoming data when creating a generic transaction.
    """
    amount: float
    type: str = 'expense'
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None

class TransactionRead(BaseModel):
    """
    Schema for serializing a Transaction record back to the client.
    """
    id: int
    piggy_bank_id: int
    amount: float
    type: str
    category: Optional[str]
    description: Optional[str]
    date: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class TransferCreate(BaseModel):
    """
    Schema for validating incoming data when transferring funds between two PiggyBanks.
    """
    source_piggy_bank_id: int
    target_piggy_bank_id: int
    amount: float
    description: Optional[str] = "Transfer"
