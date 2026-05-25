from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ── ShippingMethod ─────────────────────────────────────────────

class ShippingMethodCreateIn(BaseModel):
    name:               str   = Field(min_length=1, max_length=100)
    country_code:       str   = Field(min_length=2, max_length=2)
    timeframe_days_min: int   = Field(ge=1)
    timeframe_days_max: int   = Field(ge=1)
    price_per_kg:       float = Field(ge=0)
    min_kg:             Optional[float] = None
    max_kg:             Optional[float] = None
    icon:               Optional[str]   = None
    is_active:          bool  = True
    sort_order:         int   = 0

    @field_validator("country_code")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.upper()


class ShippingMethodUpdateIn(BaseModel):
    name:               Optional[str]   = None
    timeframe_days_min: Optional[int]   = Field(default=None, ge=1)
    timeframe_days_max: Optional[int]   = Field(default=None, ge=1)
    price_per_kg:       Optional[float] = Field(default=None, ge=0)
    min_kg:             Optional[float] = None
    max_kg:             Optional[float] = None
    icon:               Optional[str]   = None
    is_active:          Optional[bool]  = None
    sort_order:         Optional[int]   = None


# ── ServiceFeeRule ─────────────────────────────────────────────

class ServiceFeeRuleCreateIn(BaseModel):
    country_code:    str   = Field(min_length=2, max_length=2)
    min_amount_fcfa: float = Field(ge=0)
    max_amount_fcfa: Optional[float] = None
    percentage:      float = Field(ge=0, le=100)
    label:           str

    @field_validator("country_code")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.upper()


class ServiceFeeRuleUpdateIn(BaseModel):
    min_amount_fcfa: Optional[float] = Field(default=None, ge=0)
    max_amount_fcfa: Optional[float] = None
    percentage:      Optional[float] = Field(default=None, ge=0, le=100)
    label:           Optional[str]   = None


# ── ProductCategoryRule ────────────────────────────────────────

class ProductCategoryRuleCreateIn(BaseModel):
    country_code:    str   = Field(min_length=2, max_length=2)
    category_name:   str   = Field(min_length=1, max_length=100)
    surcharge_per_kg: Optional[float] = None
    surcharge_type:  str   = Field(default="none", pattern="^(per_kg|fixed|none)$")
    customs_rate_pct: Optional[float] = Field(default=None, ge=0, le=100)
    note:            Optional[str]   = None
    icon:            Optional[str]   = None

    @field_validator("country_code")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.upper()


class ProductCategoryRuleUpdateIn(BaseModel):
    category_name:   Optional[str]   = None
    surcharge_per_kg: Optional[float] = None
    surcharge_type:  Optional[str]   = Field(default=None, pattern="^(per_kg|fixed|none)$")
    customs_rate_pct: Optional[float] = Field(default=None, ge=0, le=100)
    note:            Optional[str]   = None
    icon:            Optional[str]   = None


# ── CustomsRule ────────────────────────────────────────────────

class CustomsRuleCreateIn(BaseModel):
    country_code:         str   = Field(min_length=2, max_length=2)
    threshold_amount_fcfa: float = Field(ge=0)
    rate_pct:             float = Field(ge=0, le=100)
    note:                 Optional[str] = None

    @field_validator("country_code")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.upper()


class CustomsRuleUpdateIn(BaseModel):
    threshold_amount_fcfa: Optional[float] = Field(default=None, ge=0)
    rate_pct:              Optional[float] = Field(default=None, ge=0, le=100)
    note:                  Optional[str]   = None


# ── ExchangeRate ───────────────────────────────────────────────

class ExchangeRateCreateIn(BaseModel):
    from_currency: str   = Field(min_length=2, max_length=10)
    to_currency:   str   = Field(min_length=2, max_length=10)
    rate:          float = Field(gt=0)

    @field_validator("from_currency", "to_currency")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.upper()


# ── Quote estimate ─────────────────────────────────────────────

class QuoteItemIn(BaseModel):
    product_name:  str   = Field(min_length=1)
    quantity:      int   = Field(ge=1)
    unit_cost_cny: float = Field(ge=0)
    weight_kg:     float = Field(ge=0)
    category:      Optional[str] = None


class QuoteEstimateIn(BaseModel):
    country_code:       str  = Field(min_length=2, max_length=2)
    shipping_method_id: Optional[int]          = None
    items:              list[QuoteItemIn]       = Field(min_length=1)

    @field_validator("country_code")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.upper()
