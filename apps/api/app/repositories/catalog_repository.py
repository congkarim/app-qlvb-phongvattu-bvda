from datetime import datetime, timezone

from sqlalchemy import asc, func, or_, select
from sqlalchemy.orm import Session

from app.models.catalog import AdminCatalogItem
from app.models.department import Department
from app.models.document import Document
from app.models.user import User


class CatalogRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_departments(self, *, include_inactive: bool = False, query: str | None = None) -> list[Department]:
        stmt = select(Department).where(Department.deleted_at.is_(None))
        if not include_inactive:
            stmt = stmt.where(Department.is_active.is_(True))
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(or_(Department.code.ilike(pattern), Department.name.ilike(pattern)))
        stmt = stmt.order_by(asc(Department.sort_order), asc(Department.name), asc(Department.id))
        return list(self.db.scalars(stmt))

    def get_department(self, department_id: str) -> Department | None:
        stmt = select(Department).where(Department.id == department_id, Department.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def get_department_by_code(self, code: str) -> Department | None:
        stmt = select(Department).where(Department.code == code, Department.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def get_department_by_name(self, name: str) -> Department | None:
        stmt = select(Department).where(Department.name == name, Department.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def department_is_referenced(self, department_id: str) -> bool:
        user_count = int(self.db.scalar(select(func.count()).select_from(User).where(
            User.department_id == department_id,
            User.deleted_at.is_(None),
        )) or 0)
        document_count = int(self.db.scalar(select(func.count()).select_from(Document).where(
            Document.department_id == department_id,
            Document.deleted_at.is_(None),
        )) or 0)
        return user_count > 0 or document_count > 0

    def create_department(self, **values) -> Department:
        department = Department(**values)
        self.db.add(department)
        self.db.flush()
        return department

    def update_department(self, department: Department, **values) -> Department:
        for key, value in values.items():
            setattr(department, key, value)
        self.db.add(department)
        self.db.flush()
        return department

    def soft_delete_department(self, department: Department) -> Department:
        department.deleted_at = datetime.now(timezone.utc)
        department.is_active = False
        self.db.add(department)
        self.db.flush()
        return department

    def list_items(self, *, catalog_type: str | None = None, include_inactive: bool = False, query: str | None = None) -> list[AdminCatalogItem]:
        stmt = select(AdminCatalogItem).where(AdminCatalogItem.deleted_at.is_(None))
        if catalog_type:
            stmt = stmt.where(AdminCatalogItem.catalog_type == catalog_type)
        if not include_inactive:
            stmt = stmt.where(AdminCatalogItem.is_active.is_(True))
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(or_(AdminCatalogItem.code.ilike(pattern), AdminCatalogItem.label.ilike(pattern)))
        stmt = stmt.order_by(asc(AdminCatalogItem.catalog_type), asc(AdminCatalogItem.sort_order), asc(AdminCatalogItem.label), asc(AdminCatalogItem.id))
        return list(self.db.scalars(stmt))

    def get_item(self, item_id: str) -> AdminCatalogItem | None:
        stmt = select(AdminCatalogItem).where(AdminCatalogItem.id == item_id, AdminCatalogItem.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def get_item_by_type_code(self, *, catalog_type: str, code: str) -> AdminCatalogItem | None:
        stmt = select(AdminCatalogItem).where(
            AdminCatalogItem.catalog_type == catalog_type,
            AdminCatalogItem.code == code,
            AdminCatalogItem.deleted_at.is_(None),
        )
        return self.db.scalar(stmt)

    def create_item(self, **values) -> AdminCatalogItem:
        item = AdminCatalogItem(**values)
        self.db.add(item)
        self.db.flush()
        return item

    def update_item(self, item: AdminCatalogItem, **values) -> AdminCatalogItem:
        for key, value in values.items():
            setattr(item, key, value)
        self.db.add(item)
        self.db.flush()
        return item

    def soft_delete_item(self, item: AdminCatalogItem) -> AdminCatalogItem:
        item.deleted_at = datetime.now(timezone.utc)
        item.is_active = False
        self.db.add(item)
        self.db.flush()
        return item
