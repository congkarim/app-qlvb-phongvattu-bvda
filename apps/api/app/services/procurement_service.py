from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.procurement import ProcurementRecord
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.procurement_repository import ProcurementRepository


VALID_PROCUREMENT_KINDS = {"proposal", "plan", "acceptance"}
VALID_PROCUREMENT_STATUSES = {"draft", "submitted", "approved", "rejected", "completed", "archived"}


class ProcurementNotFoundError(ValueError):
    pass


class ProcurementOperationError(ValueError):
    pass


class ProcurementAlreadyExistsError(ValueError):
    pass


class ProcurementService:
    def __init__(self, db: Session):
        self.db = db
        self.procurements = ProcurementRepository(db)
        self.audit_logs = AuditLogRepository(db)

    def list_procurements(
        self,
        *,
        limit: int,
        offset: int,
        query: str | None,
        document_id: str | None,
        procurement_kind: str | None,
        reference_number: str | None,
        requesting_unit: str | None,
        status: str | None,
        requested_date_from,
        requested_date_to,
        sort_by: str,
        sort_dir: str,
    ) -> tuple[list[dict[str, Any]], int]:
        procurement_kind = self._validate_procurement_kind(procurement_kind, allow_none=True)
        status = self._validate_status(status, allow_none=True)
        items = self.procurements.list_procurements(
            limit=limit,
            offset=offset,
            query=self._normalize_text(query),
            document_id=self._normalize_text(document_id),
            procurement_kind=procurement_kind,
            reference_number=self._normalize_text(reference_number),
            requesting_unit=self._normalize_text(requesting_unit),
            status=status,
            requested_date_from=requested_date_from,
            requested_date_to=requested_date_to,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        total = self.procurements.count_procurements(
            query=self._normalize_text(query),
            document_id=self._normalize_text(document_id),
            procurement_kind=procurement_kind,
            reference_number=self._normalize_text(reference_number),
            requesting_unit=self._normalize_text(requesting_unit),
            status=status,
            requested_date_from=requested_date_from,
            requested_date_to=requested_date_to,
        )
        return [self._read(record) for record in items], total

    def get_procurement(self, procurement_id: str) -> dict[str, Any]:
        return self._read(self._get_procurement(procurement_id))

    def get_procurement_by_document_id(self, document_id: str) -> dict[str, Any]:
        normalized_document_id = self._normalize_required(document_id, "document_id")
        document = self.procurements.get_document(normalized_document_id)
        if document is None:
            raise ProcurementNotFoundError("Document not found")
        record = self.procurements.get_active_by_document_id(normalized_document_id)
        if record is None:
            raise ProcurementNotFoundError("Procurement metadata not found for this document")
        return self._read(record)

    def create_procurement(self, *, values: dict[str, Any], actor: User) -> dict[str, Any]:
        document_id = self._normalize_required(values.get("document_id"), "document_id")
        document = self.procurements.get_document(document_id)
        if document is None:
            raise ProcurementOperationError("Document not found")
        existing = self.procurements.get_active_by_document_id(document_id)
        if existing is not None:
            raise ProcurementAlreadyExistsError("Procurement metadata already exists for this document")

        payload = self._clean_values(values)
        payload["document_id"] = document_id
        record = self.procurements.create(**payload)
        self.audit_logs.create(
            action="procurement.created",
            entity_type="procurement",
            entity_id=record.id,
            actor_user_id=actor.id,
            metadata={
                "document_id": record.document_id,
                "procurement_kind": record.procurement_kind,
                "reference_number": record.reference_number,
                "status": record.status,
            },
        )
        self.db.commit()
        self.db.refresh(record)
        return self._read(self._get_procurement(record.id))

    def update_procurement(self, *, procurement_id: str, values: dict[str, Any], actor: User) -> dict[str, Any]:
        record = self._get_procurement(procurement_id)
        old_values = self._audit_snapshot(record)
        record = self.procurements.update(record, **self._clean_values(values, include_document=False))
        self.audit_logs.create(
            action="procurement.updated",
            entity_type="procurement",
            entity_id=record.id,
            actor_user_id=actor.id,
            metadata={"old": old_values, "new": self._audit_snapshot(record)},
        )
        self.db.commit()
        self.db.refresh(record)
        return self._read(self._get_procurement(record.id))

    def delete_procurement(self, *, procurement_id: str, actor: User) -> dict[str, Any]:
        record = self._get_procurement(procurement_id)
        record = self.procurements.soft_delete(record)
        self.audit_logs.create(
            action="procurement.deleted",
            entity_type="procurement",
            entity_id=record.id,
            actor_user_id=actor.id,
            metadata={
                "document_id": record.document_id,
                "procurement_kind": record.procurement_kind,
                "reference_number": record.reference_number,
            },
        )
        self.db.commit()
        self.db.refresh(record)
        return self._read(record)

    def _get_procurement(self, procurement_id: str) -> ProcurementRecord:
        record = self.procurements.get_by_id(procurement_id)
        if record is None:
            raise ProcurementNotFoundError("Procurement metadata not found")
        return record

    def _clean_values(self, values: dict[str, Any], *, include_document: bool = True) -> dict[str, Any]:
        if include_document:
            cleaned = {
                "procurement_kind": self._validate_procurement_kind(values.get("procurement_kind"), allow_none=False),
                "reference_number": self._normalize_text(values.get("reference_number")),
                "title_summary": self._normalize_text(values.get("title_summary")),
                "requesting_unit": self._normalize_text(values.get("requesting_unit")),
                "estimated_value": values.get("estimated_value"),
                "currency": self._normalize_currency(values.get("currency")),
                "requested_date": values.get("requested_date"),
                "status": self._validate_status(values.get("status"), allow_none=False),
                "notes": self._normalize_text(values.get("notes")),
                "document_id": self._normalize_required(values.get("document_id"), "document_id"),
            }
            self._validate_estimated_value(cleaned.get("estimated_value"))
            return cleaned

        cleaned: dict[str, Any] = {}
        if "procurement_kind" in values:
            cleaned["procurement_kind"] = self._validate_procurement_kind(values.get("procurement_kind"), allow_none=False)
        if "reference_number" in values:
            cleaned["reference_number"] = self._normalize_text(values.get("reference_number"))
        if "title_summary" in values:
            cleaned["title_summary"] = self._normalize_text(values.get("title_summary"))
        if "requesting_unit" in values:
            cleaned["requesting_unit"] = self._normalize_text(values.get("requesting_unit"))
        if "estimated_value" in values:
            cleaned["estimated_value"] = values.get("estimated_value")
            self._validate_estimated_value(cleaned.get("estimated_value"))
        if "currency" in values:
            cleaned["currency"] = self._normalize_currency(values.get("currency"))
        if "requested_date" in values:
            cleaned["requested_date"] = values.get("requested_date")
        if "status" in values:
            cleaned["status"] = self._validate_status(values.get("status"), allow_none=False)
        if "notes" in values:
            cleaned["notes"] = self._normalize_text(values.get("notes"))
        return cleaned

    def _read(self, record: ProcurementRecord) -> dict[str, Any]:
        document = record.document
        return {
            "id": record.id,
            "document_id": record.document_id,
            "document_title": document.title if document else None,
            "document_number": document.document_number if document else None,
            "document_status": document.status if document else None,
            "procurement_kind": record.procurement_kind,
            "reference_number": record.reference_number,
            "title_summary": record.title_summary,
            "requesting_unit": record.requesting_unit,
            "estimated_value": record.estimated_value,
            "currency": record.currency,
            "requested_date": record.requested_date,
            "status": record.status,
            "notes": record.notes,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    def _audit_snapshot(self, record: ProcurementRecord) -> dict[str, Any]:
        return {
            "document_id": record.document_id,
            "procurement_kind": record.procurement_kind,
            "reference_number": record.reference_number,
            "status": record.status,
            "requested_date": record.requested_date.isoformat() if record.requested_date else None,
            "requesting_unit": record.requesting_unit,
            "estimated_value": str(record.estimated_value) if record.estimated_value is not None else None,
        }

    def _validate_procurement_kind(self, procurement_kind: str | None, *, allow_none: bool) -> str | None:
        normalized = self._normalize_text(procurement_kind)
        if normalized is None and allow_none:
            return None
        if normalized not in VALID_PROCUREMENT_KINDS:
            raise ProcurementOperationError("Invalid procurement kind")
        return normalized

    def _validate_status(self, status: str | None, *, allow_none: bool) -> str | None:
        normalized = self._normalize_text(status)
        if normalized is None and allow_none:
            return None
        if normalized not in VALID_PROCUREMENT_STATUSES:
            raise ProcurementOperationError("Invalid procurement status")
        return normalized

    def _validate_estimated_value(self, value: Any) -> None:
        if value is None:
            return
        if isinstance(value, (int, float, Decimal)) and Decimal(str(value)) < 0:
            raise ProcurementOperationError("estimated_value cannot be negative")

    def _normalize_currency(self, value: Any) -> str:
        normalized = self._normalize_text(value) or "VND"
        return normalized.upper()

    def _normalize_text(self, value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    def _normalize_required(self, value: Any, field_name: str) -> str:
        normalized = self._normalize_text(value)
        if normalized is None:
            raise ProcurementOperationError(f"{field_name} is required")
        return normalized
