from __future__ import annotations

import argparse
import hashlib
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.document import Document
from app.services.document_relation_suggestion_service import DocumentRelationSuggestionService
from app.repositories.document_repository import DocumentRepository

SMOKE_TITLE_PREFIX = "[SMOKE] Relation suggestions repo"


def run_smoke(*, keep_data: bool) -> dict[str, str | int]:
    db = SessionLocal()
    created_document_ids: list[str] = []
    try:
        _cleanup_existing_smoke_data(db)
        suffix = uuid4().hex[:10]
        documents = DocumentRepository(db)
        service = DocumentRelationSuggestionService(db)

        target = documents.create_document(
            title=f"{SMOKE_TITLE_PREFIX} QD {suffix}",
            original_filename=f"rel-suggest-qd-{suffix}.txt",
            file_path=f"/tmp/rel-suggest-qd-{suffix}.txt",
            content_type="text/plain",
            document_type="QĐ",
            document_number=f"01/QD-REL-{suffix}",
            business_type="decision",
        )
        source = documents.create_document(
            title=f"{SMOKE_TITLE_PREFIX} CV {suffix}",
            original_filename=f"rel-suggest-cv-{suffix}.txt",
            file_path=f"/tmp/rel-suggest-cv-{suffix}.txt",
            content_type="text/plain",
            document_type="CV",
            document_number=f"01/CV-REL-{suffix}",
            business_type="incoming_dispatch",
        )
        created_document_ids.extend([target.id, source.id])
        documents.update_status(target, "searchable")
        documents.update_status(source, "searchable")

        chunk_text = f"Căn cứ Quyết định số 01/QD-REL-{suffix} của Giám đốc về việc quản lý vật tư."
        documents.create_chunk(
            document_id=source.id,
            chunk_index=0,
            text=chunk_text,
            content_hash=hashlib.sha256(chunk_text.encode("utf-8")).hexdigest(),
            page_from=1,
            page_to=1,
            section_role="article",
        )
        db.commit()

        result = service.suggest_relations(source.id)
        if result["candidate_count"] != 1:
            raise AssertionError(f"Expected 1 suggestion, got {result['candidate_count']}")
        suggestion = result["suggestions"][0]
        if suggestion["target_document_id"] != target.id:
            raise AssertionError("Suggestion target_document_id mismatch")
        if suggestion["relation_type"] != "references":
            raise AssertionError(f"Expected references, got {suggestion['relation_type']}")

        empty = service.suggest_relations(target.id)
        if empty["candidate_count"] != 0:
            raise AssertionError("Expected no suggestions for QD without reference chunk")

        documents.update_status(source, "uploaded")
        db.commit()
        non_searchable = service.suggest_relations(source.id)
        if non_searchable["candidate_count"] != 0:
            raise AssertionError("Expected empty suggestions for non-searchable source")

        return {
            "source_document_id": source.id,
            "target_document_id": target.id,
            "candidate_count": result["candidate_count"],
            "cleanup": "kept" if keep_data else "removed",
        }
    except Exception:
        db.rollback()
        if not keep_data:
            _cleanup_created_data(db, document_ids=created_document_ids)
            db.commit()
        raise
    finally:
        if not keep_data:
            _cleanup_created_data(db, document_ids=created_document_ids)
            db.commit()
        db.close()


def _cleanup_existing_smoke_data(db) -> None:
    docs = list(db.scalars(select(Document).where(Document.title.like(f"{SMOKE_TITLE_PREFIX}%"))))
    for document in docs:
        _cleanup_created_data(db, document_ids=[document.id])
    db.commit()


def _cleanup_created_data(db, *, document_ids: list[str]) -> None:
    deleted_at = datetime.now(timezone.utc)
    for document_id in document_ids:
        document = db.get(Document, document_id)
        if document and document.deleted_at is None:
            document.deleted_at = deleted_at
            db.add(document)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test relation suggestion repository/service")
    parser.add_argument("--keep-data", action="store_true", help="Keep seeded smoke data")
    args = parser.parse_args()
    result = run_smoke(keep_data=args.keep_data)
    print("smoke_document_relation_suggestions_repo: OK")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
