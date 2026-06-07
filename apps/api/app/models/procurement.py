from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin


class ProcurementRecord(UUIDTimestampMixin, Base):
    __tablename__ = "procurement_records"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False)
    procurement_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    requesting_unit: Mapped[str | None] = mapped_column(String(255), nullable=True)
    estimated_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="VND")
    requested_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="procurement_record")

    __table_args__ = (
        Index(
            "ux_procurement_records_document_active",
            "document_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_procurement_records_procurement_kind_active", "procurement_kind", "deleted_at"),
        Index("ix_procurement_records_reference_number_active", "reference_number", "deleted_at"),
        Index("ix_procurement_records_requesting_unit_active", "requesting_unit", "deleted_at"),
        Index("ix_procurement_records_status_active", "status", "deleted_at"),
        Index("ix_procurement_records_requested_date_active", "requested_date", "deleted_at"),
    )
