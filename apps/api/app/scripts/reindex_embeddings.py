from __future__ import annotations

import argparse

from app.db.session import SessionLocal
from app.repositories.document_repository import DocumentRepository
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService


def reindex_embeddings(*, batch_size: int, limit: int | None, dry_run: bool) -> int:
    embeddings = EmbeddingService()
    qdrant = QdrantService()
    processed = 0
    offset = 0

    while True:
        remaining = None if limit is None else max(limit - processed, 0)
        if remaining == 0:
            break
        current_limit = min(batch_size, remaining) if remaining is not None else batch_size

        db = SessionLocal()
        try:
            documents = DocumentRepository(db)
            chunks = documents.list_chunks_for_indexing(limit=current_limit, offset=offset)
            if not chunks:
                break
            if dry_run:
                processed += len(chunks)
                offset += len(chunks)
                continue

            vectors = embeddings.embed_many([chunk.text for chunk in chunks])
            for chunk, vector in zip(chunks, vectors, strict=True):
                document = chunk.document
                point_id = chunk.id
                qdrant.upsert_chunk(
                    point_id=point_id,
                    vector=vector,
                    payload={
                        "document_id": document.id,
                        "chunk_id": chunk.id,
                        "text": chunk.text,
                        "title": document.title,
                        "document_type": document.document_type,
                        "department_id": document.department_id,
                        "page_from": chunk.page_from,
                        "page_to": chunk.page_to,
                    },
                )
                documents.update_chunk_qdrant_point_id(chunk, point_id)

            db.commit()
            processed += len(chunks)
            offset += len(chunks)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    return processed


def main() -> None:
    parser = argparse.ArgumentParser(description="Reindex document chunks into the configured Qdrant collection.")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    processed = reindex_embeddings(batch_size=args.batch_size, limit=args.limit, dry_run=args.dry_run)
    mode = "dry-run" if args.dry_run else "indexed"
    print(f"{mode}: {processed} chunks")


if __name__ == "__main__":
    main()
