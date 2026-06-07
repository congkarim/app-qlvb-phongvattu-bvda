from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


ProcurementKind = Literal["proposal", "plan", "acceptance"]
ProcurementStatus = Literal["draft", "submitted", "approved", "rejected", "completed", "archived"]


class ProcurementBase(BaseModel):
    document_id: str
    procurement_kind: ProcurementKind
    reference_number: str | None = Field(default=None, max_length=128)
    title_summary: str | None = None
    requesting_unit: str | None = Field(default=None, max_length=255)
    estimated_value: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="VND", max_length=8)
    requested_date: date | None = None
    status: ProcurementStatus = "draft"
    notes: str | None = None


class ProcurementCreateRequest(ProcurementBase):
    pass


class ProcurementUpdateRequest(BaseModel):
    procurement_kind: ProcurementKind | None = None
    reference_number: str | None = Field(default=None, max_length=128)
    title_summary: str | None = None
    requesting_unit: str | None = Field(default=None, max_length=255)
    estimated_value: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=8)
    requested_date: date | None = None
    status: ProcurementStatus | None = None
    notes: str | None = None


class ProcurementRead(BaseModel):
    id: str
    document_id: str
    document_title: str | None = None
    document_number: str | None = None
    document_status: str | None = None
    procurement_kind: str
    reference_number: str | None = None
    title_summary: str | None = None
    requesting_unit: str | None = None
    estimated_value: Decimal | None = None
    currency: str
    requested_date: date | None = None
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ProcurementListResponse(BaseModel):
    items: list[ProcurementRead]
    total: int
    limit: int
    offset: int
