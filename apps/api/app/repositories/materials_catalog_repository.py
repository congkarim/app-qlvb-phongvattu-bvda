from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.materials_catalog import MaterialsCatalogItem


class MaterialsCatalogRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, catalog_id: str) -> MaterialsCatalogItem | None:
        stmt = select(MaterialsCatalogItem).where(
            MaterialsCatalogItem.id == catalog_id,
            MaterialsCatalogItem.deleted_at.is_(None),
        )
        return self.db.scalar(stmt)

    def find_active_by_code(self, code: str, *, exclude_id: str | None = None) -> MaterialsCatalogItem | None:
        normalized = code.strip()
        if not normalized:
            return None
        stmt = select(MaterialsCatalogItem).where(
            MaterialsCatalogItem.deleted_at.is_(None),
            func.lower(func.trim(MaterialsCatalogItem.code)) == normalized.lower(),
        )
        if exclude_id:
            stmt = stmt.where(MaterialsCatalogItem.id != exclude_id)
        return self.db.scalar(stmt)

    def find_active_by_name(self, name: str, *, exclude_id: str | None = None) -> MaterialsCatalogItem | None:
        normalized = name.strip()
        stmt = select(MaterialsCatalogItem).where(
            MaterialsCatalogItem.deleted_at.is_(None),
            func.lower(func.trim(MaterialsCatalogItem.name)) == normalized.lower(),
        )
        if exclude_id:
            stmt = stmt.where(MaterialsCatalogItem.id != exclude_id)
        return self.db.scalar(stmt)

    def list_active(
        self,
        *,
        query: str | None = None,
        limit: int = 20,
    ) -> list[MaterialsCatalogItem]:
        stmt = (
            select(MaterialsCatalogItem)
            .where(
                MaterialsCatalogItem.deleted_at.is_(None),
                MaterialsCatalogItem.is_active.is_(True),
                *self._search_conditions(query),
            )
            .order_by(MaterialsCatalogItem.name.asc(), MaterialsCatalogItem.id.asc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def list_all(
        self,
        *,
        query: str | None = None,
        is_active: bool | None = None,
        category: str | None = None,
        limit: int,
        offset: int,
    ) -> list[MaterialsCatalogItem]:
        stmt = (
            select(MaterialsCatalogItem)
            .where(
                MaterialsCatalogItem.deleted_at.is_(None),
                *self._search_conditions(query),
                *self._filter_conditions(is_active=is_active, category=category),
            )
            .order_by(MaterialsCatalogItem.name.asc(), MaterialsCatalogItem.id.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(stmt))

    def count_all(
        self,
        *,
        query: str | None = None,
        is_active: bool | None = None,
        category: str | None = None,
    ) -> int:
        stmt = select(func.count(MaterialsCatalogItem.id)).where(
            MaterialsCatalogItem.deleted_at.is_(None),
            *self._search_conditions(query),
            *self._filter_conditions(is_active=is_active, category=category),
        )
        return int(self.db.scalar(stmt) or 0)

    def create(self, **values) -> MaterialsCatalogItem:
        item = MaterialsCatalogItem(**values)
        self.db.add(item)
        self.db.flush()
        return item

    def update(self, item: MaterialsCatalogItem, **values) -> MaterialsCatalogItem:
        for key, value in values.items():
            setattr(item, key, value)
        self.db.add(item)
        self.db.flush()
        return item

    def soft_delete(self, item: MaterialsCatalogItem) -> MaterialsCatalogItem:
        item.deleted_at = datetime.now(timezone.utc)
        self.db.add(item)
        self.db.flush()
        return item

    def _search_conditions(self, query: str | None) -> list:
        if not query:
            return []
        pattern = f"%{query.strip()}%"
        return [
            or_(
                MaterialsCatalogItem.name.ilike(pattern),
                MaterialsCatalogItem.code.ilike(pattern),
                MaterialsCatalogItem.category.ilike(pattern),
            )
        ]

    def _filter_conditions(
        self,
        *,
        is_active: bool | None,
        category: str | None,
    ) -> list:
        conditions = []
        if is_active is not None:
            conditions.append(MaterialsCatalogItem.is_active.is_(is_active))
        if category:
            conditions.append(MaterialsCatalogItem.category.ilike(f"%{category.strip()}%"))
        return conditions
