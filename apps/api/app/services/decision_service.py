from typing import Any

from sqlalchemy.orm import Session

from app.models.decision import DecisionRecord
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.decision_repository import DecisionRepository


VALID_DECISION_KINDS = {"decision", "notification"}
VALID_DECISION_STATUSES = {"draft", "registered", "effective", "expired", "revoked", "archived"}


class DecisionNotFoundError(ValueError):
    pass


class DecisionOperationError(ValueError):
    pass


class DecisionAlreadyExistsError(ValueError):
    pass


class DecisionService:
    def __init__(self, db: Session):
        self.db = db
        self.decisions = DecisionRepository(db)
        self.audit_logs = AuditLogRepository(db)

    def list_decisions(
        self,
        *,
        limit: int,
        offset: int,
        query: str | None,
        document_id: str | None,
        decision_kind: str | None,
        document_number: str | None,
        issuing_agency: str | None,
        status: str | None,
        issued_date_from,
        issued_date_to,
        effective_from,
        effective_to,
        sort_by: str,
        sort_dir: str,
    ) -> tuple[list[dict[str, Any]], int]:
        decision_kind = self._validate_decision_kind(decision_kind, allow_none=True)
        status = self._validate_status(status, allow_none=True)
        items = self.decisions.list_decisions(
            limit=limit,
            offset=offset,
            query=self._normalize_text(query),
            document_id=self._normalize_text(document_id),
            decision_kind=decision_kind,
            document_number=self._normalize_text(document_number),
            issuing_agency=self._normalize_text(issuing_agency),
            status=status,
            issued_date_from=issued_date_from,
            issued_date_to=issued_date_to,
            effective_from=effective_from,
            effective_to=effective_to,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        total = self.decisions.count_decisions(
            query=self._normalize_text(query),
            document_id=self._normalize_text(document_id),
            decision_kind=decision_kind,
            document_number=self._normalize_text(document_number),
            issuing_agency=self._normalize_text(issuing_agency),
            status=status,
            issued_date_from=issued_date_from,
            issued_date_to=issued_date_to,
            effective_from=effective_from,
            effective_to=effective_to,
        )
        return [self._read(record) for record in items], total

    def get_decision(self, decision_id: str) -> dict[str, Any]:
        return self._read(self._get_decision(decision_id))

    def get_decision_by_document_id(self, document_id: str) -> dict[str, Any]:
        normalized_document_id = self._normalize_required(document_id, "document_id")
        document = self.decisions.get_document(normalized_document_id)
        if document is None:
            raise DecisionNotFoundError("Document not found")
        record = self.decisions.get_active_by_document_id(normalized_document_id)
        if record is None:
            raise DecisionNotFoundError("Decision metadata not found for this document")
        return self._read(record)

    def create_decision(self, *, values: dict[str, Any], actor: User) -> dict[str, Any]:
        document_id = self._normalize_required(values.get("document_id"), "document_id")
        document = self.decisions.get_document(document_id)
        if document is None:
            raise DecisionOperationError("Document not found")
        existing = self.decisions.get_active_by_document_id(document_id)
        if existing is not None:
            raise DecisionAlreadyExistsError("Decision metadata already exists for this document")

        payload = self._clean_values(values)
        payload["document_id"] = document_id
        record = self.decisions.create(**payload)
        self.audit_logs.create(
            action="decision.created",
            entity_type="decision",
            entity_id=record.id,
            actor_user_id=actor.id,
            metadata={
                "document_id": record.document_id,
                "decision_kind": record.decision_kind,
                "document_number": record.document_number,
                "status": record.status,
            },
        )
        self.db.commit()
        self.db.refresh(record)
        return self._read(self._get_decision(record.id))

    def update_decision(self, *, decision_id: str, values: dict[str, Any], actor: User) -> dict[str, Any]:
        record = self._get_decision(decision_id)
        old_values = self._audit_snapshot(record)
        record = self.decisions.update(record, **self._clean_values(values, include_document=False))
        self.audit_logs.create(
            action="decision.updated",
            entity_type="decision",
            entity_id=record.id,
            actor_user_id=actor.id,
            metadata={"old": old_values, "new": self._audit_snapshot(record)},
        )
        self.db.commit()
        self.db.refresh(record)
        return self._read(self._get_decision(record.id))

    def delete_decision(self, *, decision_id: str, actor: User) -> dict[str, Any]:
        record = self._get_decision(decision_id)
        record = self.decisions.soft_delete(record)
        self.audit_logs.create(
            action="decision.deleted",
            entity_type="decision",
            entity_id=record.id,
            actor_user_id=actor.id,
            metadata={
                "document_id": record.document_id,
                "decision_kind": record.decision_kind,
                "document_number": record.document_number,
            },
        )
        self.db.commit()
        self.db.refresh(record)
        return self._read(record)

    def _get_decision(self, decision_id: str) -> DecisionRecord:
        record = self.decisions.get_by_id(decision_id)
        if record is None:
            raise DecisionNotFoundError("Decision metadata not found")
        return record

    def _clean_values(self, values: dict[str, Any], *, include_document: bool = True) -> dict[str, Any]:
        if include_document:
            return {
                "decision_kind": self._validate_decision_kind(values.get("decision_kind"), allow_none=False),
                "document_number": self._normalize_text(values.get("document_number")),
                "document_symbol": self._normalize_text(values.get("document_symbol")),
                "issued_date": values.get("issued_date"),
                "issuing_agency": self._normalize_text(values.get("issuing_agency")),
                "excerpt": self._normalize_text(values.get("excerpt")),
                "effective_from": values.get("effective_from"),
                "effective_to": values.get("effective_to"),
                "status": self._validate_status(values.get("status"), allow_none=False),
                "notes": self._normalize_text(values.get("notes")),
                "document_id": self._normalize_required(values.get("document_id"), "document_id"),
            }

        cleaned: dict[str, Any] = {}
        if "decision_kind" in values:
            cleaned["decision_kind"] = self._validate_decision_kind(values.get("decision_kind"), allow_none=False)
        if "document_number" in values:
            cleaned["document_number"] = self._normalize_text(values.get("document_number"))
        if "document_symbol" in values:
            cleaned["document_symbol"] = self._normalize_text(values.get("document_symbol"))
        if "issued_date" in values:
            cleaned["issued_date"] = values.get("issued_date")
        if "issuing_agency" in values:
            cleaned["issuing_agency"] = self._normalize_text(values.get("issuing_agency"))
        if "excerpt" in values:
            cleaned["excerpt"] = self._normalize_text(values.get("excerpt"))
        if "effective_from" in values:
            cleaned["effective_from"] = values.get("effective_from")
        if "effective_to" in values:
            cleaned["effective_to"] = values.get("effective_to")
        if "status" in values:
            cleaned["status"] = self._validate_status(values.get("status"), allow_none=False)
        if "notes" in values:
            cleaned["notes"] = self._normalize_text(values.get("notes"))
        return cleaned

    def _read(self, record: DecisionRecord) -> dict[str, Any]:
        document = record.document
        return {
            "id": record.id,
            "document_id": record.document_id,
            "document_title": document.title if document else None,
            "document_type": document.document_type if document else None,
            "document_status": document.status if document else None,
            "decision_kind": record.decision_kind,
            "document_number": record.document_number,
            "document_symbol": record.document_symbol,
            "issued_date": record.issued_date,
            "issuing_agency": record.issuing_agency,
            "excerpt": record.excerpt,
            "effective_from": record.effective_from,
            "effective_to": record.effective_to,
            "status": record.status,
            "notes": record.notes,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    def _audit_snapshot(self, record: DecisionRecord) -> dict[str, Any]:
        return {
            "document_id": record.document_id,
            "decision_kind": record.decision_kind,
            "document_number": record.document_number,
            "status": record.status,
            "issued_date": record.issued_date.isoformat() if record.issued_date else None,
            "effective_from": record.effective_from.isoformat() if record.effective_from else None,
            "effective_to": record.effective_to.isoformat() if record.effective_to else None,
            "issuing_agency": record.issuing_agency,
        }

    def _validate_decision_kind(self, decision_kind: str | None, *, allow_none: bool) -> str | None:
        normalized = self._normalize_text(decision_kind)
        if normalized is None and allow_none:
            return None
        if normalized not in VALID_DECISION_KINDS:
            raise DecisionOperationError("Invalid decision kind")
        return normalized

    def _validate_status(self, status: str | None, *, allow_none: bool) -> str | None:
        normalized = self._normalize_text(status)
        if normalized is None and allow_none:
            return None
        if normalized not in VALID_DECISION_STATUSES:
            raise DecisionOperationError("Invalid decision status")
        return normalized

    def _normalize_text(self, value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    def _normalize_required(self, value: Any, field_name: str) -> str:
        normalized = self._normalize_text(value)
        if normalized is None:
            raise DecisionOperationError(f"{field_name} is required")
        return normalized
