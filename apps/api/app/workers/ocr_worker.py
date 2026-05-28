import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.document import Document, OCRJob
from app.repositories.document_repository import DocumentRepository, OCRJobRepository
from app.services.chunking_service import ChunkingService
from app.services.document_content_service import DocumentContentService, DocumentPageContent
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService


logger = logging.getLogger(__name__)


class OCRWorker:
    def __init__(self, db: Session):
        self.db = db
        self.documents = DocumentRepository(db)
        self.ocr_jobs = OCRJobRepository(db)
        self.document_content = DocumentContentService()
        self.chunking = ChunkingService()
        self.embeddings = EmbeddingService()
        self.qdrant = QdrantService()

    def run_once(self) -> bool:
        job = self.ocr_jobs.get_next_pending_job()
        if not job:
            return False

        self.process_job(job)
        return True

    def process_job(self, job: OCRJob) -> None:
        job.status = "ocr_running"
        job.attempts += 1
        job.started_at = datetime.now(timezone.utc)
        self.db.add(job)
        self.db.commit()

        document: Document | None = None
        try:
            document = self.documents.get_document(job.document_id)
            if not document:
                raise ValueError(f"Document not found: {job.document_id}")

            self.documents.update_status(document, "ocr_running")
            page_contents = self.document_content.extract_pages(
                Path(document.file_path),
                document.original_filename,
            )
            for page_content in page_contents:
                self.documents.create_page(
                    document_id=document.id,
                    page_number=page_content.page_number,
                    text=page_content.text,
                    confidence=page_content.confidence,
                )

            self.documents.update_status(document, "chunking")
            chunk_payloads = self._create_page_chunks(page_contents)
            if not chunk_payloads:
                raise ValueError("No chunks created because extracted document content was empty")

            for chunk_index, chunk_payload in enumerate(chunk_payloads):
                chunk = self.documents.create_chunk(
                    document_id=document.id,
                    chunk_index=chunk_index,
                    text=str(chunk_payload["text"]),
                    content_hash=str(chunk_payload["content_hash"]),
                    page_from=int(chunk_payload["page_from"]),
                    page_to=int(chunk_payload["page_to"]),
                    section_title=chunk_payload["section_title"],
                )
                point_id = chunk.id
                vector = self.embeddings.embed(chunk.text)
                self.qdrant.upsert_chunk(
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
                chunk.qdrant_point_id = point_id
                self.db.add(chunk)

            self.documents.update_status(document, "searchable")
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            self.db.add(job)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if document:
                self.documents.update_status(document, "failed")
            job.status = "failed"
            job.error_message = str(exc)
            self.db.add(job)
            self.db.commit()
            logger.exception("OCR job failed: job_id=%s document_id=%s", job.id, job.document_id)

    def _create_page_chunks(self, page_contents: list[DocumentPageContent]) -> list[dict[str, str | int | None]]:
        chunks: list[dict[str, str | int | None]] = []
        for page_content in page_contents:
            for chunk_payload in self.chunking.create_chunks(page_content.text):
                chunks.append(
                    {
                        **chunk_payload,
                        "page_from": page_content.page_number,
                        "page_to": page_content.page_number,
                    }
                )
        return chunks


def run_forever(db_factory, poll_seconds: int = 5) -> None:
    while True:
        db = db_factory()
        try:
            processed = OCRWorker(db).run_once()
        finally:
            db.close()
        if not processed:
            time.sleep(poll_seconds)
