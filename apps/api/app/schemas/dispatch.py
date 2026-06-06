from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


DispatchType = Literal["incoming", "outgoing"]
DispatchStatus = Literal["draft", "registered", "processing", "completed", "archived"]


class DispatchBase(BaseModel):
    document_id: str
    dispatch_type: DispatchType
    document_number: str | None = Field(default=None, max_length=128)
    document_symbol: str | None = Field(default=None, max_length=128)
    issued_date: date | None = None
    issuing_agency: str | None = Field(default=None, max_length=255)
    recipient: str | None = None
    excerpt: str | None = None
    status: DispatchStatus = "draft"
    notes: str | None = None


class DispatchCreateRequest(DispatchBase):
    pass


class DispatchUpdateRequest(BaseModel):
    dispatch_type: DispatchType | None = None
    document_number: str | None = Field(default=None, max_length=128)
    document_symbol: str | None = Field(default=None, max_length=128)
    issued_date: date | None = None
    issuing_agency: str | None = Field(default=None, max_length=255)
    recipient: str | None = None
    excerpt: str | None = None
    status: DispatchStatus | None = None
    notes: str | None = None


class DispatchRead(BaseModel):
    id: str
    document_id: str
    document_title: str | None = None
    document_number: str | None = None
    document_status: str | None = None
    dispatch_type: str
    document_symbol: str | None = None
    issued_date: date | None = None
    issuing_agency: str | None = None
    recipient: str | None = None
    excerpt: str | None = None
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class DispatchListResponse(BaseModel):
    items: list[DispatchRead]
    total: int
    limit: int
    offset: int
