from typing import Optional
from pydantic import BaseModel, Field


class EnrollmentSchema(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: Optional[str] = None
    whatsapp: str = Field(min_length=8, max_length=30)
    country_code: Optional[str] = Field(default=None, max_length=2)
    city: Optional[str] = None
    objective: Optional[str] = None


class SessionCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    max_seats: Optional[int] = Field(default=None, ge=1)
    whatsapp_group_link: Optional[str] = None
    status: str = Field(default="planned")


class ModuleUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content_html: Optional[str] = None
    duration_label: Optional[str] = None


class TestimonialSchema(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    country_code: Optional[str] = None
    session_label: Optional[str] = None
    content: str = Field(min_length=10)
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    is_published: bool = False
