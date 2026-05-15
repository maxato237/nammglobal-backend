from typing import Optional
from pydantic import BaseModel, Field


class OrderStatusSchema(BaseModel):
    status: str
    note: Optional[str] = None


class OrderEventSchema(BaseModel):
    title: str = Field(min_length=1)
    description: Optional[str] = None
    location: Optional[str] = None
    is_public: bool = True


class OrderMessageSchema(BaseModel):
    content: str = Field(min_length=1)
    attachment_url: Optional[str] = None


class BulkStatusSchema(BaseModel):
    wave_id: str
    status: str
