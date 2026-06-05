from __future__ import annotations

import argparse
import hashlib
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.document import Document, DocumentChunk, DocumentFile, DocumentPage
from app.repositories.document_repository import DocumentRepository
from app.services.chunk_payload import build_qdrant_payload
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService
from app.services.search_service import SearchService


SMOKE_TITLE_PREFIX = "[SMOKE] Appendix review fixture"
FIXTURE_PATHS = (
    Path("/app/tests/fixtures/appendix_smoke/appendix_review_fixture.txt"),
    Path("tests/fixtures/appendix_smoke/appendix_review_fixture.txt"),
)


def run_smoke(*, keep_data: bool) -> dict[str, str]:
    db = SessionLocal()
    qdrant = QdrantService()
    created_document_id: str | None = None
    created_point_ids: list[str] = []
    try:
        _cleanup_existing_smoke_data(db=db, qdrant=qdrant)

        fixture_path = _resolve_fixture_path()
        fixture_text = fixture_path.read_text(encoding="utf-8")
        documents = DocumentRepository(db)
        document = documents.create_document(
            title=f"{SMOKE_TITLE_PREFIX} {uuid4().hex[:8]}",
            original_filename=fixture_path.name,
            file_path=str(fixture_path),
            content_type="text/plain",
            document_type="document",
            document_number="01/SMOKE-PL",
            issued_date=date(2026, 6, 5),
            issuing_agency="Phong Vat Tu",
            business_type="cong_van_den",
        )
        documents.create_file(
            document_id=document.id,
            original_filename=fixture_path.name,
            file_path=str(fixture_path),
            content_type="text/plain",
            file_size=fixture_path.stat().st_size,
            file_order=0,
            status="ocr_completed",
        )
        documents.create_page(document_id=document.id, page_number=1, text=fixture_text, confidence=0.42)
        appendix_chunk = documents.create_chunk(
            document_id=document.id,
            chunk_index=0,
            text=fixture_text,
            content_hash=hashlib.sha256(fixture_text.encode("utf-8")).hexdigest(),
            page_from=1,
            page_to=1,
            section_title="PHU LUC I",
            chunk_metadata={
                "doc_group": "A",
                "chunk_level": "section",
                "section_role": "appendix",
                "section_path": ["PHU LUC I", "DANH MUC VAT TU CAN DOI CHIEU"],
                "confidence": 0.42,
                "requires_review": True,
            },
        )
        documents.update_status(document, "searchable")
        db.commit()
        db.refresh(document)
        db.refresh(appendix_chunk)
        created_document_id = document.id
        created_point_ids.append(appendix_chunk.id)

        vector = EmbeddingService().embed(appendix_chunk.text)
        qdrant.upsert_chunk(
            point_id=appendix_chunk.id,
            vector=vector,
            payload=build_qdrant_payload(document, appendix_chunk),
        )
        documents.update_chunk_qdrant_point_id(appendix_chunk, appendix_chunk.id)
        db.commit()

        detail = DocumentService(db).get_document(document.id)
        active_appendix_chunks = [
            chunk for chunk in (detail.chunks if detail else []) if chunk.section_role == "appendix" and chunk.deleted_at is None
        ]
        _assert(bool(active_appendix_chunks), "Document detail does not include an appendix chunk")

        queue_items = DocumentService(db).list_review_queue_chunks(
            limit=10,
            offset=0,
            section_role="appendix",
            document_id=document.id,
            max_confidence=None,
        )
        _assert(any(item["id"] == appendix_chunk.id for item in queue_items), "Review queue did not return appendix smoke chunk")

        search_results = SearchService(db).semantic_search(
            query="danh muc vat tu phu luc smoke",
            limit=5,
            section_role="appendix",
        )
        _assert(any(item["chunk_id"] == appendix_chunk.id for item in search_results), "Semantic search did not return appendix smoke chunk")
        _assert(
            all(item["section_role"] == "appendix" for item in search_results),
            "Semantic search returned a non-appendix result while appendix filter was active",
        )

        reviewed_chunk = DocumentService(db).mark_chunk_reviewed(document_id=document.id, chunk_id=appendix_chunk.id)
        _assert(reviewed_chunk.requires_review is False, "Review action did not clear requires_review")

        queue_after_review = DocumentService(db).list_review_queue_chunks(
            limit=10,
            offset=0,
            section_role="appendix",
            document_id=document.id,
            max_confidence=None,
        )
        _assert(
            all(item["id"] != appendix_chunk.id for item in queue_after_review),
            "Reviewed appendix chunk still appears in review queue",
        )

        review_search_results = SearchService(db).semantic_search(
            query="danh muc vat tu phu luc smoke",
            limit=5,
            section_role="appendix",
            requires_review=True,
        )
        _assert(
            all(item["chunk_id"] != appendix_chunk.id for item in review_search_results),
            "Reviewed appendix chunk still appears in requires_review search",
        )

        if not keep_data:
            _soft_delete_document_tree(db=db, document_id=document.id)
            qdrant.delete_points(created_point_ids)
            db.commit()

        return {
            "document_id": document.id,
            "chunk_id": appendix_chunk.id,
            "cleanup": "kept" if keep_data else "removed",
        }
    except Exception:
        db.rollback()
        if created_point_ids:
            qdrant.delete_points(created_point_ids)
        if created_document_id:
            _soft_delete_document_tree(db=db, document_id=created_document_id)
            db.commit()
        raise
    finally:
        db.close()


def _resolve_fixture_path() -> Path:
    for path in FIXTURE_PATHS:
        if path.is_file():
            return path
    raise FileNotFoundError("Appendix smoke fixture not found")


def _cleanup_existing_smoke_data(*, db, qdrant: QdrantService) -> None:
    docs = list(db.scalars(select(Document).where(Document.title.like(f"{SMOKE_TITLE_PREFIX}%"))))
    point_ids = [
        chunk.qdrant_point_id or chunk.id
        for document in docs
        for chunk in document.chunks
        if chunk.qdrant_point_id or chunk.id
    ]
    if point_ids:
        qdrant.delete_points(point_ids)
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
    parser = argparse.ArgumentParser(description="Seed and verify real appendix data across detail, review queue, and search.")
    parser.add_argument("--keep-data", action="store_true", help="Keep the smoke document for manual UI inspection.")
    args = parser.parse_args()

    result = run_smoke(keep_data=args.keep_data)
    print(
        "appendix smoke passed: "
        f"document_id={result['document_id']} chunk_id={result['chunk_id']} cleanup={result['cleanup']}"
    )


if __name__ == "__main__":
    main()
