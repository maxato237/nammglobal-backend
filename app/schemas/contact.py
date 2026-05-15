from typing import Optional
from pydantic import BaseModel, Field


class ContactMessageSchema(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: Optional[str] = None
    email: Optional[str] = None
    whatsapp: Optional[str] = Field(default=None, max_length=30)
    country_code: Optional[str] = Field(default=None, max_length=2)
    subject: str = Field(pattern="^(info|order_issue|partnership|complaint|other)$")
    order_id: Optional[int] = None
    company_name: Optional[str] = None
    message: str = Field(min_length=10)


class ContactReplySchema(BaseModel):
    content: str = Field(min_length=1)
    sent_via: str = Field(default="internal", pattern="^(email|whatsapp|internal)$")
