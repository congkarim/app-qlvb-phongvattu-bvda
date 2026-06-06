from typing import Any

from sqlalchemy.orm import Session

from app.models.dispatch import DispatchRecord
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.dispatch_repository import DispatchRepository


VALID_DISPATCH_TYPES = {"incoming", "outgoing"}
VALID_DISPATCH_STATUSES = {"draft", "registered", "processing", "completed", "archived"}


class DispatchNotFoundError(ValueError):
    pass


class DispatchOperationError(ValueError):
    pass


class DispatchAlreadyExistsError(ValueError):
    pass


class DispatchService:
    def __init__(self, db: Session):
        self.db = db
        self.dispatches = DispatchRepository(db)
        self.audit_logs = AuditLogRepository(db)

    def list_dispatches(
        self,
        *,
        limit: int,
        offset: int,
        query: str | None,
        document_id: str | None,
        dispatch_type: str | None,
        document_number: str | None,
        issuing_agency: str | None,
        status: str | None,
        issued_date_from,
        issued_date_to,
        sort_by: str,
        sort_dir: str,
    ) -> tuple[list[dict[str, Any]], int]:
        dispatch_type = self._validate_dispatch_type(dispatch_type, allow_none=True)
        status = self._validate_status(status, allow_none=True)
        items = self.dispatches.list_dispatches(
            limit=limit,
            offset=offset,
            query=self._normalize_text(query),
            document_id=self._normalize_text(document_id),
            dispatch_type=dispatch_type,
            document_number=self._normalize_text(document_number),
            issuing_agency=self._normalize_text(issuing_agency),
            status=status,
            issued_date_from=issued_date_from,
            issued_date_to=issued_date_to,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        total = self.dispatches.count_dispatches(
            query=self._normalize_text(query),
            document_id=self._normalize_text(document_id),
            dispatch_type=dispatch_type,
            document_number=self._normalize_text(document_number),
            issuing_agency=self._normalize_text(issuing_agency),
            status=status,
            issued_date_from=issued_date_from,
            issued_date_to=issued_date_to,
        )
        return [self._read(record) for record in items], total

    def get_dispatch(self, dispatch_id: str) -> dict[str, Any]:
        return self._read(self._get_dispatch(dispatch_id))

    def get_dispatch_by_document_id(self, document_id: str) -> dict[str, Any]:
        normalized_document_id = self._normalize_required(document_id, "document_id")
        document = self.dispatches.get_document(normalized_document_id)
        if document is None:
            raise DispatchNotFoundError("Document not found")
        record = self.dispatches.get_active_by_document_id(normalized_document_id)
        if record is None:
            raise DispatchNotFoundError("Dispatch metadata not found for this document")
        return self._read(record)

    def create_dispatch(self, *, values: dict[str, Any], actor: User) -> dict[str, Any]:
        document_id = self._normalize_required(values.get("document_id"), "document_id")
        document = self.dispatches.get_document(document_id)
        if document is None:
            raise DispatchOperationError("Document not found")
        existing = self.dispatches.get_active_by_document_id(document_id)
        if existing is not None:
            raise DispatchAlreadyExistsError("Dispatch metadata already exists for this document")

        payload = self._clean_values(values)
        payload["document_id"] = document_id
        record = self.dispatches.create(**payload)
        self.audit_logs.create(
            action="dispatch.created",
            entity_type="dispatch",
            entity_id=record.id,
            actor_user_id=actor.id,
            metadata={
                "document_id": record.document_id,
                "dispatch_type": record.dispatch_type,
                "document_number": record.document_number,
                "status": record.status,
            },
        )
        self.db.commit()
        self.db.refresh(record)
        return self._read(self._get_dispatch(record.id))

    def update_dispatch(self, *, dispatch_id: str, values: dict[str, Any], actor: User) -> dict[str, Any]:
        record = self._get_dispatch(dispatch_id)
        old_values = self._audit_snapshot(record)
        record = self.dispatches.update(record, **self._clean_values(values, include_document=False))
        self.audit_logs.create(
            action="dispatch.updated",
            entity_type="dispatch",
            entity_id=record.id,
            actor_user_id=actor.id,
            metadata={"old": old_values, "new": self._audit_snapshot(record)},
        )
        self.db.commit()
        self.db.refresh(record)
        return self._read(self._get_dispatch(record.id))

    def delete_dispatch(self, *, dispatch_id: str, actor: User) -> dict[str, Any]:
        record = self._get_dispatch(dispatch_id)
        record = self.dispatches.soft_delete(record)
        self.audit_logs.create(
            action="dispatch.deleted",
            entity_type="dispatch",
            entity_id=record.id,
            actor_user_id=actor.id,
            metadata={
                "document_id": record.document_id,
                "dispatch_type": record.dispatch_type,
                "document_number": record.document_number,
            },
        )
        self.db.commit()
        self.db.refresh(record)
        return self._read(record)

    def _get_dispatch(self, dispatch_id: str) -> DispatchRecord:
        record = self.dispatches.get_by_id(dispatch_id)
        if record is None:
            raise DispatchNotFoundError("Dispatch metadata not found")
        return record

    def _clean_values(self, values: dict[str, Any], *, include_document: bool = True) -> dict[str, Any]:
        if include_document:
            cleaned = {
                "dispatch_type": self._validate_dispatch_type(values.get("dispatch_type"), allow_none=False),
                "document_number": self._normalize_text(values.get("document_number")),
                "document_symbol": self._normalize_text(values.get("document_symbol")),
                "issued_date": values.get("issued_date"),
                "issuing_agency": self._normalize_text(values.get("issuing_agency")),
                "recipient": self._normalize_text(values.get("recipient")),
                "excerpt": self._normalize_text(values.get("excerpt")),
                "status": self._validate_status(values.get("status"), allow_none=False),
                "notes": self._normalize_text(values.get("notes")),
                "document_id": self._normalize_required(values.get("document_id"), "document_id"),
            }
            return cleaned

        cleaned: dict[str, Any] = {}
        if "dispatch_type" in values:
            cleaned["dispatch_type"] = self._validate_dispatch_type(values.get("dispatch_type"), allow_none=False)
        if "document_number" in values:
            cleaned["document_number"] = self._normalize_text(values.get("document_number"))
        if "document_symbol" in values:
            cleaned["document_symbol"] = self._normalize_text(values.get("document_symbol"))
        if "issued_date" in values:
            cleaned["issued_date"] = values.get("issued_date")
        if "issuing_agency" in values:
            cleaned["issuing_agency"] = self._normalize_text(values.get("issuing_agency"))
        if "recipient" in values:
            cleaned["recipient"] = self._normalize_text(values.get("recipient"))
        if "excerpt" in values:
            cleaned["excerpt"] = self._normalize_text(values.get("excerpt"))
        if "status" in values:
            cleaned["status"] = self._validate_status(values.get("status"), allow_none=False)
        if "notes" in values:
            cleaned["notes"] = self._normalize_text(values.get("notes"))
        return cleaned

    def _read(self, record: DispatchRecord) -> dict[str, Any]:
        document = record.document
        return {
            "id": record.id,
            "document_id": record.document_id,
            "document_title": document.title if document else None,
            "document_number": record.document_number,
            "document_status": document.status if document else None,
            "dispatch_type": record.dispatch_type,
            "document_symbol": record.document_symbol,
            "issued_date": record.issued_date,
            "issuing_agency": record.issuing_agency,
            "recipient": record.recipient,
            "excerpt": record.excerpt,
            "status": record.status,
            "notes": record.notes,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    def _audit_snapshot(self, record: DispatchRecord) -> dict[str, Any]:
        return {
            "document_id": record.document_id,
            "dispatch_type": record.dispatch_type,
            "document_number": record.document_number,
            "status": record.status,
            "issued_date": record.issued_date.isoformat() if record.issued_date else None,
            "issuing_agency": record.issuing_agency,
        }

    def _validate_dispatch_type(self, dispatch_type: str | None, *, allow_none: bool) -> str | None:
        normalized = self._normalize_text(dispatch_type)
        if normalized is None and allow_none:
            return None
        if normalized not in VALID_DISPATCH_TYPES:
            raise DispatchOperationError("Invalid dispatch type")
        return normalized

    def _validate_status(self, status: str | None, *, allow_none: bool) -> str | None:
        normalized = self._normalize_text(status)
        if normalized is None and allow_none:
            return None
        if normalized not in VALID_DISPATCH_STATUSES:
            raise DispatchOperationError("Invalid dispatch status")
        return normalized

    def _normalize_text(self, value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    def _normalize_required(self, value: Any, field_name: str) -> str:
        normalized = self._normalize_text(value)
        if normalized is None:
            raise DispatchOperationError(f"{field_name} is required")
        return normalized
