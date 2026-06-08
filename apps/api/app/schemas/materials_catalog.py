from datetime import datetime

from pydantic import BaseModel, Field


class MaterialsCatalogCreateRequest(BaseModel):
    code: str | None = Field(default=None, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    default_unit: str | None = Field(default=None, max_length=32)
    category: str | None = Field(default=None, max_length=128)
    description: str | None = None
    is_active: bool = True


class MaterialsCatalogUpdateRequest(BaseModel):
    code: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    default_unit: str | None = Field(default=None, max_length=32)
    category: str | None = Field(default=None, max_length=128)
    description: str | None = None
    is_active: bool | None = None


class MaterialsCatalogAutocompleteRead(BaseModel):
    id: str
    code: str | None = None
    name: str
    default_unit: str | None = None
    category: str | None = None


class MaterialsCatalogRead(BaseModel):
    id: str
    code: str | None = None
    name: str
    default_unit: str | None = None
    category: str | None = None
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MaterialsCatalogListResponse(BaseModel):
    items: list[MaterialsCatalogRead]
    total: int
    limit: int
    offset: int
