from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class RegisterSchema(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=8, max_length=30)
    password: str = Field(min_length=6)
    email: Optional[EmailStr] = None
    whatsapp: Optional[str] = Field(default=None, max_length=30)
    country: Optional[str] = Field(default=None, max_length=2)
    city: Optional[str] = Field(default=None, max_length=100)


class LoginSchema(BaseModel):
    phone: str
    password: str
    remember: bool = False


class OTPRequestSchema(BaseModel):
    phone: str
    channel: str = "whatsapp"


class OTPVerifySchema(BaseModel):
    phone: str
    otp_code: str


class PasswordResetSchema(BaseModel):
    reset_token: str
    new_password: str = Field(min_length=6)


class PasswordChangeSchema(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6)
