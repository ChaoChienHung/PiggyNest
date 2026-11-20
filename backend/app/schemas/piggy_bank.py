from pydantic import BaseModel, ConfigDict

class PiggyBankCreate(BaseModel):
    """
    Schema for validating incoming data when creating a PiggyBank.
    """
    name: str
    currency: str = "USD"

class PiggyBankPinUpdate(BaseModel):
    """Schema for pinning or unpinning a PiggyBank."""
    is_pinned: bool


class PiggyBankRead(BaseModel):
    """
    Schema for serializing a PiggyBank record back to the client.
    """
    id: int
    name: str
    currency: str
    user_id: int
    is_pinned: bool = False

    model_config = ConfigDict(from_attributes=True)
