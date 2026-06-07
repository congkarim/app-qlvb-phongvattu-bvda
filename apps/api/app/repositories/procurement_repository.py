from datetime import date, datetime, timezone

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.document import Document
from app.models.procurement import ProcurementRecord


class ProcurementRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_document(self, document_id: str) -> Document | None:
        stmt = select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def get_by_id(self, procurement_id: str) -> ProcurementRecord | None:
        stmt = (
            select(ProcurementRecord)
            .where(ProcurementRecord.id == procurement_id, ProcurementRecord.deleted_at.is_(None))
            .options(selectinload(ProcurementRecord.document))
        )
        return self.db.scalar(stmt)

    def get_active_by_document_id(self, document_id: str) -> ProcurementRecord | None:
        stmt = (
            select(ProcurementRecord)
            .where(ProcurementRecord.document_id == document_id, ProcurementRecord.deleted_at.is_(None))
            .options(selectinload(ProcurementRecord.document))
        )
        return self.db.scalar(stmt)

    def list_document_ids_by_metadata(
        self,
        *,
        procurement_kind: str | None = None,
        reference_number: str | None = None,
        requesting_unit: str | None = None,
        status: str | None = None,
    ) -> list[str]:
        stmt = (
            select(ProcurementRecord.document_id)
            .join(ProcurementRecord.document)
            .where(*self._conditions(
                query=None,
                document_id=None,
                procurement_kind=procurement_kind,
                reference_number=reference_number,
                requesting_unit=requesting_unit,
                status=status,
                requested_date_from=None,
                requested_date_to=None,
            ))
        )
        return list(self.db.scalars(stmt))

    def map_active_by_document_ids(self, document_ids: list[str]) -> dict[str, ProcurementRecord]:
        if not document_ids:
            return {}
        stmt = (
            select(ProcurementRecord)
            .where(
                ProcurementRecord.document_id.in_(document_ids),
                ProcurementRecord.deleted_at.is_(None),
            )
        )
        return {record.document_id: record for record in self.db.scalars(stmt)}

    def list_procurements(
        self,
        *,
        limit: int,
        offset: int,
        query: str | None = None,
        document_id: str | None = None,
        procurement_kind: str | None = None,
        reference_number: str | None = None,
        requesting_unit: str | None = None,
        status: str | None = None,
        requested_date_from: date | None = None,
        requested_date_to: date | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> list[ProcurementRecord]:
        stmt = (
            select(ProcurementRecord)
            .join(ProcurementRecord.document)
            .where(*self._conditions(
                query=query,
                document_id=document_id,
                procurement_kind=procurement_kind,
                reference_number=reference_number,
                requesting_unit=requesting_unit,
                status=status,
                requested_date_from=requested_date_from,
                requested_date_to=requested_date_to,
            ))
            .options(selectinload(ProcurementRecord.document))
        )
        sortable_columns = {
            "created_at": ProcurementRecord.created_at,
            "updated_at": ProcurementRecord.updated_at,
            "reference_number": ProcurementRecord.reference_number,
            "procurement_kind": ProcurementRecord.procurement_kind,
            "requesting_unit": ProcurementRecord.requesting_unit,
            "status": ProcurementRecord.status,
            "requested_date": ProcurementRecord.requested_date,
            "estimated_value": ProcurementRecord.estimated_value,
        }
        direction = asc if sort_dir == "asc" else desc
        sort_column = sortable_columns.get(sort_by, ProcurementRecord.created_at)
        stmt = stmt.order_by(direction(sort_column), ProcurementRecord.created_at.desc(), ProcurementRecord.id.desc())
        stmt = stmt.limit(limit).offset(offset)
        return list(self.db.scalars(stmt))

    def count_procurements(
        self,
        *,
        query: str | None = None,
        document_id: str | None = None,
        procurement_kind: str | None = None,
        reference_number: str | None = None,
        requesting_unit: str | None = None,
        status: str | None = None,
        requested_date_from: date | None = None,
        requested_date_to: date | None = None,
    ) -> int:
        stmt = (
            select(func.count(ProcurementRecord.id))
            .join(ProcurementRecord.document)
            .where(*self._conditions(
                query=query,
                document_id=document_id,
                procurement_kind=procurement_kind,
                reference_number=reference_number,
                requesting_unit=requesting_unit,
                status=status,
                requested_date_from=requested_date_from,
                requested_date_to=requested_date_to,
            ))
        )
        return int(self.db.scalar(stmt) or 0)

    def create(self, **values) -> ProcurementRecord:
        record = ProcurementRecord(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def update(self, record: ProcurementRecord, **values) -> ProcurementRecord:
        for key, value in values.items():
            setattr(record, key, value)
        self.db.add(record)
        self.db.flush()
        return record

    def soft_delete(self, record: ProcurementRecord) -> ProcurementRecord:
        record.deleted_at = datetime.now(timezone.utc)
        self.db.add(record)
        self.db.flush()
        return record

    def _conditions(
        self,
        *,
        query: str | None,
        document_id: str | None,
        procurement_kind: str | None,
        reference_number: str | None,
        requesting_unit: str | None,
        status: str | None,
        requested_date_from: date | None,
        requested_date_to: date | None,
    ):
        conditions = [ProcurementRecord.deleted_at.is_(None), Document.deleted_at.is_(None)]
        if query:
            pattern = f"%{query}%"
            conditions.append(
                or_(
                    ProcurementRecord.reference_number.ilike(pattern),
                    ProcurementRecord.title_summary.ilike(pattern),
                    ProcurementRecord.requesting_unit.ilike(pattern),
                    Document.title.ilike(pattern),
                    Document.document_number.ilike(pattern),
                )
            )
        if document_id:
            conditions.append(ProcurementRecord.document_id == document_id)
        if procurement_kind:
            conditions.append(ProcurementRecord.procurement_kind == procurement_kind)
        if reference_number:
            conditions.append(ProcurementRecord.reference_number.ilike(f"%{reference_number}%"))
        if requesting_unit:
            conditions.append(ProcurementRecord.requesting_unit.ilike(f"%{requesting_unit}%"))
        if status:
            conditions.append(ProcurementRecord.status == status)
        if requested_date_from:
            conditions.append(ProcurementRecord.requested_date >= requested_date_from)
        if requested_date_to:
            conditions.append(ProcurementRecord.requested_date <= requested_date_to)
        return conditions
