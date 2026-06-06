from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


CatalogType = Literal["business_type", "document_type"]


class DepartmentRead(BaseModel):
    id: str
    code: str | None = None
    name: str
    description: str | None = None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DepartmentCreateRequest(BaseModel):
    code: str | None = Field(default=None, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    sort_order: int = 0
    is_active: bool = True


class DepartmentUpdateRequest(BaseModel):
    code: str | None = Field(default=None, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    sort_order: int = 0
    is_active: bool = True


class CatalogItemRead(BaseModel):
    id: str
    catalog_type: str
    code: str
    label: str
    description: str | None = None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CatalogItemCreateRequest(BaseModel):
    catalog_type: CatalogType
    code: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=255)
    description: str | None = None
    sort_order: int = 0
    is_active: bool = True


class CatalogItemUpdateRequest(BaseModel):
    catalog_type: CatalogType
    code: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=255)
    description: str | None = None
    sort_order: int = 0
    is_active: bool = True
