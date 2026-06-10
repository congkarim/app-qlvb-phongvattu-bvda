from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin


class StockMovement(UUIDTimestampMixin, Base):
    __tablename__ = "stock_movements"

    catalog_item_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materials_catalog.id", ondelete="RESTRICT"),
        nullable=False,
    )
    movement_type: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    movement_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    procurement_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("procurement_records.id", ondelete="SET NULL"),
        nullable=True,
    )
    balance_after: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    created_by_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    catalog_item = relationship("MaterialsCatalogItem", back_populates="stock_movements")
    procurement = relationship("ProcurementRecord", back_populates="stock_movements")
    created_by = relationship("User")

    __table_args__ = (
        CheckConstraint("movement_type IN ('in', 'out')", name="ck_stock_movements_movement_type"),
        CheckConstraint("quantity > 0", name="ck_stock_movements_quantity_positive"),
        Index("ix_stock_movements_catalog_item_active", "catalog_item_id", "deleted_at"),
        Index("ix_stock_movements_movement_date_active", "movement_date", "deleted_at"),
        Index("ix_stock_movements_movement_type_active", "movement_type", "deleted_at"),
        Index("ix_stock_movements_procurement_active", "procurement_id", "deleted_at"),
    )
