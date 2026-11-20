from datetime import date as _date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.money import to_minor_units
from app.schemas.transaction import EntryType

RecurrenceFrequency = Literal["daily", "weekly", "monthly", "yearly"]
RecurrenceStatus = Literal["active", "paused", "stopped"]


def _validate_iso_date(value: str) -> str:
    _date.fromisoformat(value[:10])
    return value[:10]


class RecurringRuleCreate(BaseModel):
    piggy_bank_id: int
    amount: float = Field(allow_inf_nan=False)
    type: EntryType = "expense"
    category: Optional[str] = None
    description: Optional[str] = None
    frequency: RecurrenceFrequency = "monthly"
    interval: int = Field(default=1, ge=1, le=365)
    start_date: str
    end_date: Optional[str] = None
    # When attaching a rule to an already-created transaction, pass its ID so that
    # start_date is recorded as already executed instead of double-posting.
    initial_transaction_id: Optional[int] = None

    @field_validator("amount")
    @classmethod
    def valid_amount(cls, value: float) -> float:
        to_minor_units(value)
        return value

    @field_validator("start_date")
    @classmethod
    def valid_start_date(cls, value: str) -> str:
        return _validate_iso_date(value)

    @field_validator("end_date")
    @classmethod
    def valid_end_date(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return None
        return _validate_iso_date(value)


class RecurringRuleUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, allow_inf_nan=False)
    type: Optional[EntryType] = None
    category: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[RecurrenceFrequency] = None
    interval: Optional[int] = Field(default=None, ge=1, le=365)
    next_run_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[RecurrenceStatus] = None

    @field_validator("amount")
    @classmethod
    def valid_amount(cls, value: Optional[float]) -> Optional[float]:
        if value is not None:
            to_minor_units(value)
        return value

    @field_validator("next_run_date", "end_date")
    @classmethod
    def valid_optional_date(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return None
        return _validate_iso_date(value)


class RecurringRunRequest(BaseModel):
    as_of: Optional[str] = None

    @field_validator("as_of")
    @classmethod
    def valid_as_of(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return None
        return _validate_iso_date(value)


class RecurringRuleRead(BaseModel):
    id: int
    piggy_bank_id: int
    piggy_bank_name: Optional[str] = None
    piggy_bank_currency: Optional[str] = None
    amount: float
    type: str
    category: Optional[str] = None
    description: Optional[str] = None
    frequency: str
    interval: int
    start_date: str
    next_run_date: str
    end_date: Optional[str] = None
    status: str
    execution_count: int = 0
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
