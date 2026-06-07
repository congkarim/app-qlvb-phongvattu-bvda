from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_relation import DocumentRelation
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.document_relation_repository import (
    DocumentRelationInvalidTypeError,
    DocumentRelationRepository,
    DocumentRelationSelfLinkError,
)


class DocumentRelationNotFoundError(ValueError):
    pass


class DocumentRelationAlreadyExistsError(ValueError):
    pass


class DocumentRelationOperationError(ValueError):
    pass


class DocumentRelationForbiddenError(ValueError):
    pass


class DocumentRelationService:
    def __init__(self, db: Session):
        self.db = db
        self.relations = DocumentRelationRepository(db)
        self.audit_logs = AuditLogRepository(db)

    def list_relations(self, document_id: str) -> dict[str, Any]:
        normalized_document_id = self._normalize_required(document_id, "document_id")
        if self.relations.get_active_document(normalized_document_id) is None:
            raise DocumentRelationNotFoundError("Document not found")

        outgoing = [
            self._read_outgoing(relation)
            for relation in self.relations.list_outgoing(normalized_document_id)
        ]
        incoming = [
            self._read_incoming(relation)
            for relation in self.relations.list_incoming(normalized_document_id)
        ]
        return {
            "document_id": normalized_document_id,
            "outgoing": outgoing,
            "incoming": incoming,
        }

    def create_relation(
        self,
        *,
        document_id: str,
        values: dict[str, Any],
        actor: User,
    ) -> dict[str, Any]:
        source_document_id = self._normalize_required(document_id, "document_id")
        target_document_id = self._normalize_required(values.get("target_document_id"), "target_document_id")
        relation_type = self._normalize_required(values.get("relation_type"), "relation_type")
        notes = self._normalize_text(values.get("notes"))

        if self.relations.get_active_document(source_document_id) is None:
            raise DocumentRelationOperationError("Source document not found")
        if self.relations.get_active_document(target_document_id) is None:
            raise DocumentRelationOperationError("Target document not found")

        existing = self.relations.find_active(
            source_document_id=source_document_id,
            target_document_id=target_document_id,
            relation_type=relation_type,
        )
        if existing is not None:
            raise DocumentRelationAlreadyExistsError("Document relation already exists")

        try:
            relation = self.relations.create(
                source_document_id=source_document_id,
                target_document_id=target_document_id,
                relation_type=relation_type,
                notes=notes,
                created_by_user_id=actor.id,
            )
            self.audit_logs.create(
                action="document_relation.created",
                entity_type="document_relation",
                entity_id=relation.id,
                actor_user_id=actor.id,
                metadata={
                    "source_document_id": relation.source_document_id,
                    "target_document_id": relation.target_document_id,
                    "relation_type": relation.relation_type,
                },
            )
            self.db.commit()
        except DocumentRelationSelfLinkError as exc:
            self.db.rollback()
            raise DocumentRelationOperationError(str(exc)) from exc
        except DocumentRelationInvalidTypeError as exc:
            self.db.rollback()
            raise DocumentRelationOperationError(str(exc)) from exc
        except IntegrityError as exc:
            self.db.rollback()
            raise DocumentRelationAlreadyExistsError("Document relation already exists") from exc

        relation = self.relations.get_by_id(relation.id)
        if relation is None:
            raise DocumentRelationNotFoundError("Document relation not found after create")
        return self._read_outgoing(relation)

    def delete_relation(self, *, relation_id: str, actor: User) -> dict[str, Any]:
        normalized_relation_id = self._normalize_required(relation_id, "relation_id")
        relation = self.relations.get_by_id(normalized_relation_id)
        if relation is None:
            raise DocumentRelationNotFoundError("Document relation not found")

        if actor.role != "admin" and relation.created_by_user_id != actor.id:
            raise DocumentRelationForbiddenError("Only the relation creator or admin can delete this relation")

        snapshot = self._delete_snapshot(relation)
        relation = self.relations.soft_delete(relation)
        self.audit_logs.create(
            action="document_relation.deleted",
            entity_type="document_relation",
            entity_id=relation.id,
            actor_user_id=actor.id,
            metadata={
                "source_document_id": relation.source_document_id,
                "target_document_id": relation.target_document_id,
                "relation_type": relation.relation_type,
            },
        )
        self.db.commit()
        return snapshot

    def _read_outgoing(self, relation: DocumentRelation) -> dict[str, Any]:
        target = relation.target_document
        if target is None:
            raise DocumentRelationNotFoundError("Target document not found for relation")
        return {
            "id": relation.id,
            "relation_type": relation.relation_type,
            "notes": relation.notes,
            "target_document": self._document_summary(target),
            "created_at": relation.created_at,
        }

    def _read_incoming(self, relation: DocumentRelation) -> dict[str, Any]:
        source = relation.source_document
        if source is None:
            raise DocumentRelationNotFoundError("Source document not found for relation")
        return {
            "id": relation.id,
            "relation_type": relation.relation_type,
            "notes": relation.notes,
            "source_document": self._document_summary(source),
            "created_at": relation.created_at,
        }

    def _delete_snapshot(self, relation: DocumentRelation) -> dict[str, Any]:
        return {
            "id": relation.id,
            "source_document_id": relation.source_document_id,
            "target_document_id": relation.target_document_id,
            "relation_type": relation.relation_type,
            "notes": relation.notes,
            "created_at": relation.created_at,
        }

    def _document_summary(self, document: Document) -> dict[str, Any]:
        return {
            "id": document.id,
            "title": document.title,
            "document_number": document.document_number,
            "document_type": document.document_type,
            "status": document.status,
        }

    def _normalize_text(self, value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    def _normalize_required(self, value: Any, field_name: str) -> str:
        normalized = self._normalize_text(value)
        if normalized is None:
            raise DocumentRelationOperationError(f"{field_name} is required")
        return normalized
