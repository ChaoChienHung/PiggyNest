from pydantic import BaseModel, EmailStr
from typing import Literal, Optional

# Transactions shown per page in a PiggyBank; 0 shows all.
TransactionsPerPage = Literal[10, 20, 50, 0]
# How clients show and read dates; the API itself always uses ISO 8601.
DateFormat = Literal["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"]

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

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    transactions_per_page: Optional[TransactionsPerPage] = None
    date_format: Optional[DateFormat] = None
