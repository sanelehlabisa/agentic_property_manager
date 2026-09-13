from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    name: str
    role: UserRole


class EmailAuthRequest(BaseModel):
    email: EmailStr
    name: str | None = Field(default=None, min_length=2, max_length=150)
    role: UserRole | None = None


class AuthResponse(BaseModel):
    requires_onboarding: bool
    token: str | None = None
    user: UserRead | None = None


class SessionResponse(BaseModel):
    authenticated: Literal[True] = True
    user: UserRead
