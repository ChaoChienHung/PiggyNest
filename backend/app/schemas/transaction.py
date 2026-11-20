from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import List, Optional, Literal
from app.core.money import to_minor_units

EntryType = Literal['expense', 'income', 'withdrawal', 'deposit', 'transfer_out', 'transfer_in']

class TransactionCreate(BaseModel):
    """
    Schema for validating incoming data when creating a generic transaction.
    """
    amount: float = Field(allow_inf_nan=False)
    type: EntryType = 'expense'
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None

    @field_validator("amount")
    @classmethod
    def valid_amount(cls, value):
        to_minor_units(value)
        return value

class TransactionRead(BaseModel):
    """
    Schema for serializing a Transaction record back to the client.
    """
    id: int
    transaction_id: str
    piggy_bank_id: int
    amount: float = Field(allow_inf_nan=False)
    type: str
    category: Optional[str]
    description: Optional[str]
    date: datetime
    created_at: datetime
    recurring_rule_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class TransferCreate(BaseModel):
    """
    Schema for validating incoming data when transferring funds between two PiggyBanks.
    """
    source_piggy_bank_id: int
    target_piggy_bank_id: int
    amount: float = Field(gt=0, allow_inf_nan=False)
    received_amount: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    description: Optional[str] = "Transfer"
    date: Optional[datetime] = None

    @field_validator("amount", "received_amount")
    @classmethod
    def valid_amount(cls, value):
        if value is not None:
            to_minor_units(value)
        return value

class TransactionUpdate(BaseModel):
    """
    Schema for validating incoming data when updating a transaction.
    """
    amount: Optional[float] = Field(default=None, allow_inf_nan=False)
    counterpart_amount: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    type: Optional[EntryType] = None
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None

    @field_validator("amount", "counterpart_amount")
    @classmethod
    def valid_amount(cls, value):
        if value is not None:
            to_minor_units(value)
        return value


class BulkCategoryUpdateRequest(BaseModel):
    """Schema for updating the category of multiple transactions at once."""
    transaction_ids: List[int] = Field(min_length=1)
    category: Optional[str] = None


class BulkDeleteRequest(BaseModel):
    """Schema for deleting multiple transactions at once."""
    transaction_ids: List[int] = Field(min_length=1)
