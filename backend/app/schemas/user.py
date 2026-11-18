from datetime import datetime
from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, EmailStr, Field, StringConstraints
from typing import Literal, Optional

# Transactions shown per page in a PiggyBank; 0 shows all.
TransactionsPerPage = Literal[10, 20, 50, 0]
# How clients show and read dates; the API itself always uses ISO 8601.
DateFormat = Literal["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    # Existing local accounts may use a reserved test domain; keep strict
    # EmailStr validation on UserCreate, not when serializing stored data.
    email: str
    is_active: bool
    transactions_per_page: int = 20
    date_format: str = "YYYY-MM-DD"
    display_currency: str = "NTD"
    net_worth_hidden: bool = False

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    transactions_per_page: Optional[TransactionsPerPage] = None
    date_format: Optional[DateFormat] = None
    display_currency: Optional[Currency] = None
    net_worth_hidden: Optional[bool] = None


class CurrencyRateUpdate(BaseModel):
    rate_to_ntd: Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=4)]


class CurrencyRateResponse(BaseModel):
    currency: str
    rate_to_ntd: float
    updated_at: datetime

    class Config:
        from_attributes = True
