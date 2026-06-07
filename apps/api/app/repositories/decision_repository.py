from datetime import date, datetime, timezone

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.decision import DecisionRecord
from app.models.document import Document


class DecisionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_document(self, document_id: str) -> Document | None:
        stmt = select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def get_by_id(self, decision_id: str) -> DecisionRecord | None:
        stmt = (
            select(DecisionRecord)
            .where(DecisionRecord.id == decision_id, DecisionRecord.deleted_at.is_(None))
            .options(selectinload(DecisionRecord.document))
        )
        return self.db.scalar(stmt)

    def get_active_by_document_id(self, document_id: str) -> DecisionRecord | None:
        stmt = (
            select(DecisionRecord)
            .where(DecisionRecord.document_id == document_id, DecisionRecord.deleted_at.is_(None))
            .options(selectinload(DecisionRecord.document))
        )
        return self.db.scalar(stmt)

    def list_document_ids_by_metadata(
        self,
        *,
        decision_kind: str | None = None,
        document_number: str | None = None,
        issuing_agency: str | None = None,
        status: str | None = None,
        effective_from: date | None = None,
        effective_to: date | None = None,
    ) -> list[str]:
        stmt = (
            select(DecisionRecord.document_id)
            .join(DecisionRecord.document)
            .where(*self._conditions(
                query=None,
                document_id=None,
                decision_kind=decision_kind,
                document_number=document_number,
                issuing_agency=issuing_agency,
                status=status,
                issued_date_from=None,
                issued_date_to=None,
                effective_from=effective_from,
                effective_to=effective_to,
            ))
        )
        return list(self.db.scalars(stmt))

    def list_decisions(
        self,
        *,
        limit: int,
        offset: int,
        query: str | None = None,
        document_id: str | None = None,
        decision_kind: str | None = None,
        document_number: str | None = None,
        issuing_agency: str | None = None,
        status: str | None = None,
        issued_date_from: date | None = None,
        issued_date_to: date | None = None,
        effective_from: date | None = None,
        effective_to: date | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> list[DecisionRecord]:
        stmt = (
            select(DecisionRecord)
            .join(DecisionRecord.document)
            .where(*self._conditions(
                query=query,
                document_id=document_id,
                decision_kind=decision_kind,
                document_number=document_number,
                issuing_agency=issuing_agency,
                status=status,
                issued_date_from=issued_date_from,
                issued_date_to=issued_date_to,
                effective_from=effective_from,
                effective_to=effective_to,
            ))
            .options(selectinload(DecisionRecord.document))
        )
        sortable_columns = {
            "created_at": DecisionRecord.created_at,
            "updated_at": DecisionRecord.updated_at,
            "document_number": DecisionRecord.document_number,
            "decision_kind": DecisionRecord.decision_kind,
            "issuing_agency": DecisionRecord.issuing_agency,
            "status": DecisionRecord.status,
            "issued_date": DecisionRecord.issued_date,
            "effective_from": DecisionRecord.effective_from,
            "effective_to": DecisionRecord.effective_to,
        }
        direction = asc if sort_dir == "asc" else desc
        sort_column = sortable_columns.get(sort_by, DecisionRecord.created_at)
        stmt = stmt.order_by(direction(sort_column), DecisionRecord.created_at.desc(), DecisionRecord.id.desc())
        stmt = stmt.limit(limit).offset(offset)
        return list(self.db.scalars(stmt))

    def count_decisions(
        self,
        *,
        query: str | None = None,
        document_id: str | None = None,
        decision_kind: str | None = None,
        document_number: str | None = None,
        issuing_agency: str | None = None,
        status: str | None = None,
        issued_date_from: date | None = None,
        issued_date_to: date | None = None,
        effective_from: date | None = None,
        effective_to: date | None = None,
    ) -> int:
        stmt = (
            select(func.count(DecisionRecord.id))
            .join(DecisionRecord.document)
            .where(*self._conditions(
                query=query,
                document_id=document_id,
                decision_kind=decision_kind,
                document_number=document_number,
                issuing_agency=issuing_agency,
                status=status,
                issued_date_from=issued_date_from,
                issued_date_to=issued_date_to,
                effective_from=effective_from,
                effective_to=effective_to,
            ))
        )
        return int(self.db.scalar(stmt) or 0)

    def create(self, **values) -> DecisionRecord:
        record = DecisionRecord(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def update(self, record: DecisionRecord, **values) -> DecisionRecord:
        for key, value in values.items():
            setattr(record, key, value)
        self.db.add(record)
        self.db.flush()
        return record

    def soft_delete(self, record: DecisionRecord) -> DecisionRecord:
        record.deleted_at = datetime.now(timezone.utc)
        self.db.add(record)
        self.db.flush()
        return record

    def _conditions(
        self,
        *,
        query: str | None,
        document_id: str | None,
        decision_kind: str | None,
        document_number: str | None,
        issuing_agency: str | None,
        status: str | None,
        issued_date_from: date | None,
        issued_date_to: date | None,
        effective_from: date | None,
        effective_to: date | None,
    ):
        conditions = [DecisionRecord.deleted_at.is_(None), Document.deleted_at.is_(None)]
        if query:
            pattern = f"%{query}%"
            conditions.append(
                or_(
                    DecisionRecord.document_number.ilike(pattern),
                    DecisionRecord.document_symbol.ilike(pattern),
                    DecisionRecord.issuing_agency.ilike(pattern),
                    DecisionRecord.excerpt.ilike(pattern),
                    Document.title.ilike(pattern),
                    Document.document_number.ilike(pattern),
                )
            )
        if document_id:
            conditions.append(DecisionRecord.document_id == document_id)
        if decision_kind:
            conditions.append(DecisionRecord.decision_kind == decision_kind)
        if document_number:
            conditions.append(DecisionRecord.document_number.ilike(f"%{document_number}%"))
        if issuing_agency:
            conditions.append(DecisionRecord.issuing_agency.ilike(f"%{issuing_agency}%"))
        if status:
            conditions.append(DecisionRecord.status == status)
        if issued_date_from:
            conditions.append(DecisionRecord.issued_date >= issued_date_from)
        if issued_date_to:
            conditions.append(DecisionRecord.issued_date <= issued_date_to)
        if effective_from:
            conditions.append(DecisionRecord.effective_from >= effective_from)
        if effective_to:
            conditions.append(DecisionRecord.effective_to <= effective_to)
        return conditions
