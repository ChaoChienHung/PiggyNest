from pydantic import BaseModel, EmailStr, Field


class RecoveryEmail(BaseModel):
    email: EmailStr


class PasswordResetConfirm(RecoveryEmail):
    code: str = Field(pattern=r"^\d{8}$")
    new_password: str = Field(min_length=8, max_length=128)
