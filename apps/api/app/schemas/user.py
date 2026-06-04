from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


UserRole = Literal["admin", "user"]


class UserRead(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[UserRead]
    total: int
    limit: int
    offset: int


class UserCreateRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = "user"
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole
    is_active: bool


class UserResetPasswordRequest(BaseModel):
    password: str = Field(min_length=8, max_length=128)
