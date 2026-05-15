from typing import Optional
from pydantic import BaseModel, Field


class PaymentInitSchema(BaseModel):
    order_id: int
    method: str = Field(pattern="^(mtn_momo|orange_money|wave|airtel|moov|card|bank_transfer)$")
    phone_number: Optional[str] = None
    redirect_url: Optional[str] = None


class PaymentRefundSchema(BaseModel):
    reason: Optional[str] = None
