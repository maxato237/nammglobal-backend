from typing import Optional
from pydantic import BaseModel, Field


class ShippingMethodSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    country_code: str = Field(max_length=2)
    timeframe_days_min: int = Field(ge=1)
    timeframe_days_max: int = Field(ge=1)
    price_per_kg: float = Field(ge=0)
    min_kg: Optional[float] = None
    max_kg: Optional[float] = None
    icon: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class ServiceFeeRuleSchema(BaseModel):
    country_code: str = Field(max_length=2)
    min_amount_fcfa: float = Field(ge=0)
    max_amount_fcfa: Optional[float] = None
    percentage: float = Field(ge=0, le=100)
    label: str


class PriceEstimateItemSchema(BaseModel):
    product_name: str
    quantity: int = Field(ge=1)
    unit_price_cny: float = Field(ge=0)
    weight_kg: Optional[float] = None
    category: Optional[str] = None


class PriceEstimateSchema(BaseModel):
    country_code: str = Field(max_length=2)
    shipping_method_id: Optional[int] = None
    items: list[PriceEstimateItemSchema] = Field(min_length=1)
