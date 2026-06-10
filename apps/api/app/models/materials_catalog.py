from decimal import Decimal

from sqlalchemy import Boolean, Index, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin


class MaterialsCatalogItem(UUIDTimestampMixin, Base):
    __tablename__ = "materials_catalog"

    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    min_stock_level: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)

    stock_balance = relationship("StockBalance", back_populates="catalog_item", uselist=False)
    stock_movements = relationship("StockMovement", back_populates="catalog_item")

    __table_args__ = (
        Index("ix_materials_catalog_name_active", "name", "deleted_at"),
        Index("ix_materials_catalog_is_active", "is_active", "deleted_at"),
    )
