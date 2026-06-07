from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService


SMOKE_TITLE_PREFIX = "[SMOKE] Documents pagination"


def run_smoke() -> dict[str, int]:
    db = SessionLocal()
    created_document_ids: list[str] = []
    try:
        _cleanup_existing_smoke_data(db)
        documents = DocumentRepository(db)
        base_time = datetime.now(timezone.utc).replace(microsecond=0)
        for index in range(3):
            document = documents.create_document(
                title=f"{SMOKE_TITLE_PREFIX} {index} {uuid4().hex[:8]}",
                original_filename=f"documents-pagination-{index}.txt",
                file_path=f"/tmp/documents-pagination-{index}.txt",
                content_type="text/plain",
                document_type="CV" if index < 2 else "QĐ",
                document_number=f"PG-{index}",
                issued_date=date(2026, 6, 5 + index),
                issuing_agency="Phong Vat Tu Smoke",
                business_type="incoming_dispatch" if index < 2 else "decision",
            )
            document.status = "searchable" if index < 2 else "failed"
            document.created_at = base_time + timedelta(seconds=index)
            document.updated_at = base_time + timedelta(seconds=index)
            db.add(document)
            db.flush()
            created_document_ids.append(document.id)
        db.commit()

        service = DocumentService(db)
        first_page = service.list_documents(limit=2, offset=0, query=SMOKE_TITLE_PREFIX, sort_by="created_at", sort_dir="asc")
        second_page = service.list_documents(limit=2, offset=2, query=SMOKE_TITLE_PREFIX, sort_by="created_at", sort_dir="asc")
        _assert(first_page["total"] == 3, f"Expected total=3, got {first_page['total']}")
        _assert(first_page["limit"] == 2 and first_page["offset"] == 0, "First page limit/offset mismatch")
        _assert(second_page["limit"] == 2 and second_page["offset"] == 2, "Second page limit/offset mismatch")
        first_ids = {document.id for document in first_page["items"]}
        second_ids = {document.id for document in second_page["items"]}
        _assert(len(first_page["items"]) == 2, "First page should contain 2 documents")
        _assert(len(second_page["items"]) == 1, "Second page should contain 1 document")
        _assert(first_ids.isdisjoint(second_ids), "Pagination returned duplicate documents across pages")

        filtered = service.list_documents(
            limit=10,
            offset=0,
            query=SMOKE_TITLE_PREFIX,
            status="searchable",
            document_type="CV",
            business_type="incoming_dispatch",
            sort_by="issued_date",
            sort_dir="desc",
        )
        _assert(filtered["total"] == 2, f"Expected filtered total=2, got {filtered['total']}")
        issued_dates = [document.issued_date for document in filtered["items"]]
        _assert(issued_dates == sorted(issued_dates, reverse=True), "Sort by issued_date desc is not stable")

        searched = service.list_documents(limit=10, offset=0, query="PG-2")
        _assert(searched["total"] == 1, f"Expected query by document_number to return 1 item, got {searched['total']}")
        _assert(searched["items"][0].document_number == "PG-2", "Search did not match document_number")

        missing_module = service.list_documents(
            limit=10,
            offset=0,
            query=SMOKE_TITLE_PREFIX,
            missing_module_metadata=True,
        )
        _assert(
            missing_module["total"] == 2,
            f"Expected missing_module_metadata total=2, got {missing_module['total']}",
        )
        _assert(
            all(item.missing_module_metadata for item in missing_module["items"]),
            "All filtered items should have missing_module_metadata=true",
        )

        _soft_delete_documents(db, created_document_ids)
        db.commit()
        return {
            "created": len(created_document_ids),
            "first_page": len(first_page["items"]),
            "second_page": len(second_page["items"]),
        }
    except Exception:
        db.rollback()
        if created_document_ids:
            _soft_delete_documents(db, created_document_ids)
            db.commit()
        raise
    finally:
        db.close()


def _cleanup_existing_smoke_data(db) -> None:
    docs = list(db.scalars(select(Document).where(Document.title.like(f"{SMOKE_TITLE_PREFIX}%"))))
    _soft_delete_documents(db, [document.id for document in docs])
    db.commit()


def _soft_delete_documents(db, document_ids: list[str]) -> None:
    deleted_at = datetime.now(timezone.utc)
    for document_id in document_ids:
        document = db.get(Document, document_id)
        if document is not None:
            document.deleted_at = deleted_at
            db.add(document)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    result = run_smoke()
    print(
        "documents pagination smoke passed: "
        f"created={result['created']} first_page={result['first_page']} second_page={result['second_page']}"
    )


if __name__ == "__main__":
    main()
