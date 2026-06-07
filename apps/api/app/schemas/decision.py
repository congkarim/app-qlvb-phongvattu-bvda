from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


DecisionKind = Literal["decision", "notification"]
DecisionStatus = Literal["draft", "registered", "effective", "expired", "revoked", "archived"]


class DecisionBase(BaseModel):
    document_id: str
    decision_kind: DecisionKind
    document_number: str | None = Field(default=None, max_length=128)
    document_symbol: str | None = Field(default=None, max_length=128)
    issued_date: date | None = None
    issuing_agency: str | None = Field(default=None, max_length=255)
    excerpt: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    status: DecisionStatus = "draft"
    notes: str | None = None


class DecisionCreateRequest(DecisionBase):
    pass


class DecisionUpdateRequest(BaseModel):
    decision_kind: DecisionKind | None = None
    document_number: str | None = Field(default=None, max_length=128)
    document_symbol: str | None = Field(default=None, max_length=128)
    issued_date: date | None = None
    issuing_agency: str | None = Field(default=None, max_length=255)
    excerpt: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    status: DecisionStatus | None = None
    notes: str | None = None


class DecisionRead(BaseModel):
    id: str
    document_id: str
    document_title: str | None = None
    document_type: str | None = None
    document_status: str | None = None
    decision_kind: str
    document_number: str | None = None
    document_symbol: str | None = None
    issued_date: date | None = None
    issuing_agency: str | None = None
    excerpt: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class DecisionListResponse(BaseModel):
    items: list[DecisionRead]
    total: int
    limit: int
    offset: int
