from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin


class ContractRecord(UUIDTimestampMixin, Base):
    __tablename__ = "contract_records"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False)
    contract_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    contract_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    supplier_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sign_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    contract_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="VND")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="contract_record")

    __table_args__ = (
        Index(
            "ux_contract_records_document_active",
            "document_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_contract_records_contract_number_active", "contract_number", "deleted_at"),
        Index("ix_contract_records_supplier_active", "supplier_name", "deleted_at"),
        Index("ix_contract_records_status_active", "status", "deleted_at"),
        Index("ix_contract_records_sign_date_active", "sign_date", "deleted_at"),
        Index("ix_contract_records_effective_to_active", "effective_to", "deleted_at"),
    )
