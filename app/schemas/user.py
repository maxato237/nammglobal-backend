from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserUpdateSchema(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = None
    whatsapp: Optional[str] = Field(default=None, max_length=30)
    city: Optional[str] = Field(default=None, max_length=100)
    country_code: Optional[str] = Field(default=None, max_length=2)


class UserRoleSchema(BaseModel):
    role: str = Field(pattern="^(client|operator|super_admin)$")


class NotificationPreferenceSchema(BaseModel):
    email_enabled: bool = True
    whatsapp_enabled: bool = True
    in_app_enabled: bool = True
    types_disabled: list[str] = []
