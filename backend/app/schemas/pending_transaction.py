from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.money import to_minor_units
from app.schemas.transaction import EntryType

PendingStatus = Literal["pending", "confirmed", "cancelled"]


def _validate_iso_date_optional(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return None
    from datetime import date as _date
    _date.fromisoformat(value[:10])
    return value[:10]


class PendingTransactionCreate(BaseModel):
    piggy_bank_id: int
    amount: float = Field(allow_inf_nan=False)
    type: EntryType = "expense"
    category: Optional[str] = None
    description: Optional[str] = None
    expected_date: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def valid_amount(cls, value: float) -> float:
        to_minor_units(value)
        return value

    @field_validator("expected_date")
    @classmethod
    def valid_expected_date(cls, value: Optional[str]) -> Optional[str]:
        return _validate_iso_date_optional(value)


class PendingTransactionUpdate(BaseModel):
    piggy_bank_id: Optional[int] = None
    amount: Optional[float] = Field(default=None, allow_inf_nan=False)
    type: Optional[EntryType] = None
    category: Optional[str] = None
    description: Optional[str] = None
    expected_date: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def valid_amount(cls, value: Optional[float]) -> Optional[float]:
        if value is not None:
            to_minor_units(value)
        return value

    @field_validator("expected_date")
    @classmethod
    def valid_expected_date(cls, value: Optional[str]) -> Optional[str]:
        return _validate_iso_date_optional(value)


class PendingTransactionConfirm(BaseModel):
    date: Optional[datetime] = None
    amount: Optional[float] = Field(default=None, allow_inf_nan=False)
    category: Optional[str] = None
    description: Optional[str] = None
    piggy_bank_id: Optional[int] = None

    @field_validator("amount")
    @classmethod
    def valid_amount(cls, value: Optional[float]) -> Optional[float]:
        if value is not None:
            to_minor_units(value)
        return value


class PendingTransactionRead(BaseModel):
    id: int
    piggy_bank_id: int
    piggy_bank_name: Optional[str] = None
    piggy_bank_currency: Optional[str] = None
    amount: float
    type: str
    category: Optional[str] = None
    description: Optional[str] = None
    expected_date: Optional[str] = None
    status: str
    confirmed_transaction_id: Optional[int] = None
    created_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
