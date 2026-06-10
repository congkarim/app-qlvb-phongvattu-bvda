from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin


class StockBalance(UUIDTimestampMixin, Base):
    __tablename__ = "stock_balances"

    catalog_item_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materials_catalog.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))

    catalog_item = relationship("MaterialsCatalogItem", back_populates="stock_balance", uselist=False)

    __table_args__ = (
        Index("ix_stock_balances_catalog_item_active", "catalog_item_id", "deleted_at"),
    )
