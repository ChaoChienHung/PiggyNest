from pydantic import BaseModel

class PiggyBankCreate(BaseModel):
    """
    Schema for validating incoming data when creating a PiggyBank.
    """
    name: str
    currency: str = "USD"

class PiggyBankRead(BaseModel):
    """
    Schema for serializing a PiggyBank record back to the client.
    """
    id: int
    name: str
    currency: str
    user_id: int

    class Config:
        from_attributes = True
