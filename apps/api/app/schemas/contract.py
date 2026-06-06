from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


ContractStatus = Literal["draft", "active", "expired", "terminated", "completed"]


class ContractBase(BaseModel):
    document_id: str
    contract_number: str | None = Field(default=None, max_length=128)
    contract_title: str | None = Field(default=None, max_length=512)
    supplier_name: str | None = Field(default=None, max_length=255)
    sign_date: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    contract_value: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="VND", min_length=1, max_length=8)
    status: ContractStatus = "draft"
    notes: str | None = None


class ContractCreateRequest(ContractBase):
    pass


class ContractUpdateRequest(BaseModel):
    contract_number: str | None = Field(default=None, max_length=128)
    contract_title: str | None = Field(default=None, max_length=512)
    supplier_name: str | None = Field(default=None, max_length=255)
    sign_date: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    contract_value: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="VND", min_length=1, max_length=8)
    status: ContractStatus = "draft"
    notes: str | None = None


class ContractRead(BaseModel):
    id: str
    document_id: str
    document_title: str | None = None
    document_number: str | None = None
    document_status: str | None = None
    contract_number: str | None = None
    contract_title: str | None = None
    supplier_name: str | None = None
    sign_date: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    contract_value: Decimal | None = None
    currency: str
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ContractListResponse(BaseModel):
    items: list[ContractRead]
    total: int
    limit: int
    offset: int
