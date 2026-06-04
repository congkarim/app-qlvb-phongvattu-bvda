from __future__ import annotations

import argparse
from dataclasses import dataclass

from app.db.session import SessionLocal
from app.models.document import Document, DocumentPage
from app.repositories.document_repository import DocumentRepository
from app.services.ocr_chunking.adapter import create_chunk_payloads


@dataclass(frozen=True)
class BackfillSummary:
    scanned_documents: int = 0
    processed_documents: int = 0
    skipped_documents: int = 0
    updated_chunks: int = 0
    skipped_chunks: int = 0
    mismatched_documents: int = 0

    def add(self, result: BackfillResult) -> BackfillSummary:
        return BackfillSummary(
            scanned_documents=self.scanned_documents + 1,
            processed_documents=self.processed_documents + int(result.updated_chunks > 0),
            skipped_documents=self.skipped_documents + int(result.skipped_reason is not None),
            updated_chunks=self.updated_chunks + result.updated_chunks,
            skipped_chunks=self.skipped_chunks + result.skipped_chunks,
            mismatched_documents=self.mismatched_documents + int(result.chunk_count_mismatch),
        )


@dataclass(frozen=True)
class BackfillResult:
    document_id: str
    title: str
    existing_chunks: int
    generated_chunks: int
    updated_chunks: int = 0
    skipped_chunks: int = 0
    dry_run: bool = False
    skipped_reason: str | None = None

    @property
    def chunk_count_mismatch(self) -> bool:
        return self.existing_chunks != self.generated_chunks

    def to_log_line(self) -> str:
        status = "skipped" if self.skipped_reason else "dry-run" if self.dry_run else "updated"
        parts = [
            f"status={status}",
            f"document_id={self.document_id}",
            f"existing_chunks={self.existing_chunks}",
            f"generated_chunks={self.generated_chunks}",
            f"updated_chunks={self.updated_chunks}",
            f"skipped_chunks={self.skipped_chunks}",
            f"mismatch={str(self.chunk_count_mismatch).lower()}",
        ]
        if self.skipped_reason:
            parts.append(f"reason={self.skipped_reason}")
        return " ".join(parts)


@dataclass(frozen=True)
class PageContent:
    page_number: int
    text: str
    confidence: float


def backfill_chunk_metadata(
    *,
    document_ids: list[str],
    batch_size: int,
    limit: int | None,
    dry_run: bool,
    include_complete: bool,
) -> BackfillSummary:
    summary = BackfillSummary()

    if document_ids:
        for document_id in document_ids:
            result = _backfill_document_id(document_id=document_id, dry_run=dry_run)
            print(result.to_log_line())
            summary = summary.add(result)
        return summary

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
            query_offset = offset if dry_run or include_complete else 0
            candidates = documents.list_documents_for_chunk_metadata_backfill(
                limit=current_limit,
                offset=query_offset,
                missing_only=not include_complete,
            )
            if not candidates:
                break
            for document in candidates:
                result = _backfill_loaded_document(documents=documents, document=document, dry_run=dry_run)
                print(result.to_log_line())
                summary = summary.add(result)
            if dry_run:
                db.rollback()
            else:
                db.commit()
            processed += len(candidates)
            offset += len(candidates)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    return summary


def _backfill_document_id(*, document_id: str, dry_run: bool) -> BackfillResult:
    db = SessionLocal()
    try:
        documents = DocumentRepository(db)
        document = documents.get_document(document_id)
        if document is None:
            return BackfillResult(
                document_id=document_id,
                title="",
                existing_chunks=0,
                generated_chunks=0,
                dry_run=dry_run,
                skipped_reason="document_not_found",
            )
        result = _backfill_loaded_document(documents=documents, document=document, dry_run=dry_run)
        if dry_run:
            db.rollback()
        else:
            db.commit()
        return result
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _backfill_loaded_document(
    *,
    documents: DocumentRepository,
    document: Document,
    dry_run: bool,
) -> BackfillResult:
    pages = _active_pages(document.pages)
    chunks = [chunk for chunk in document.chunks if chunk.deleted_at is None]
    existing_chunks = len(chunks)
    if not pages:
        return BackfillResult(
            document_id=document.id,
            title=document.title,
            existing_chunks=existing_chunks,
            generated_chunks=0,
            dry_run=dry_run,
            skipped_reason="no_active_pages",
        )
    if not chunks:
        return BackfillResult(
            document_id=document.id,
            title=document.title,
            existing_chunks=0,
            generated_chunks=0,
            dry_run=dry_run,
            skipped_reason="no_active_chunks",
        )

    chunk_payloads = create_chunk_payloads(
        doc_id=document.id,
        document_type=document.document_type,
        page_contents=[
            PageContent(page_number=page.page_number, text=page.text, confidence=page.confidence)
            for page in pages
        ],
    )
    if not chunk_payloads:
        return BackfillResult(
            document_id=document.id,
            title=document.title,
            existing_chunks=existing_chunks,
            generated_chunks=0,
            dry_run=dry_run,
            skipped_reason="no_generated_chunks",
        )

    if dry_run:
        return BackfillResult(
            document_id=document.id,
            title=document.title,
            existing_chunks=existing_chunks,
            generated_chunks=len(chunk_payloads),
            updated_chunks=min(existing_chunks, len(chunk_payloads)),
            skipped_chunks=max(existing_chunks - len(chunk_payloads), 0),
            dry_run=True,
        )

    updated_chunks, skipped_chunks = documents.update_chunk_metadata_for_document(
        document_id=document.id,
        chunk_payloads=chunk_payloads,
    )
    return BackfillResult(
        document_id=document.id,
        title=document.title,
        existing_chunks=existing_chunks,
        generated_chunks=len(chunk_payloads),
        updated_chunks=updated_chunks,
        skipped_chunks=skipped_chunks,
    )


def _active_pages(pages: list[DocumentPage]) -> list[DocumentPage]:
    return sorted((page for page in pages if page.deleted_at is None), key=lambda page: page.page_number)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill structural metadata for existing document chunks from stored OCR pages.",
    )
    parser.add_argument("--document-id", action="append", default=[], help="Backfill one document id. Repeatable.")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--include-complete",
        action="store_true",
        help="Also scan documents whose chunks already have metadata.",
    )
    args = parser.parse_args()

    summary = backfill_chunk_metadata(
        document_ids=args.document_id,
        batch_size=args.batch_size,
        limit=args.limit,
        dry_run=args.dry_run,
        include_complete=args.include_complete,
    )
    print(
        "summary "
        f"scanned_documents={summary.scanned_documents} "
        f"processed_documents={summary.processed_documents} "
        f"skipped_documents={summary.skipped_documents} "
        f"updated_chunks={summary.updated_chunks} "
        f"skipped_chunks={summary.skipped_chunks} "
        f"mismatched_documents={summary.mismatched_documents}"
    )


if __name__ == "__main__":
    main()
