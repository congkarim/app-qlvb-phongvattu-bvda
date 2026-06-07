from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.document import Document
from app.models.document_relation import RELATION_TYPES, DocumentRelation


class DocumentRelationSelfLinkError(ValueError):
    pass


class DocumentRelationInvalidTypeError(ValueError):
    pass


class DocumentRelationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, relation_id: str) -> DocumentRelation | None:
        stmt = (
            select(DocumentRelation)
            .where(DocumentRelation.id == relation_id, DocumentRelation.deleted_at.is_(None))
            .options(
                selectinload(DocumentRelation.source_document),
                selectinload(DocumentRelation.target_document),
            )
        )
        return self.db.scalar(stmt)

    def find_active(
        self,
        *,
        source_document_id: str,
        target_document_id: str,
        relation_type: str,
    ) -> DocumentRelation | None:
        stmt = select(DocumentRelation).where(
            DocumentRelation.source_document_id == source_document_id,
            DocumentRelation.target_document_id == target_document_id,
            DocumentRelation.relation_type == relation_type,
            DocumentRelation.deleted_at.is_(None),
        )
        return self.db.scalar(stmt)

    def list_outgoing(self, document_id: str) -> list[DocumentRelation]:
        stmt = (
            select(DocumentRelation)
            .where(
                DocumentRelation.source_document_id == document_id,
                DocumentRelation.deleted_at.is_(None),
            )
            .options(selectinload(DocumentRelation.target_document))
            .order_by(DocumentRelation.created_at.desc(), DocumentRelation.id.desc())
        )
        return list(self.db.scalars(stmt))

    def list_incoming(self, document_id: str) -> list[DocumentRelation]:
        stmt = (
            select(DocumentRelation)
            .where(
                DocumentRelation.target_document_id == document_id,
                DocumentRelation.deleted_at.is_(None),
            )
            .options(selectinload(DocumentRelation.source_document))
            .order_by(DocumentRelation.created_at.desc(), DocumentRelation.id.desc())
        )
        return list(self.db.scalars(stmt))

    def count_active_for_document(self, document_id: str) -> int:
        stmt = select(func.count(DocumentRelation.id)).where(
            DocumentRelation.deleted_at.is_(None),
            or_(
                DocumentRelation.source_document_id == document_id,
                DocumentRelation.target_document_id == document_id,
            ),
        )
        return int(self.db.scalar(stmt) or 0)

    def batch_count_active_for_documents(self, document_ids: list[str]) -> dict[str, int]:
        if not document_ids:
            return {}
        counts = {document_id: 0 for document_id in document_ids}
        source_stmt = (
            select(DocumentRelation.source_document_id, func.count(DocumentRelation.id))
            .where(
                DocumentRelation.deleted_at.is_(None),
                DocumentRelation.source_document_id.in_(document_ids),
            )
            .group_by(DocumentRelation.source_document_id)
        )
        for document_id, count in self.db.execute(source_stmt):
            counts[document_id] = counts.get(document_id, 0) + int(count)
        target_stmt = (
            select(DocumentRelation.target_document_id, func.count(DocumentRelation.id))
            .where(
                DocumentRelation.deleted_at.is_(None),
                DocumentRelation.target_document_id.in_(document_ids),
            )
            .group_by(DocumentRelation.target_document_id)
        )
        for document_id, count in self.db.execute(target_stmt):
            counts[document_id] = counts.get(document_id, 0) + int(count)
        return counts

    def create(
        self,
        *,
        source_document_id: str,
        target_document_id: str,
        relation_type: str,
        notes: str | None = None,
        created_by_user_id: str | None = None,
    ) -> DocumentRelation:
        if source_document_id == target_document_id:
            raise DocumentRelationSelfLinkError("source_document_id must differ from target_document_id")
        if relation_type not in RELATION_TYPES:
            raise DocumentRelationInvalidTypeError(f"Unsupported relation_type: {relation_type}")

        relation = DocumentRelation(
            source_document_id=source_document_id,
            target_document_id=target_document_id,
            relation_type=relation_type,
            notes=notes,
            created_by_user_id=created_by_user_id,
        )
        self.db.add(relation)
        self.db.flush()
        return relation

    def soft_delete(self, relation: DocumentRelation) -> DocumentRelation:
        relation.deleted_at = datetime.now(timezone.utc)
        self.db.add(relation)
        self.db.flush()
        return relation

    def get_active_document(self, document_id: str) -> Document | None:
        stmt = select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
        return self.db.scalar(stmt)
