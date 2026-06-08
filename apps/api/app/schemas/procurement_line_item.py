from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ProcurementLineItemCreateRequest(BaseModel):
    line_number: int | None = Field(default=None, ge=1)
    item_name: str = Field(..., min_length=1, max_length=512)
    item_code: str | None = Field(default=None, max_length=64)
    unit: str | None = Field(default=None, max_length=32)
    quantity: Decimal = Field(default=Decimal("1"), ge=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    amount: Decimal | None = Field(default=None, ge=0)
    catalog_item_id: str | None = None
    notes: str | None = None


class ProcurementLineItemUpdateRequest(BaseModel):
    line_number: int | None = Field(default=None, ge=1)
    item_name: str | None = Field(default=None, min_length=1, max_length=512)
    item_code: str | None = Field(default=None, max_length=64)
    unit: str | None = Field(default=None, max_length=32)
    quantity: Decimal | None = Field(default=None, ge=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    amount: Decimal | None = Field(default=None, ge=0)
    catalog_item_id: str | None = None
    notes: str | None = None


class ProcurementLineItemRead(BaseModel):
    id: str
    procurement_id: str
    line_number: int
    item_name: str
    item_code: str | None = None
    unit: str | None = None
    quantity: Decimal
    unit_price: Decimal | None = None
    amount: Decimal | None = None
    catalog_item_id: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ProcurementLineItemListResponse(BaseModel):
    items: list[ProcurementLineItemRead]
    total: int
    lines_total_amount: Decimal | None = None
