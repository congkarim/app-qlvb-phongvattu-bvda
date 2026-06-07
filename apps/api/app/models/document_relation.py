from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin

RELATION_TYPES = frozenset({"references", "appendix_of", "implements", "related"})


class DocumentRelation(UUIDTimestampMixin, Base):
    __tablename__ = "document_relations"

    source_document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False)
    target_document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    source_document: Mapped["Document"] = relationship(
        back_populates="outgoing_relations",
        foreign_keys=[source_document_id],
    )
    target_document: Mapped["Document"] = relationship(
        back_populates="incoming_relations",
        foreign_keys=[target_document_id],
    )
    created_by_user: Mapped["User | None"] = relationship(foreign_keys=[created_by_user_id])

    __table_args__ = (
        CheckConstraint(
            "source_document_id <> target_document_id",
            name="ck_document_relations_no_self_link",
        ),
        Index(
            "ux_document_relations_active_triple",
            "source_document_id",
            "target_document_id",
            "relation_type",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_document_relations_source_active", "source_document_id", "deleted_at"),
        Index("ix_document_relations_target_active", "target_document_id", "deleted_at"),
        Index("ix_document_relations_type_active", "relation_type", "deleted_at"),
    )
