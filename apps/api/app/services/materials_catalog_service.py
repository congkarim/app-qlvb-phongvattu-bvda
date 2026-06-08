from typing import Any

from sqlalchemy.orm import Session

from app.models.materials_catalog import MaterialsCatalogItem
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.materials_catalog_repository import MaterialsCatalogRepository


class MaterialsCatalogNotFoundError(ValueError):
    pass


class MaterialsCatalogAlreadyExistsError(ValueError):
    pass


class MaterialsCatalogOperationError(ValueError):
    pass


class MaterialsCatalogService:
    def __init__(self, db: Session):
        self.db = db
        self.catalog = MaterialsCatalogRepository(db)
        self.audit_logs = AuditLogRepository(db)

    def list_active(self, *, query: str | None, limit: int) -> list[dict[str, Any]]:
        items = self.catalog.list_active(query=self._normalize_text(query), limit=limit)
        return [self._autocomplete_read(item) for item in items]

    def list_all(
        self,
        *,
        query: str | None,
        is_active: bool | None,
        category: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        normalized_query = self._normalize_text(query)
        normalized_category = self._normalize_text(category)
        items = self.catalog.list_all(
            query=normalized_query,
            is_active=is_active,
            category=normalized_category,
            limit=limit,
            offset=offset,
        )
        total = self.catalog.count_all(
            query=normalized_query,
            is_active=is_active,
            category=normalized_category,
        )
        return [self._read(item) for item in items], total

    def get_catalog_item(self, catalog_id: str) -> dict[str, Any]:
        return self._read(self._get_item(catalog_id))

    def create_catalog_item(self, *, values: dict[str, Any], actor: User) -> dict[str, Any]:
        payload = self._clean_values(values, for_create=True)
        self._ensure_unique(code=payload.get("code"), name=payload["name"])
        item = self.catalog.create(**payload)
        self.audit_logs.create(
            action="materials_catalog.created",
            entity_type="materials_catalog",
            entity_id=item.id,
            actor_user_id=actor.id,
            metadata={"code": item.code, "name": item.name},
        )
        self.db.commit()
        self.db.refresh(item)
        return self._read(item)

    def update_catalog_item(
        self,
        *,
        catalog_id: str,
        values: dict[str, Any],
        actor: User,
    ) -> dict[str, Any]:
        item = self._get_item(catalog_id)
        old_values = self._audit_snapshot(item)
        payload = self._clean_values(values, for_create=False)
        code = payload.get("code", item.code)
        name = payload.get("name", item.name)
        self._ensure_unique(code=code, name=name, exclude_id=item.id)
        item = self.catalog.update(item, **payload)
        self.audit_logs.create(
            action="materials_catalog.updated",
            entity_type="materials_catalog",
            entity_id=item.id,
            actor_user_id=actor.id,
            metadata={"old": old_values, "new": self._audit_snapshot(item)},
        )
        self.db.commit()
        self.db.refresh(item)
        return self._read(item)

    def delete_catalog_item(self, *, catalog_id: str, actor: User) -> dict[str, Any]:
        item = self._get_item(catalog_id)
        item = self.catalog.soft_delete(item)
        self.audit_logs.create(
            action="materials_catalog.deleted",
            entity_type="materials_catalog",
            entity_id=item.id,
            actor_user_id=actor.id,
            metadata={"code": item.code, "name": item.name},
        )
        self.db.commit()
        self.db.refresh(item)
        return self._read(item)

    def ensure_catalog_reference(self, catalog_item_id: str | None) -> None:
        if catalog_item_id is None:
            return
        item = self.catalog.get_by_id(catalog_item_id)
        if item is None:
            raise MaterialsCatalogNotFoundError("Materials catalog item not found")

    def _get_item(self, catalog_id: str) -> MaterialsCatalogItem:
        item = self.catalog.get_by_id(catalog_id)
        if item is None:
            raise MaterialsCatalogNotFoundError("Materials catalog item not found")
        return item

    def _ensure_unique(
        self,
        *,
        code: str | None,
        name: str,
        exclude_id: str | None = None,
    ) -> None:
        if code and self.catalog.find_active_by_code(code, exclude_id=exclude_id):
            raise MaterialsCatalogAlreadyExistsError("Materials catalog code already exists")
        if self.catalog.find_active_by_name(name, exclude_id=exclude_id):
            raise MaterialsCatalogAlreadyExistsError("Materials catalog name already exists")

    def _clean_values(self, values: dict[str, Any], *, for_create: bool) -> dict[str, Any]:
        if for_create:
            name = self._normalize_required(values.get("name"), "name")
            return {
                "code": self._normalize_text(values.get("code")),
                "name": name,
                "default_unit": self._normalize_text(values.get("default_unit")),
                "category": self._normalize_text(values.get("category")),
                "description": self._normalize_text(values.get("description")),
                "is_active": bool(values.get("is_active", True)),
            }

        cleaned: dict[str, Any] = {}
        if "code" in values:
            cleaned["code"] = self._normalize_text(values.get("code"))
        if "name" in values:
            cleaned["name"] = self._normalize_required(values.get("name"), "name")
        if "default_unit" in values:
            cleaned["default_unit"] = self._normalize_text(values.get("default_unit"))
        if "category" in values:
            cleaned["category"] = self._normalize_text(values.get("category"))
        if "description" in values:
            cleaned["description"] = self._normalize_text(values.get("description"))
        if "is_active" in values and values.get("is_active") is not None:
            cleaned["is_active"] = bool(values.get("is_active"))
        return cleaned

    def _read(self, item: MaterialsCatalogItem) -> dict[str, Any]:
        return {
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "default_unit": item.default_unit,
            "category": item.category,
            "description": item.description,
            "is_active": item.is_active,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }

    def _autocomplete_read(self, item: MaterialsCatalogItem) -> dict[str, Any]:
        return {
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "default_unit": item.default_unit,
            "category": item.category,
        }

    def _audit_snapshot(self, item: MaterialsCatalogItem) -> dict[str, Any]:
        return {
            "code": item.code,
            "name": item.name,
            "default_unit": item.default_unit,
            "category": item.category,
            "is_active": item.is_active,
        }

    def _normalize_text(self, value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    def _normalize_required(self, value: Any, field_name: str) -> str:
        normalized = self._normalize_text(value)
        if normalized is None:
            raise MaterialsCatalogOperationError(f"{field_name} is required")
        return normalized
