from datetime import date, datetime, timezone

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.contract import ContractRecord
from app.models.document import Document


class ContractRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_document(self, document_id: str) -> Document | None:
        stmt = select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def get_by_id(self, contract_id: str) -> ContractRecord | None:
        stmt = (
            select(ContractRecord)
            .where(ContractRecord.id == contract_id, ContractRecord.deleted_at.is_(None))
            .options(selectinload(ContractRecord.document))
        )
        return self.db.scalar(stmt)

    def get_active_by_document_id(self, document_id: str) -> ContractRecord | None:
        stmt = (
            select(ContractRecord)
            .where(ContractRecord.document_id == document_id, ContractRecord.deleted_at.is_(None))
            .options(selectinload(ContractRecord.document))
        )
        return self.db.scalar(stmt)

    def list_contracts(
        self,
        *,
        limit: int,
        offset: int,
        query: str | None = None,
        document_id: str | None = None,
        contract_number: str | None = None,
        supplier_name: str | None = None,
        status: str | None = None,
        sign_date_from: date | None = None,
        sign_date_to: date | None = None,
        effective_to_from: date | None = None,
        effective_to_to: date | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> list[ContractRecord]:
        stmt = (
            select(ContractRecord)
            .join(ContractRecord.document)
            .where(*self._conditions(
                query=query,
                document_id=document_id,
                contract_number=contract_number,
                supplier_name=supplier_name,
                status=status,
                sign_date_from=sign_date_from,
                sign_date_to=sign_date_to,
                effective_to_from=effective_to_from,
                effective_to_to=effective_to_to,
            ))
            .options(selectinload(ContractRecord.document))
        )
        sortable_columns = {
            "created_at": ContractRecord.created_at,
            "updated_at": ContractRecord.updated_at,
            "contract_number": ContractRecord.contract_number,
            "supplier_name": ContractRecord.supplier_name,
            "status": ContractRecord.status,
            "sign_date": ContractRecord.sign_date,
            "effective_to": ContractRecord.effective_to,
        }
        direction = asc if sort_dir == "asc" else desc
        sort_column = sortable_columns.get(sort_by, ContractRecord.created_at)
        stmt = stmt.order_by(direction(sort_column), ContractRecord.created_at.desc(), ContractRecord.id.desc())
        stmt = stmt.limit(limit).offset(offset)
        return list(self.db.scalars(stmt))

    def count_contracts(
        self,
        *,
        query: str | None = None,
        document_id: str | None = None,
        contract_number: str | None = None,
        supplier_name: str | None = None,
        status: str | None = None,
        sign_date_from: date | None = None,
        sign_date_to: date | None = None,
        effective_to_from: date | None = None,
        effective_to_to: date | None = None,
    ) -> int:
        stmt = (
            select(func.count(ContractRecord.id))
            .join(ContractRecord.document)
            .where(*self._conditions(
                query=query,
                document_id=document_id,
                contract_number=contract_number,
                supplier_name=supplier_name,
                status=status,
                sign_date_from=sign_date_from,
                sign_date_to=sign_date_to,
                effective_to_from=effective_to_from,
                effective_to_to=effective_to_to,
            ))
        )
        return int(self.db.scalar(stmt) or 0)

    def create(self, **values) -> ContractRecord:
        record = ContractRecord(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def update(self, record: ContractRecord, **values) -> ContractRecord:
        for key, value in values.items():
            setattr(record, key, value)
        self.db.add(record)
        self.db.flush()
        return record

    def soft_delete(self, record: ContractRecord) -> ContractRecord:
        record.deleted_at = datetime.now(timezone.utc)
        self.db.add(record)
        self.db.flush()
        return record

    def _conditions(
        self,
        *,
        query: str | None,
        document_id: str | None,
        contract_number: str | None,
        supplier_name: str | None,
        status: str | None,
        sign_date_from: date | None,
        sign_date_to: date | None,
        effective_to_from: date | None,
        effective_to_to: date | None,
    ):
        conditions = [ContractRecord.deleted_at.is_(None), Document.deleted_at.is_(None)]
        if query:
            pattern = f"%{query}%"
            conditions.append(
                or_(
                    ContractRecord.contract_number.ilike(pattern),
                    ContractRecord.contract_title.ilike(pattern),
                    ContractRecord.supplier_name.ilike(pattern),
                    Document.title.ilike(pattern),
                    Document.document_number.ilike(pattern),
                )
            )
        if document_id:
            conditions.append(ContractRecord.document_id == document_id)
        if contract_number:
            conditions.append(ContractRecord.contract_number.ilike(f"%{contract_number}%"))
        if supplier_name:
            conditions.append(ContractRecord.supplier_name.ilike(f"%{supplier_name}%"))
        if status:
            conditions.append(ContractRecord.status == status)
        if sign_date_from:
            conditions.append(ContractRecord.sign_date >= sign_date_from)
        if sign_date_to:
            conditions.append(ContractRecord.sign_date <= sign_date_to)
        if effective_to_from:
            conditions.append(ContractRecord.effective_to >= effective_to_from)
        if effective_to_to:
            conditions.append(ContractRecord.effective_to <= effective_to_to)
        return conditions
