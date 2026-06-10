from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class StockMovementCreateRequest(BaseModel):
    catalog_item_id: str
    movement_type: str = Field(..., pattern="^(in|out)$")
    quantity: Decimal = Field(..., gt=0)
    movement_date: date
    notes: str | None = None
    reference_number: str | None = Field(default=None, max_length=128)
    procurement_id: str | None = None


class StockMovementRead(BaseModel):
    id: str
    catalog_item_id: str
    catalog_item_code: str | None = None
    catalog_item_name: str
    catalog_item_unit: str | None = None
    movement_type: str
    quantity: Decimal
    movement_date: date
    notes: str | None = None
    reference_number: str | None = None
    procurement_id: str | None = None
    balance_after: Decimal
    created_by_user_id: str
    created_by_email: str | None = None
    created_at: datetime
    updated_at: datetime


class StockMovementListResponse(BaseModel):
    items: list[StockMovementRead]
    total: int
    limit: int
    offset: int


class StockBalanceRead(BaseModel):
    catalog_item_id: str
    catalog_item_code: str | None = None
    catalog_item_name: str
    catalog_item_unit: str | None = None
    quantity: Decimal
    min_stock_level: Decimal | None = None
    is_below_min: bool = False


class LowStockListResponse(BaseModel):
    items: list[StockBalanceRead]
    total: int
