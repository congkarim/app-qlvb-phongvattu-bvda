from __future__ import annotations

import argparse
from pathlib import Path

from app.db.session import SessionLocal
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.services.chunking_service import ChunkingService
from app.services.document_content_service import DocumentContentService, DocumentPageContent
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService


def reprocess_document(*, document_id: str, dry_run: bool, batch_size: int) -> dict[str, object]:
    document_content = DocumentContentService()
    chunking = ChunkingService()
    embeddings = EmbeddingService()
    qdrant = QdrantService()

    db = SessionLocal()
    try:
        documents = DocumentRepository(db)
        document = documents.get_document(document_id)
        if document is None:
            raise ValueError(f"Document not found: {document_id}")

        old_page_count = len([page for page in document.pages if page.deleted_at is None])
        old_chunk_count = len([chunk for chunk in document.chunks if chunk.deleted_at is None])
        page_contents = document_content.extract_pages(Path(document.file_path), document.original_filename)
        chunk_payloads = _create_page_chunks(chunking, page_contents)
        if not chunk_payloads:
            raise ValueError("No chunks created because extracted document content was empty")

        summary: dict[str, object] = {
            "document_id": document.id,
            "filename": document.original_filename,
            "dry_run": dry_run,
            "old_pages": old_page_count,
            "new_pages": len(page_contents),
            "old_chunks": old_chunk_count,
            "new_chunks": len(chunk_payloads),
            "average_confidence": round(
                sum(page.confidence for page in page_contents) / max(len(page_contents), 1),
                4,
            ),
        }
        if dry_run:
            db.rollback()
            return summary

        documents.update_status(document, "ocr_running")
        documents.replace_pages_for_document(
            document_id=document.id,
            pages=[
                {
                    "page_number": page.page_number,
                    "text": page.text,
                    "confidence": page.confidence,
                }
                for page in page_contents
            ],
        )
        documents.update_status(document, "chunking")
        chunks, deleted_chunks = documents.replace_chunks_for_document(
            document_id=document.id,
            chunks=chunk_payloads,
        )

        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            vectors = embeddings.embed_many([chunk.text for chunk in batch])
            for chunk, vector in zip(batch, vectors, strict=True):
                document_for_chunk: Document = chunk.document or document
                point_id = chunk.id
                qdrant.upsert_chunk(
                    point_id=point_id,
                    vector=vector,
                    payload={
                        "document_id": document.id,
                        "chunk_id": chunk.id,
                        "text": chunk.text,
                        "title": document_for_chunk.title,
                        "document_type": document_for_chunk.document_type,
                        "department_id": document_for_chunk.department_id,
                        "page_from": chunk.page_from,
                        "page_to": chunk.page_to,
                        "content_hash": chunk.content_hash,
                    },
                )
                documents.update_chunk_qdrant_point_id(chunk, point_id)

        qdrant.delete_points([chunk.qdrant_point_id or chunk.id for chunk in deleted_chunks])
        documents.update_status(document, "searchable")
        db.commit()
        summary["deleted_chunks"] = len(deleted_chunks)
        return summary
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _create_page_chunks(
    chunking: ChunkingService,
    page_contents: list[DocumentPageContent],
) -> list[dict[str, str | int | None]]:
    chunks: list[dict[str, str | int | None]] = []
    for page_content in page_contents:
        for chunk_payload in chunking.create_chunks(page_content.text):
            chunks.append(
                {
                    **chunk_payload,
                    "page_from": page_content.page_number,
                    "page_to": page_content.page_number,
                }
            )
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Reprocess existing documents from their original uploaded files.")
    parser.add_argument("--document-id", action="append", required=True, help="Document ID to reprocess. Repeatable.")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    for document_id in args.document_id:
        summary = reprocess_document(document_id=document_id, dry_run=args.dry_run, batch_size=args.batch_size)
        print(summary)


if __name__ == "__main__":
    main()
