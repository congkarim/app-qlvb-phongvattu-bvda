from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDTimestampMixin


class AdminCatalogItem(UUIDTimestampMixin, Base):
    __tablename__ = "admin_catalog_items"

    catalog_type: Mapped[str] = mapped_column(String(64), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("ix_admin_catalog_items_type_active_sort", "catalog_type", "is_active", "sort_order"),
        Index("ix_admin_catalog_items_type_code_active", "catalog_type", "code", "deleted_at"),
    )
