from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.materials_catalog import MaterialsCatalogItem
from app.models.stock_movement import StockMovement
from app.models.user import User


class StockMovementRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, movement_id: str) -> StockMovement | None:
        stmt = (
            select(StockMovement)
            .options(
                joinedload(StockMovement.catalog_item),
                joinedload(StockMovement.created_by),
            )
            .where(
                StockMovement.id == movement_id,
                StockMovement.deleted_at.is_(None),
            )
        )
        return self.db.scalar(stmt)

    def list_movements(
        self,
        *,
        movement_type: str | None = None,
        catalog_item_id: str | None = None,
        query: str | None = None,
        reference_number: str | None = None,
        movement_date_from: date | None = None,
        movement_date_to: date | None = None,
        limit: int,
        offset: int,
    ) -> list[StockMovement]:
        stmt = (
            select(StockMovement)
            .join(StockMovement.catalog_item)
            .options(
                joinedload(StockMovement.catalog_item),
                joinedload(StockMovement.created_by),
            )
            .where(
                StockMovement.deleted_at.is_(None),
                *self._filter_conditions(
                    movement_type=movement_type,
                    catalog_item_id=catalog_item_id,
                    query=query,
                    reference_number=reference_number,
                    movement_date_from=movement_date_from,
                    movement_date_to=movement_date_to,
                ),
            )
            .order_by(StockMovement.movement_date.desc(), StockMovement.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(stmt).unique())

    def count_movements(
        self,
        *,
        movement_type: str | None = None,
        catalog_item_id: str | None = None,
        query: str | None = None,
        reference_number: str | None = None,
        movement_date_from: date | None = None,
        movement_date_to: date | None = None,
    ) -> int:
        stmt = (
            select(func.count(StockMovement.id))
            .join(StockMovement.catalog_item)
            .where(
                StockMovement.deleted_at.is_(None),
                *self._filter_conditions(
                    movement_type=movement_type,
                    catalog_item_id=catalog_item_id,
                    query=query,
                    reference_number=reference_number,
                    movement_date_from=movement_date_from,
                    movement_date_to=movement_date_to,
                ),
            )
        )
        return int(self.db.scalar(stmt) or 0)

    def create(self, **values) -> StockMovement:
        movement = StockMovement(**values)
        self.db.add(movement)
        self.db.flush()
        return movement

    def soft_delete(self, movement: StockMovement) -> StockMovement:
        from datetime import datetime, timezone

        movement.deleted_at = datetime.now(timezone.utc)
        self.db.add(movement)
        self.db.flush()
        return movement

    def _filter_conditions(
        self,
        *,
        movement_type: str | None,
        catalog_item_id: str | None,
        query: str | None,
        reference_number: str | None,
        movement_date_from: date | None,
        movement_date_to: date | None,
    ) -> list:
        conditions = []
        if movement_type:
            conditions.append(StockMovement.movement_type == movement_type)
        if catalog_item_id:
            conditions.append(StockMovement.catalog_item_id == catalog_item_id)
        if reference_number:
            pattern = f"%{reference_number.strip()}%"
            conditions.append(StockMovement.reference_number.ilike(pattern))
        if movement_date_from:
            conditions.append(StockMovement.movement_date >= movement_date_from)
        if movement_date_to:
            conditions.append(StockMovement.movement_date <= movement_date_to)
        if query:
            pattern = f"%{query.strip()}%"
            conditions.append(
                or_(
                    MaterialsCatalogItem.name.ilike(pattern),
                    MaterialsCatalogItem.code.ilike(pattern),
                    StockMovement.reference_number.ilike(pattern),
                )
            )
        return conditions
