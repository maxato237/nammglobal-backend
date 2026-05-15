from typing import Optional
from pydantic import BaseModel, Field


class RequestItemSchema(BaseModel):
    product_name: str = Field(min_length=1, max_length=255)
    category: Optional[str] = None
    supplier_link: Optional[str] = None
    quantity: int = Field(ge=1)
    color: Optional[str] = None
    size: Optional[str] = None
    target_price_cny: Optional[float] = None
    notes: Optional[str] = None
    position: int = 0


class RequestCreateSchema(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=8, max_length=30)
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    country_code: Optional[str] = Field(default=None, max_length=2)
    city: Optional[str] = None
    target_wave_id: Optional[str] = None
    items: list[RequestItemSchema] = Field(min_length=1)


class RequestStatusSchema(BaseModel):
    status: str
    admin_notes: Optional[str] = None
