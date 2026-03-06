"""Pydantic schemas for authentication."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class RegisterPayload(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = Field(default="viewer")
    organization_id: Optional[int] = None
    language: str = Field(default="en", max_length=5)  # Preferred language


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshPayload(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    name: str
    username: str
    email: str
    role: str
    organization_id: Optional[int] = None
    language: str = "en"
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
