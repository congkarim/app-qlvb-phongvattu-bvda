from __future__ import annotations

import argparse
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.document_relation import DocumentRelation
from app.repositories.document_relation_repository import (
    DocumentRelationRepository,
    DocumentRelationSelfLinkError,
)
from app.repositories.document_repository import DocumentRepository

SMOKE_TITLE_PREFIX = "[SMOKE] Document relations repo"


def run_smoke(*, keep_data: bool) -> dict[str, str | int]:
    db = SessionLocal()
    created_document_ids: list[str] = []
    created_relation_id: str | None = None
    try:
        _cleanup_existing_smoke_data(db)
        suffix = uuid4().hex[:10]
        documents = DocumentRepository(db)
        relations = DocumentRelationRepository(db)

        source = documents.create_document(
            title=f"{SMOKE_TITLE_PREFIX} source {suffix}",
            original_filename=f"relations-repo-source-{suffix}.txt",
            file_path=f"/tmp/relations-repo-source-{suffix}.txt",
            content_type="text/plain",
            document_type="CV",
            document_number=f"CV-REL-SRC-{suffix}",
        )
        target = documents.create_document(
            title=f"{SMOKE_TITLE_PREFIX} target {suffix}",
            original_filename=f"relations-repo-target-{suffix}.txt",
            file_path=f"/tmp/relations-repo-target-{suffix}.txt",
            content_type="text/plain",
            document_type="QĐ",
            document_number=f"QD-REL-TGT-{suffix}",
        )
        created_document_ids.extend([source.id, target.id])
        db.commit()

        relation = relations.create(
            source_document_id=source.id,
            target_document_id=target.id,
            relation_type="references",
            notes="smoke relation",
        )
        created_relation_id = relation.id
        db.commit()

        outgoing = relations.list_outgoing(source.id)
        incoming = relations.list_incoming(target.id)
        if len(outgoing) != 1 or outgoing[0].id != relation.id:
            raise AssertionError(f"Expected 1 outgoing relation for source, got {len(outgoing)}")
        if len(incoming) != 1 or incoming[0].id != relation.id:
            raise AssertionError(f"Expected 1 incoming relation for target, got {len(incoming)}")
        if relations.count_active_for_document(source.id) != 1:
            raise AssertionError("Expected relation_count=1 for source document")

        duplicate = relations.find_active(
            source_document_id=source.id,
            target_document_id=target.id,
            relation_type="references",
        )
        if duplicate is None or duplicate.id != relation.id:
            raise AssertionError("find_active did not return the created relation")

        try:
            relations.create(
                source_document_id=source.id,
                target_document_id=source.id,
                relation_type="related",
            )
            db.flush()
        except DocumentRelationSelfLinkError:
            db.rollback()
        else:
            raise AssertionError("Expected DocumentRelationSelfLinkError for self-link")

        relations.soft_delete(relation)
        db.commit()

        if relations.list_outgoing(source.id):
            raise AssertionError("Expected no outgoing relations after soft delete")
        if relations.list_incoming(target.id):
            raise AssertionError("Expected no incoming relations after soft delete")
        if relations.get_by_id(relation.id) is not None:
            raise AssertionError("Expected get_by_id to return None after soft delete")

        return {
            "source_document_id": source.id,
            "target_document_id": target.id,
            "relation_id": created_relation_id or "",
            "cleanup": "kept" if keep_data else "removed",
        }
    except Exception:
        db.rollback()
        if not keep_data:
            _cleanup_created_data(db, document_ids=created_document_ids, relation_id=created_relation_id)
            db.commit()
        raise
    finally:
        if not keep_data:
            _cleanup_created_data(db, document_ids=created_document_ids, relation_id=created_relation_id)
            db.commit()
        db.close()


def _cleanup_existing_smoke_data(db) -> None:
    docs = list(db.scalars(select(Document).where(Document.title.like(f"{SMOKE_TITLE_PREFIX}%"))))
    for document in docs:
        _cleanup_created_data(db, document_ids=[document.id], relation_id=None)
    db.commit()


def _cleanup_created_data(
    db,
    *,
    document_ids: list[str],
    relation_id: str | None,
) -> None:
    deleted_at = datetime.now(timezone.utc)
    if relation_id:
        relation = db.get(DocumentRelation, relation_id)
        if relation and relation.deleted_at is None:
            relation.deleted_at = deleted_at
            db.add(relation)
    for document_id in document_ids:
        for relation in db.scalars(
            select(DocumentRelation).where(
                DocumentRelation.deleted_at.is_(None),
                (
                    (DocumentRelation.source_document_id == document_id)
                    | (DocumentRelation.target_document_id == document_id)
                ),
            )
        ):
            relation.deleted_at = deleted_at
            db.add(relation)
        document = db.get(Document, document_id)
        if document and document.deleted_at is None:
            document.deleted_at = deleted_at
            db.add(document)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test document_relations repository")
    parser.add_argument("--keep-data", action="store_true", help="Keep seeded smoke data")
    args = parser.parse_args()
    result = run_smoke(keep_data=args.keep_data)
    print("smoke_document_relations_repo: OK")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
