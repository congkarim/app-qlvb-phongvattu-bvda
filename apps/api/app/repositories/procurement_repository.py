from datetime import date, datetime, timezone

from sqlalchemy import asc, desc, exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.document import Document
from app.models.procurement import ProcurementRecord
from app.models.procurement_line_item import ProcurementLineItem


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
        item_name: str | None = None,
        item_code: str | None = None,
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
                item_name=item_name,
                item_code=item_code,
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
        item_name: str | None = None,
        item_code: str | None = None,
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
                item_name=item_name,
                item_code=item_code,
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
        item_name: str | None = None,
        item_code: str | None = None,
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
                item_name=item_name,
                item_code=item_code,
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
        item_name: str | None,
        item_code: str | None,
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
        line_item_condition = self._line_item_exists_condition(item_name=item_name, item_code=item_code)
        if line_item_condition is not None:
            conditions.append(line_item_condition)
        return conditions

    def _line_item_exists_condition(
        self,
        *,
        item_name: str | None,
        item_code: str | None,
    ):
        if not item_name and not item_code:
            return None
        line_conditions = [
            ProcurementLineItem.procurement_id == ProcurementRecord.id,
            ProcurementLineItem.deleted_at.is_(None),
        ]
        if item_name:
            line_conditions.append(ProcurementLineItem.item_name.ilike(f"%{item_name}%"))
        if item_code:
            line_conditions.append(ProcurementLineItem.item_code.ilike(f"%{item_code}%"))
        return exists(select(ProcurementLineItem.id).where(*line_conditions))
