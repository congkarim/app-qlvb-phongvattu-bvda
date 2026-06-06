from typing import Any

from sqlalchemy.orm import Session

from app.models.catalog import AdminCatalogItem
from app.models.department import Department
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.catalog_repository import CatalogRepository


VALID_CATALOG_TYPES = {"business_type", "document_type"}


class CatalogNotFoundError(ValueError):
    pass


class CatalogAlreadyExistsError(ValueError):
    pass


class CatalogOperationError(ValueError):
    pass


class CatalogService:
    def __init__(self, db: Session):
        self.db = db
        self.catalogs = CatalogRepository(db)
        self.audit_logs = AuditLogRepository(db)

    def list_departments(self, *, include_inactive: bool = False, query: str | None = None) -> list[Department]:
        return self.catalogs.list_departments(include_inactive=include_inactive, query=self._normalize_text(query))

    def create_department(self, *, values: dict[str, Any], actor: User) -> Department:
        payload = self._clean_department_values(values)
        self._ensure_department_unique(code=payload["code"], name=payload["name"])
        department = self.catalogs.create_department(**payload)
        self.audit_logs.create(
            action="admin_catalog.department_created",
            entity_type="department",
            entity_id=department.id,
            actor_user_id=actor.id,
            metadata=self._department_snapshot(department),
        )
        self.db.commit()
        self.db.refresh(department)
        return department

    def update_department(self, *, department_id: str, values: dict[str, Any], actor: User) -> Department:
        department = self._get_department(department_id)
        payload = self._clean_department_values(values)
        self._ensure_department_unique(code=payload["code"], name=payload["name"], current_id=department.id)
        old_values = self._department_snapshot(department)
        department = self.catalogs.update_department(department, **payload)
        self.audit_logs.create(
            action="admin_catalog.department_updated",
            entity_type="department",
            entity_id=department.id,
            actor_user_id=actor.id,
            metadata={"old": old_values, "new": self._department_snapshot(department)},
        )
        self.db.commit()
        self.db.refresh(department)
        return department

    def delete_department(self, *, department_id: str, actor: User) -> Department:
        department = self._get_department(department_id)
        if self.catalogs.department_is_referenced(department.id):
            raise CatalogOperationError("Department is referenced by users or documents")
        department = self.catalogs.soft_delete_department(department)
        self.audit_logs.create(
            action="admin_catalog.department_deleted",
            entity_type="department",
            entity_id=department.id,
            actor_user_id=actor.id,
            metadata=self._department_snapshot(department),
        )
        self.db.commit()
        self.db.refresh(department)
        return department

    def list_items(
        self,
        *,
        catalog_type: str | None = None,
        include_inactive: bool = False,
        query: str | None = None,
    ) -> list[AdminCatalogItem]:
        normalized_type = self._validate_catalog_type(catalog_type, allow_none=True)
        return self.catalogs.list_items(
            catalog_type=normalized_type,
            include_inactive=include_inactive,
            query=self._normalize_text(query),
        )

    def create_item(self, *, values: dict[str, Any], actor: User) -> AdminCatalogItem:
        payload = self._clean_item_values(values)
        self._ensure_item_unique(catalog_type=payload["catalog_type"], code=payload["code"])
        item = self.catalogs.create_item(**payload)
        self.audit_logs.create(
            action="admin_catalog.item_created",
            entity_type="admin_catalog_item",
            entity_id=item.id,
            actor_user_id=actor.id,
            metadata=self._item_snapshot(item),
        )
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_item(self, *, item_id: str, values: dict[str, Any], actor: User) -> AdminCatalogItem:
        item = self._get_item(item_id)
        payload = self._clean_item_values(values)
        self._ensure_item_unique(catalog_type=payload["catalog_type"], code=payload["code"], current_id=item.id)
        old_values = self._item_snapshot(item)
        item = self.catalogs.update_item(item, **payload)
        self.audit_logs.create(
            action="admin_catalog.item_updated",
            entity_type="admin_catalog_item",
            entity_id=item.id,
            actor_user_id=actor.id,
            metadata={"old": old_values, "new": self._item_snapshot(item)},
        )
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_item(self, *, item_id: str, actor: User) -> AdminCatalogItem:
        item = self._get_item(item_id)
        item = self.catalogs.soft_delete_item(item)
        self.audit_logs.create(
            action="admin_catalog.item_deleted",
            entity_type="admin_catalog_item",
            entity_id=item.id,
            actor_user_id=actor.id,
            metadata=self._item_snapshot(item),
        )
        self.db.commit()
        self.db.refresh(item)
        return item

    def _get_department(self, department_id: str) -> Department:
        department = self.catalogs.get_department(department_id)
        if department is None:
            raise CatalogNotFoundError("Department not found")
        return department

    def _get_item(self, item_id: str) -> AdminCatalogItem:
        item = self.catalogs.get_item(item_id)
        if item is None:
            raise CatalogNotFoundError("Catalog item not found")
        return item

    def _clean_department_values(self, values: dict[str, Any]) -> dict[str, Any]:
        return {
            "code": self._normalize_code(values.get("code"), allow_none=True),
            "name": self._normalize_required(values.get("name"), "name"),
            "description": self._normalize_text(values.get("description")),
            "sort_order": int(values.get("sort_order") or 0),
            "is_active": bool(values.get("is_active")),
        }

    def _clean_item_values(self, values: dict[str, Any]) -> dict[str, Any]:
        return {
            "catalog_type": self._validate_catalog_type(values.get("catalog_type"), allow_none=False),
            "code": self._normalize_code(values.get("code"), allow_none=False),
            "label": self._normalize_required(values.get("label"), "label"),
            "description": self._normalize_text(values.get("description")),
            "sort_order": int(values.get("sort_order") or 0),
            "is_active": bool(values.get("is_active")),
        }

    def _ensure_department_unique(self, *, code: str | None, name: str, current_id: str | None = None) -> None:
        if code:
            existing = self.catalogs.get_department_by_code(code)
            if existing and existing.id != current_id:
                raise CatalogAlreadyExistsError("Department code already exists")
        existing_name = self.catalogs.get_department_by_name(name)
        if existing_name and existing_name.id != current_id:
            raise CatalogAlreadyExistsError("Department name already exists")

    def _ensure_item_unique(self, *, catalog_type: str, code: str, current_id: str | None = None) -> None:
        existing = self.catalogs.get_item_by_type_code(catalog_type=catalog_type, code=code)
        if existing and existing.id != current_id:
            raise CatalogAlreadyExistsError("Catalog item code already exists")

    def _department_snapshot(self, department: Department) -> dict[str, Any]:
        return {
            "code": department.code,
            "name": department.name,
            "is_active": department.is_active,
            "sort_order": department.sort_order,
        }

    def _item_snapshot(self, item: AdminCatalogItem) -> dict[str, Any]:
        return {
            "catalog_type": item.catalog_type,
            "code": item.code,
            "label": item.label,
            "is_active": item.is_active,
            "sort_order": item.sort_order,
        }

    def _validate_catalog_type(self, catalog_type: Any, *, allow_none: bool) -> str | None:
        normalized = self._normalize_text(catalog_type)
        if normalized is None and allow_none:
            return None
        if normalized not in VALID_CATALOG_TYPES:
            raise CatalogOperationError("Invalid catalog type")
        return normalized

    def _normalize_code(self, value: Any, *, allow_none: bool) -> str | None:
        normalized = self._normalize_text(value)
        if normalized is None and allow_none:
            return None
        if normalized is None:
            raise CatalogOperationError("code is required")
        if any(char.isspace() for char in normalized):
            raise CatalogOperationError("code cannot contain whitespace")
        return normalized

    def _normalize_required(self, value: Any, field_name: str) -> str:
        normalized = self._normalize_text(value)
        if normalized is None:
            raise CatalogOperationError(f"{field_name} is required")
        return normalized

    def _normalize_text(self, value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None
