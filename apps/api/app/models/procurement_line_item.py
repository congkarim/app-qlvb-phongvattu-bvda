from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin


class ProcurementLineItem(UUIDTimestampMixin, Base):
    __tablename__ = "procurement_line_items"

    procurement_id: Mapped[str] = mapped_column(ForeignKey("procurement_records.id"), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    item_name: Mapped[str] = mapped_column(String(512), nullable=False)
    item_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("1"))
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    procurement: Mapped["ProcurementRecord"] = relationship(back_populates="line_items")

    __table_args__ = (
        Index(
            "ux_procurement_line_items_procurement_line_active",
            "procurement_id",
            "line_number",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_procurement_line_items_procurement_active", "procurement_id", "deleted_at"),
        Index("ix_procurement_line_items_item_name_active", "item_name", "deleted_at"),
        Index("ix_procurement_line_items_item_code_active", "item_code", "deleted_at"),
    )
