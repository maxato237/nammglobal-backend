from typing import Optional
from pydantic import BaseModel


class NotificationPreferenceSchema(BaseModel):
    email_enabled: bool = True
    whatsapp_enabled: bool = True
    in_app_enabled: bool = True
    types_disabled: list[str] = []
