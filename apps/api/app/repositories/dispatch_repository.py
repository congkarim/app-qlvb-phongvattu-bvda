from datetime import date, datetime, timezone

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.dispatch import DispatchRecord
from app.models.document import Document


class DispatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_document(self, document_id: str) -> Document | None:
        stmt = select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def get_by_id(self, dispatch_id: str) -> DispatchRecord | None:
        stmt = (
            select(DispatchRecord)
            .where(DispatchRecord.id == dispatch_id, DispatchRecord.deleted_at.is_(None))
            .options(selectinload(DispatchRecord.document))
        )
        return self.db.scalar(stmt)

    def get_active_by_document_id(self, document_id: str) -> DispatchRecord | None:
        stmt = (
            select(DispatchRecord)
            .where(DispatchRecord.document_id == document_id, DispatchRecord.deleted_at.is_(None))
            .options(selectinload(DispatchRecord.document))
        )
        return self.db.scalar(stmt)

    def list_document_ids_by_metadata(
        self,
        *,
        dispatch_type: str | None = None,
        document_number: str | None = None,
        issuing_agency: str | None = None,
        status: str | None = None,
    ) -> list[str]:
        stmt = (
            select(DispatchRecord.document_id)
            .join(DispatchRecord.document)
            .where(*self._conditions(
                query=None,
                document_id=None,
                dispatch_type=dispatch_type,
                document_number=document_number,
                issuing_agency=issuing_agency,
                status=status,
                issued_date_from=None,
                issued_date_to=None,
            ))
        )
        return list(self.db.scalars(stmt))

    def map_active_by_document_ids(self, document_ids: list[str]) -> dict[str, DispatchRecord]:
        if not document_ids:
            return {}
        stmt = (
            select(DispatchRecord)
            .where(
                DispatchRecord.document_id.in_(document_ids),
                DispatchRecord.deleted_at.is_(None),
            )
        )
        return {record.document_id: record for record in self.db.scalars(stmt)}

    def list_dispatches(
        self,
        *,
        limit: int,
        offset: int,
        query: str | None = None,
        document_id: str | None = None,
        dispatch_type: str | None = None,
        document_number: str | None = None,
        issuing_agency: str | None = None,
        status: str | None = None,
        issued_date_from: date | None = None,
        issued_date_to: date | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> list[DispatchRecord]:
        stmt = (
            select(DispatchRecord)
            .join(DispatchRecord.document)
            .where(*self._conditions(
                query=query,
                document_id=document_id,
                dispatch_type=dispatch_type,
                document_number=document_number,
                issuing_agency=issuing_agency,
                status=status,
                issued_date_from=issued_date_from,
                issued_date_to=issued_date_to,
            ))
            .options(selectinload(DispatchRecord.document))
        )
        sortable_columns = {
            "created_at": DispatchRecord.created_at,
            "updated_at": DispatchRecord.updated_at,
            "document_number": DispatchRecord.document_number,
            "dispatch_type": DispatchRecord.dispatch_type,
            "issuing_agency": DispatchRecord.issuing_agency,
            "status": DispatchRecord.status,
            "issued_date": DispatchRecord.issued_date,
        }
        direction = asc if sort_dir == "asc" else desc
        sort_column = sortable_columns.get(sort_by, DispatchRecord.created_at)
        stmt = stmt.order_by(direction(sort_column), DispatchRecord.created_at.desc(), DispatchRecord.id.desc())
        stmt = stmt.limit(limit).offset(offset)
        return list(self.db.scalars(stmt))

    def count_dispatches(
        self,
        *,
        query: str | None = None,
        document_id: str | None = None,
        dispatch_type: str | None = None,
        document_number: str | None = None,
        issuing_agency: str | None = None,
        status: str | None = None,
        issued_date_from: date | None = None,
        issued_date_to: date | None = None,
    ) -> int:
        stmt = (
            select(func.count(DispatchRecord.id))
            .join(DispatchRecord.document)
            .where(*self._conditions(
                query=query,
                document_id=document_id,
                dispatch_type=dispatch_type,
                document_number=document_number,
                issuing_agency=issuing_agency,
                status=status,
                issued_date_from=issued_date_from,
                issued_date_to=issued_date_to,
            ))
        )
        return int(self.db.scalar(stmt) or 0)

    def create(self, **values) -> DispatchRecord:
        record = DispatchRecord(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def update(self, record: DispatchRecord, **values) -> DispatchRecord:
        for key, value in values.items():
            setattr(record, key, value)
        self.db.add(record)
        self.db.flush()
        return record

    def soft_delete(self, record: DispatchRecord) -> DispatchRecord:
        record.deleted_at = datetime.now(timezone.utc)
        self.db.add(record)
        self.db.flush()
        return record

    def _conditions(
        self,
        *,
        query: str | None,
        document_id: str | None,
        dispatch_type: str | None,
        document_number: str | None,
        issuing_agency: str | None,
        status: str | None,
        issued_date_from: date | None,
        issued_date_to: date | None,
    ):
        conditions = [DispatchRecord.deleted_at.is_(None), Document.deleted_at.is_(None)]
        if query:
            pattern = f"%{query}%"
            conditions.append(
                or_(
                    DispatchRecord.document_number.ilike(pattern),
                    DispatchRecord.document_symbol.ilike(pattern),
                    DispatchRecord.issuing_agency.ilike(pattern),
                    DispatchRecord.recipient.ilike(pattern),
                    DispatchRecord.excerpt.ilike(pattern),
                    Document.title.ilike(pattern),
                    Document.document_number.ilike(pattern),
                )
            )
        if document_id:
            conditions.append(DispatchRecord.document_id == document_id)
        if dispatch_type:
            conditions.append(DispatchRecord.dispatch_type == dispatch_type)
        if document_number:
            conditions.append(DispatchRecord.document_number.ilike(f"%{document_number}%"))
        if issuing_agency:
            conditions.append(DispatchRecord.issuing_agency.ilike(f"%{issuing_agency}%"))
        if status:
            conditions.append(DispatchRecord.status == status)
        if issued_date_from:
            conditions.append(DispatchRecord.issued_date >= issued_date_from)
        if issued_date_to:
            conditions.append(DispatchRecord.issued_date <= issued_date_to)
        return conditions
