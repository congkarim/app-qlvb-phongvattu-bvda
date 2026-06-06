from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.contract import ContractRecord
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.contract_repository import ContractRepository


VALID_CONTRACT_STATUSES = {"draft", "active", "expired", "terminated", "completed"}


class ContractNotFoundError(ValueError):
    pass


class ContractOperationError(ValueError):
    pass


class ContractAlreadyExistsError(ValueError):
    pass


class ContractService:
    def __init__(self, db: Session):
        self.db = db
        self.contracts = ContractRepository(db)
        self.audit_logs = AuditLogRepository(db)

    def list_contracts(
        self,
        *,
        limit: int,
        offset: int,
        query: str | None,
        document_id: str | None,
        contract_number: str | None,
        supplier_name: str | None,
        status: str | None,
        sign_date_from: date | None,
        sign_date_to: date | None,
        effective_to_from: date | None,
        effective_to_to: date | None,
        sort_by: str,
        sort_dir: str,
    ) -> tuple[list[dict[str, Any]], int]:
        status = self._validate_status(status, allow_none=True)
        items = self.contracts.list_contracts(
            limit=limit,
            offset=offset,
            query=self._normalize_text(query),
            document_id=self._normalize_text(document_id),
            contract_number=self._normalize_text(contract_number),
            supplier_name=self._normalize_text(supplier_name),
            status=status,
            sign_date_from=sign_date_from,
            sign_date_to=sign_date_to,
            effective_to_from=effective_to_from,
            effective_to_to=effective_to_to,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        total = self.contracts.count_contracts(
            query=self._normalize_text(query),
            document_id=self._normalize_text(document_id),
            contract_number=self._normalize_text(contract_number),
            supplier_name=self._normalize_text(supplier_name),
            status=status,
            sign_date_from=sign_date_from,
            sign_date_to=sign_date_to,
            effective_to_from=effective_to_from,
            effective_to_to=effective_to_to,
        )
        return [self._read(record) for record in items], total

    def get_contract(self, contract_id: str) -> dict[str, Any]:
        return self._read(self._get_contract(contract_id))

    def get_contract_by_document_id(self, document_id: str) -> dict[str, Any]:
        normalized_document_id = self._normalize_required(document_id, "document_id")
        document = self.contracts.get_document(normalized_document_id)
        if document is None:
            raise ContractNotFoundError("Document not found")
        record = self.contracts.get_active_by_document_id(normalized_document_id)
        if record is None:
            raise ContractNotFoundError("Contract metadata not found for this document")
        return self._read(record)

    def create_contract(self, *, values: dict[str, Any], actor: User) -> dict[str, Any]:
        document_id = self._normalize_required(values.get("document_id"), "document_id")
        document = self.contracts.get_document(document_id)
        if document is None:
            raise ContractOperationError("Document not found")
        existing = self.contracts.get_active_by_document_id(document_id)
        if existing is not None:
            raise ContractAlreadyExistsError("Contract metadata already exists for this document")

        payload = self._clean_values(values)
        payload["document_id"] = document_id
        record = self.contracts.create(**payload)
        self.audit_logs.create(
            action="contract.created",
            entity_type="contract",
            entity_id=record.id,
            actor_user_id=actor.id,
            metadata={"document_id": record.document_id, "contract_number": record.contract_number},
        )
        self.db.commit()
        self.db.refresh(record)
        return self._read(self._get_contract(record.id))

    def update_contract(self, *, contract_id: str, values: dict[str, Any], actor: User) -> dict[str, Any]:
        record = self._get_contract(contract_id)
        old_values = self._audit_snapshot(record)
        record = self.contracts.update(record, **self._clean_values(values, include_document=False))
        self.audit_logs.create(
            action="contract.updated",
            entity_type="contract",
            entity_id=record.id,
            actor_user_id=actor.id,
            metadata={"old": old_values, "new": self._audit_snapshot(record)},
        )
        self.db.commit()
        self.db.refresh(record)
        return self._read(self._get_contract(record.id))

    def delete_contract(self, *, contract_id: str, actor: User) -> dict[str, Any]:
        record = self._get_contract(contract_id)
        record = self.contracts.soft_delete(record)
        self.audit_logs.create(
            action="contract.deleted",
            entity_type="contract",
            entity_id=record.id,
            actor_user_id=actor.id,
            metadata={"document_id": record.document_id, "contract_number": record.contract_number},
        )
        self.db.commit()
        self.db.refresh(record)
        return self._read(record)

    def _get_contract(self, contract_id: str) -> ContractRecord:
        record = self.contracts.get_by_id(contract_id)
        if record is None:
            raise ContractNotFoundError("Contract metadata not found")
        return record

    def _clean_values(self, values: dict[str, Any], *, include_document: bool = True) -> dict[str, Any]:
        cleaned = {
            "contract_number": self._normalize_text(values.get("contract_number")),
            "contract_title": self._normalize_text(values.get("contract_title")),
            "supplier_name": self._normalize_text(values.get("supplier_name")),
            "sign_date": values.get("sign_date"),
            "effective_from": values.get("effective_from"),
            "effective_to": values.get("effective_to"),
            "contract_value": values.get("contract_value"),
            "currency": self._normalize_currency(values.get("currency")),
            "status": self._validate_status(values.get("status"), allow_none=False),
            "notes": self._normalize_text(values.get("notes")),
        }
        if include_document:
            cleaned["document_id"] = self._normalize_required(values.get("document_id"), "document_id")
        if cleaned["effective_from"] and cleaned["effective_to"] and cleaned["effective_from"] > cleaned["effective_to"]:
            raise ContractOperationError("effective_from cannot be after effective_to")
        if isinstance(cleaned["contract_value"], Decimal) and cleaned["contract_value"] < 0:
            raise ContractOperationError("contract_value cannot be negative")
        return cleaned

    def _read(self, record: ContractRecord) -> dict[str, Any]:
        document = record.document
        return {
            "id": record.id,
            "document_id": record.document_id,
            "document_title": document.title if document else None,
            "document_number": document.document_number if document else None,
            "document_status": document.status if document else None,
            "contract_number": record.contract_number,
            "contract_title": record.contract_title,
            "supplier_name": record.supplier_name,
            "sign_date": record.sign_date,
            "effective_from": record.effective_from,
            "effective_to": record.effective_to,
            "contract_value": record.contract_value,
            "currency": record.currency,
            "status": record.status,
            "notes": record.notes,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    def _audit_snapshot(self, record: ContractRecord) -> dict[str, Any]:
        return {
            "document_id": record.document_id,
            "contract_number": record.contract_number,
            "supplier_name": record.supplier_name,
            "status": record.status,
            "sign_date": record.sign_date.isoformat() if record.sign_date else None,
            "effective_to": record.effective_to.isoformat() if record.effective_to else None,
        }

    def _validate_status(self, status: str | None, *, allow_none: bool) -> str | None:
        normalized = self._normalize_text(status)
        if normalized is None and allow_none:
            return None
        if normalized not in VALID_CONTRACT_STATUSES:
            raise ContractOperationError("Invalid contract status")
        return normalized

    def _normalize_text(self, value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    def _normalize_required(self, value: Any, field_name: str) -> str:
        normalized = self._normalize_text(value)
        if normalized is None:
            raise ContractOperationError(f"{field_name} is required")
        return normalized

    def _normalize_currency(self, value: Any) -> str:
        normalized = self._normalize_text(value) or "VND"
        return normalized.upper()
