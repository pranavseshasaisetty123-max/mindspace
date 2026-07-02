import re
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserRegister(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate that the password is strong enough (contains letters and numbers)."""
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v

class UserLogin(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
