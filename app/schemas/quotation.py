from typing import Optional
from pydantic import BaseModel, Field


class QuotationItemSchema(BaseModel):
    request_item_id: int
    product_name: str
    quantity: int = Field(ge=1)
    weight_kg: Optional[float] = None
    category: Optional[str] = None
    unit_cost_cny: float = Field(ge=0)


class QuotationCostSchema(BaseModel):
    type: str
    label: str
    amount_fcfa: float = Field(ge=0)


class QuotationCreateSchema(BaseModel):
    request_id: int
    country_code: str = Field(max_length=2)
    items: list[QuotationItemSchema] = Field(min_length=1)
    costs: list[QuotationCostSchema] = []
    valid_until: Optional[str] = None
    admin_notes: Optional[str] = None
    client_notes: Optional[str] = None


class PartialAcceptSchema(BaseModel):
    accepted_item_ids: list[int] = Field(min_length=1)
