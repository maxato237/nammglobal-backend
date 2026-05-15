from typing import Optional
from pydantic import BaseModel, Field


class WaveCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    country_code: Optional[str] = Field(default=None, max_length=2)
    deadline_date: Optional[str] = None
    shipping_date: Optional[str] = None
    arrival_date_min: Optional[str] = None
    arrival_date_max: Optional[str] = None
    transport_type: Optional[str] = Field(default=None, max_length=100)
    capacity_kg: Optional[float] = None
    notes: Optional[str] = None


class WaveStatusSchema(BaseModel):
    status: str = Field(pattern="^(planned|open|closed|in_transit|delivered|cancelled)$")
