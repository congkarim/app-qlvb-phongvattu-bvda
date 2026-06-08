from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.procurement import ProcurementRecord
from app.models.procurement_line_item import ProcurementLineItem


class ProcurementLineItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, line_item_id: str) -> ProcurementLineItem | None:
        stmt = select(ProcurementLineItem).where(
            ProcurementLineItem.id == line_item_id,
            ProcurementLineItem.deleted_at.is_(None),
        )
        return self.db.scalar(stmt)

    def get_procurement(self, procurement_id: str) -> ProcurementRecord | None:
        stmt = select(ProcurementRecord).where(
            ProcurementRecord.id == procurement_id,
            ProcurementRecord.deleted_at.is_(None),
        )
        return self.db.scalar(stmt)

    def list_by_procurement_id(self, procurement_id: str) -> list[ProcurementLineItem]:
        stmt = (
            select(ProcurementLineItem)
            .where(
                ProcurementLineItem.procurement_id == procurement_id,
                ProcurementLineItem.deleted_at.is_(None),
            )
            .order_by(ProcurementLineItem.line_number.asc(), ProcurementLineItem.id.asc())
        )
        return list(self.db.scalars(stmt))

    def count_by_procurement_id(self, procurement_id: str) -> int:
        stmt = select(func.count(ProcurementLineItem.id)).where(
            ProcurementLineItem.procurement_id == procurement_id,
            ProcurementLineItem.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0)

    def get_max_line_number(self, procurement_id: str) -> int:
        stmt = select(func.max(ProcurementLineItem.line_number)).where(
            ProcurementLineItem.procurement_id == procurement_id,
            ProcurementLineItem.deleted_at.is_(None),
        )
        value = self.db.scalar(stmt)
        return int(value or 0)

    def sum_amount_by_procurement_id(self, procurement_id: str) -> Decimal | None:
        stmt = select(func.sum(ProcurementLineItem.amount)).where(
            ProcurementLineItem.procurement_id == procurement_id,
            ProcurementLineItem.deleted_at.is_(None),
            ProcurementLineItem.amount.is_not(None),
        )
        value = self.db.scalar(stmt)
        if value is None:
            return None
        return Decimal(value)

    def create(self, **values) -> ProcurementLineItem:
        item = ProcurementLineItem(**values)
        self.db.add(item)
        self.db.flush()
        return item

    def update(self, item: ProcurementLineItem, **values) -> ProcurementLineItem:
        for key, value in values.items():
            setattr(item, key, value)
        self.db.add(item)
        self.db.flush()
        return item

    def soft_delete(self, item: ProcurementLineItem) -> ProcurementLineItem:
        item.deleted_at = datetime.now(timezone.utc)
        self.db.add(item)
        self.db.flush()
        return item
