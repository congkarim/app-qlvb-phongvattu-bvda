from __future__ import annotations

import argparse
import hashlib
from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.document import Document, DocumentChunk, DocumentFile, DocumentPage
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService


SMOKE_TITLE_PREFIX = "[SMOKE] Review queue pagination"


def run_smoke(*, keep_data: bool) -> dict[str, int | str]:
    db = SessionLocal()
    created_document_id: str | None = None
    try:
        _cleanup_existing_smoke_data(db)
        document_id = _seed_review_queue_data(db)
        created_document_id = document_id
        service = DocumentService(db)

        first_page = service.list_review_queue_chunks(limit=3, offset=0, document_id=document_id)
        second_page = service.list_review_queue_chunks(limit=3, offset=3, document_id=document_id)
        first_ids = {item["id"] for item in first_page["items"]}
        second_ids = {item["id"] for item in second_page["items"]}
        _assert(first_page["total"] == 7, f"Expected total=7, got {first_page['total']}")
        _assert(first_page["limit"] == 3 and first_page["offset"] == 0, "First page limit/offset mismatch")
        _assert(second_page["limit"] == 3 and second_page["offset"] == 3, "Second page limit/offset mismatch")
        _assert(len(first_ids) == 3, "First page should contain 3 unique chunks")
        _assert(len(second_ids) == 3, "Second page should contain 3 unique chunks")
        _assert(first_ids.isdisjoint(second_ids), "Review queue pages returned duplicate chunks")

        appendix_page = service.list_review_queue_chunks(
            limit=10,
            offset=0,
            section_role="appendix",
            document_id=document_id,
        )
        _assert(appendix_page["total"] == 3, f"Expected appendix total=3, got {appendix_page['total']}")
        _assert(
            all(item["section_role"] == "appendix" for item in appendix_page["items"]),
            "Appendix filter returned non-appendix chunks",
        )

        low_confidence_page = service.list_review_queue_chunks(
            limit=10,
            offset=0,
            document_id=document_id,
            max_confidence=0.65,
        )
        _assert(low_confidence_page["total"] == 4, f"Expected low confidence total=4, got {low_confidence_page['total']}")
        _assert(
            all((item["chunk_confidence"] or 0) <= 0.65 for item in low_confidence_page["items"]),
            "Low confidence filter returned high-confidence chunks",
        )

        if not keep_data:
            _soft_delete_document_tree(db=db, document_id=document_id)
            db.commit()

        return {
            "document_id": document_id,
            "total": first_page["total"],
            "first_page": len(first_page["items"]),
            "second_page": len(second_page["items"]),
            "cleanup": "kept" if keep_data else "removed",
        }
    except Exception:
        db.rollback()
        if created_document_id and not keep_data:
            _soft_delete_document_tree(db=db, document_id=created_document_id)
            db.commit()
        raise
    finally:
        db.close()


def _seed_review_queue_data(db) -> str:
    suffix = uuid4().hex[:8]
    documents = DocumentRepository(db)
    document = documents.create_document(
        title=f"{SMOKE_TITLE_PREFIX} {suffix}",
        original_filename=f"review-queue-pagination-{suffix}.txt",
        file_path=f"/tmp/review-queue-pagination-{suffix}.txt",
        content_type="text/plain",
        document_type="CV",
        document_number=f"RQ-PAGE-{suffix}",
        issued_date=date(2026, 6, 5),
        issuing_agency="Phong Vat Tu Smoke",
        business_type="incoming_dispatch",
    )
    documents.create_file(
        document_id=document.id,
        original_filename=f"review-queue-pagination-{suffix}.txt",
        file_path=f"/tmp/review-queue-pagination-{suffix}.txt",
        content_type="text/plain",
        file_size=128,
        file_order=0,
        status="ocr_completed",
    )
    documents.create_page(
        document_id=document.id,
        page_number=1,
        text=f"Review queue pagination smoke {suffix}",
        confidence=0.7,
    )
    confidences = [0.41, 0.52, 0.63, 0.64, 0.72, 0.83, 0.91]
    for index, confidence in enumerate(confidences):
        section_role = "appendix" if index in {0, 2, 4} else "unknown"
        text = f"review queue pagination smoke {suffix} chunk {index} role {section_role}"
        documents.create_chunk(
            document_id=document.id,
            chunk_index=index,
            text=text,
            content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            page_from=1,
            page_to=1,
            section_title=f"SMOKE CHUNK {index}",
            doc_group="A",
            chunk_level="section",
            section_role=section_role,
            section_path=[f"SMOKE {index}"],
            chunk_confidence=confidence,
            requires_review=True,
        )
    documents.update_status(document, "searchable")
    db.commit()
    return document.id


def _cleanup_existing_smoke_data(db) -> None:
    docs = list(db.scalars(select(Document).where(Document.title.like(f"{SMOKE_TITLE_PREFIX}%"))))
    for document in docs:
        _soft_delete_document_tree(db=db, document_id=document.id)
    db.commit()


def _soft_delete_document_tree(*, db, document_id: str) -> None:
    deleted_at = datetime.now(timezone.utc)
    for model in (DocumentChunk, DocumentPage, DocumentFile):
        for row in db.scalars(select(model).where(model.document_id == document_id)):
            row.deleted_at = deleted_at
            db.add(row)
    document = db.get(Document, document_id)
    if document is not None:
        document.deleted_at = deleted_at
        db.add(document)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed and verify review queue pagination with multiple pages.")
    parser.add_argument("--keep-data", action="store_true", help="Keep smoke document for UI debugging.")
    args = parser.parse_args()

    result = run_smoke(keep_data=args.keep_data)
    print(
        "review queue pagination smoke passed: "
        f"document_id={result['document_id']} total={result['total']} "
        f"first_page={result['first_page']} second_page={result['second_page']} cleanup={result['cleanup']}"
    )


if __name__ == "__main__":
    main()
