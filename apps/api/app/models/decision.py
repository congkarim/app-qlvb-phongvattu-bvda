from datetime import date

from sqlalchemy import Date, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin


class DecisionRecord(UUIDTimestampMixin, Base):
    __tablename__ = "decision_records"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False)
    decision_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    document_symbol: Mapped[str | None] = mapped_column(String(128), nullable=True)
    issued_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    issuing_agency: Mapped[str | None] = mapped_column(String(255), nullable=True)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="decision_record")

    __table_args__ = (
        Index(
            "ux_decision_records_document_active",
            "document_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_decision_records_decision_kind_active", "decision_kind", "deleted_at"),
        Index("ix_decision_records_document_number_active", "document_number", "deleted_at"),
        Index("ix_decision_records_issuing_agency_active", "issuing_agency", "deleted_at"),
        Index("ix_decision_records_issued_date_active", "issued_date", "deleted_at"),
        Index("ix_decision_records_effective_from_active", "effective_from", "deleted_at"),
        Index("ix_decision_records_effective_to_active", "effective_to", "deleted_at"),
        Index("ix_decision_records_status_active", "status", "deleted_at"),
    )
