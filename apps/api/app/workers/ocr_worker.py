import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document, DocumentChunk, DocumentFile, OCRJob
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.document_repository import DocumentRepository, OCRJobRepository
from app.services.chunking_service import ChunkingService
from app.services.document_classifier_service import DocumentClassifierService
from app.services.document_content_service import (
    DocumentContentService,
    DocumentPageContent,
    EmptyDocumentContentError,
    UnsupportedDocumentFormatError,
)
from app.services.embedding_service import EmbeddingService
from app.services.ocr_chunking.adapter import create_chunk_payloads
from app.services.ocr_job_recovery_service import OCRJobRecoveryService
from app.services.qdrant_service import QdrantService


logger = logging.getLogger(__name__)


RETRY_DELAY_SECONDS = 30
PROCESSING_DOCUMENT_STATUSES = {
    "ocr_pending",
    "ocr_running",
    "reprocess_pending",
    "reprocess_running",
    "chunking",
}
UNRECOVERABLE_FAILURE_REASONS = {
    "document_not_found",
    "unsupported_document_format",
    "empty_document_content",
    "empty_chunks",
    "uploaded_file_missing",
    "invalid_configuration",
}


class OCRWorker:
    def __init__(self, db: Session):
        self.settings = get_settings()
        self.db = db
        self.audit_logs = AuditLogRepository(db)
        self.documents = DocumentRepository(db)
        self.ocr_jobs = OCRJobRepository(db)
        self.document_content = DocumentContentService()
        self.classifier = DocumentClassifierService()
        self.chunking = ChunkingService()
        self.embeddings = EmbeddingService()
        self.qdrant = QdrantService()

    def run_once(self) -> bool:
        recovered = OCRJobRecoveryService(self.db).recover_stale_jobs()
        if recovered:
            self.db.commit()

        job = self.ocr_jobs.claim_next_pending_job()
        if not job:
            return False
        self.db.commit()

        self.process_job(job)
        return True

    def process_job(self, job: OCRJob) -> None:
        document: Document | None = None
        previous_document_status: str | None = None
        try:
            document = self.documents.get_document(job.document_id)
            if not document:
                raise ValueError(f"Document not found: {job.document_id}")

            previous_document_status = document.status
            self.documents.update_status(document, "reprocess_running" if job.job_type == "reprocess" else "ocr_running")
            self.db.commit()
            page_contents = self._extract_document_pages(document)
            if job.job_type == "reprocess":
                self.documents.replace_pages_for_document(
                    document_id=document.id,
                    pages=[
                        {
                            "page_number": page_content.page_number,
                            "text": page_content.text,
                            "confidence": page_content.confidence,
                        }
                        for page_content in page_contents
                    ],
                )
            else:
                for page_content in page_contents:
                    self.documents.create_page(
                        document_id=document.id,
                        page_number=page_content.page_number,
                        text=page_content.text,
                        confidence=page_content.confidence,
                    )

            self._extract_and_store_metadata(document, job, page_contents)
            self.documents.update_status(document, "chunking")
            chunk_payloads = self._create_page_chunks(document, page_contents)
            if not chunk_payloads:
                raise ValueError("No chunks created because extracted document content was empty")

            deleted_chunks = []
            if job.job_type == "reprocess":
                chunks, deleted_chunks = self.documents.replace_chunks_for_document(
                    document_id=document.id,
                    chunks=chunk_payloads,
                )
            else:
                chunks = [
                    self.documents.create_chunk(
                        document_id=document.id,
                        chunk_index=chunk_index,
                        text=str(chunk_payload["text"]),
                        content_hash=str(chunk_payload["content_hash"]),
                        page_from=int(chunk_payload["page_from"]),
                        page_to=int(chunk_payload["page_to"]),
                        section_title=chunk_payload["section_title"],
                        chunk_metadata=chunk_payload.get("chunk_metadata")
                        if isinstance(chunk_payload.get("chunk_metadata"), dict)
                        else None,
                    )
                    for chunk_index, chunk_payload in enumerate(chunk_payloads)
                ]

            for chunk in chunks:
                chunk_payload = chunk_payloads[chunk.chunk_index] if chunk.chunk_index < len(chunk_payloads) else {}
                point_id = chunk.id
                vector = self.embeddings.embed(chunk.text)
                self.qdrant.upsert_chunk(
                    point_id=point_id,
                    vector=vector,
                    payload=self._qdrant_payload(document, chunk, chunk_payload),
                )
                self.documents.update_chunk_qdrant_point_id(chunk, point_id)

            self.qdrant.delete_points([chunk.qdrant_point_id or chunk.id for chunk in deleted_chunks])
            self.documents.update_status(document, "searchable")
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            self.db.add(job)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            self._record_job_failure(job, document, previous_document_status, exc)
            self.db.commit()
            logger.exception(
                "OCR job failed: job_id=%s document_id=%s status=%s attempts=%s max_attempts=%s failed_reason=%s",
                job.id,
                job.document_id,
                job.status,
                job.attempts,
                job.max_attempts,
                job.failed_reason,
            )

    def _record_job_failure(
        self,
        job: OCRJob,
        document: Document | None,
        previous_document_status: str | None,
        exc: Exception,
    ) -> None:
        now = datetime.now(timezone.utc)
        failed_reason = self._failed_reason(exc)
        retryable = failed_reason not in UNRECOVERABLE_FAILURE_REASONS
        should_retry = retryable and job.attempts < job.max_attempts

        job.failed_reason = failed_reason
        job.error_message = str(exc)

        if should_retry:
            job.status = "pending"
            job.next_run_at = now + timedelta(seconds=RETRY_DELAY_SECONDS)
            if document:
                pending_status = "reprocess_pending" if job.job_type == "reprocess" else "ocr_pending"
                self.documents.update_status(document, pending_status)
                self._reset_incomplete_files_pending(document.id)
        else:
            job.status = "failed"
            job.completed_at = now
            job.next_run_at = None
            if document:
                fallback_status = previous_document_status if job.job_type == "reprocess" else "failed"
                if fallback_status in PROCESSING_DOCUMENT_STATUSES:
                    fallback_status = "failed"
                self.documents.update_status(document, fallback_status or "failed")
                self._mark_incomplete_files_failed(document.id)

        self.db.add(job)

    def _failed_reason(self, exc: Exception) -> str:
        message = str(exc)
        if isinstance(exc, UnsupportedDocumentFormatError):
            return "unsupported_document_format"
        if isinstance(exc, EmptyDocumentContentError):
            return "empty_document_content"
        if isinstance(exc, FileNotFoundError):
            return "uploaded_file_missing"
        if "Document not found" in message:
            return "document_not_found"
        if "No chunks created" in message:
            return "empty_chunks"
        if message.startswith("Unsupported OCR_") or message.startswith("Unsupported embedding backend"):
            return "invalid_configuration"
        return "processing_error"

    def _extract_and_store_metadata(
        self,
        document: Document,
        job: OCRJob,
        page_contents: list[DocumentPageContent],
    ) -> None:
        result = self.classifier.classify(page_contents)
        result_metadata = result.to_audit_metadata()
        has_manual_review = document.metadata_reviewed_at is not None or document.metadata_source in {"manual", "mixed"}

        if has_manual_review:
            self.audit_logs.create(
                action="document.metadata_auto_extracted",
                entity_type="document",
                entity_id=document.id,
                actor_user_id=None,
                metadata={
                    "ocr_job_id": job.id,
                    "applied": False,
                    "reason": "metadata already reviewed manually",
                    "result": result_metadata,
                },
            )
            return

        self.documents.update_metadata(
            document,
            title=result.title or result.excerpt or document.title,
            document_type=result.document_type,
            classification_confidence=result.confidence,
            document_number=result.document_number,
            document_symbol=result.symbol,
            issued_date=result.date,
            issued_place=result.place,
            issuing_agency=result.agency_name,
            excerpt=result.excerpt,
            recipient=result.recipient,
            signer_name=result.signer_name,
            signer_title=result.signer_title,
            seals_present=result.seals_present,
            attachment_present=result.attachment_present,
            page_count=result.page_count,
            metadata_source="auto",
            metadata_reviewed_at=None,
            business_type=document.business_type,
        )
        self.audit_logs.create(
            action="document.metadata_auto_extracted",
            entity_type="document",
            entity_id=document.id,
            actor_user_id=None,
            metadata={
                "ocr_job_id": job.id,
                "applied": True,
                "result": result_metadata,
            },
        )

    def _extract_document_pages(self, document: Document) -> list[DocumentPageContent]:
        document_files = self.documents.list_files_for_document(document.id)
        if not document_files:
            return self.document_content.extract_pages(
                Path(document.file_path),
                document.original_filename,
            )

        page_contents: list[DocumentPageContent] = []
        next_page_number = 1
        processing_files: list[DocumentFile] = []

        for document_file in document_files:
            self.documents.update_file_status(document_file, "ocr_running")
            self.db.commit()
            processing_files.append(document_file)

            extracted_pages = self.document_content.extract_pages(
                Path(document_file.file_path),
                document_file.original_filename,
            )
            for page_content in extracted_pages:
                page_contents.append(
                    DocumentPageContent(
                        page_number=next_page_number,
                        text=page_content.text,
                        confidence=page_content.confidence,
                    )
                )
                next_page_number += 1

        for document_file in processing_files:
            self.documents.update_file_status(document_file, "completed")
        return page_contents

    def _mark_incomplete_files_failed(self, document_id: str) -> None:
        for document_file in self.documents.list_files_for_document(document_id):
            if document_file.status != "completed":
                self.documents.update_file_status(document_file, "failed")

    def _reset_incomplete_files_pending(self, document_id: str) -> None:
        for document_file in self.documents.list_files_for_document(document_id):
            if document_file.status != "completed":
                self.documents.update_file_status(document_file, "pending")

    def _create_page_chunks(
        self,
        document: Document,
        page_contents: list[DocumentPageContent],
    ) -> list[dict[str, Any]]:
        backend = (self.settings.chunking_backend or "ocr_chunking").lower()
        if backend in {"ocr_chunking", "legal", "legal_aware"}:
            chunk_payloads = create_chunk_payloads(
                doc_id=document.id,
                document_type=document.document_type,
                page_contents=page_contents,
            )
            if chunk_payloads:
                return chunk_payloads
            logger.warning("Legal-aware chunking returned no chunks; falling back to legacy chunking")
        elif backend not in {"legacy", "simple"}:
            logger.warning("Unknown CHUNKING_BACKEND=%s; falling back to legacy chunking", self.settings.chunking_backend)

        chunks: list[dict[str, Any]] = []
        for page_content in page_contents:
            for chunk_payload in self.chunking.create_chunks(page_content.text):
                chunks.append(
                    {
                        **chunk_payload,
                        "page_from": page_content.page_number,
                        "page_to": page_content.page_number,
                        "chunk_metadata": {
                            "chunking_backend": "legacy",
                            "section_role": "unknown",
                            "section_path": [chunk_payload["section_title"]] if chunk_payload["section_title"] else [],
                            "doc_group": None,
                            "confidence": page_content.confidence,
                            "fallback_info": {
                                "used_fallback": True,
                                "fallback_reason": "legacy_chunking_backend",
                                "candidate_doc_type": document.document_type,
                            },
                        },
                    }
                )
        return chunks

    def _qdrant_payload(self, document: Document, chunk: DocumentChunk, chunk_payload: dict[str, Any]) -> dict[str, Any]:
        chunk_metadata = chunk_payload.get("chunk_metadata")
        if not isinstance(chunk_metadata, dict):
            chunk_metadata = {}
        entities = chunk_metadata.get("entities") if isinstance(chunk_metadata.get("entities"), dict) else {}
        fallback_info = (
            chunk_metadata.get("fallback_info") if isinstance(chunk_metadata.get("fallback_info"), dict) else {}
        )

        return {
            "document_id": document.id,
            "chunk_id": chunk.id,
            "text": chunk.text,
            "title": document.title,
            "document_type": document.document_type,
            "document_number": document.document_number,
            "issued_date": document.issued_date.isoformat() if document.issued_date else None,
            "issuing_agency": document.issuing_agency,
            "excerpt": document.excerpt,
            "recipient": document.recipient,
            "signer_name": document.signer_name,
            "business_type": document.business_type,
            "department_id": document.department_id,
            "page_from": chunk.page_from,
            "page_to": chunk.page_to,
            "content_hash": chunk.content_hash,
            "chunking_backend": self.settings.chunking_backend,
            "chunk_doc_type": chunk_metadata.get("doc_type"),
            "doc_group": chunk_metadata.get("doc_group"),
            "chunk_level": chunk_metadata.get("chunk_level"),
            "section_role": chunk_metadata.get("section_role"),
            "section_title": chunk.section_title,
            "section_path": chunk_metadata.get("section_path") or [],
            "article_number": chunk_metadata.get("article_number"),
            "clause_number": chunk_metadata.get("clause_number"),
            "point_number": chunk_metadata.get("point_number"),
            "chunk_confidence": chunk_metadata.get("confidence"),
            "ocr_confidence": chunk_metadata.get("ocr_confidence"),
            "layout_confidence": chunk_metadata.get("layout_confidence"),
            "classification_confidence": chunk_metadata.get("classification_confidence"),
            "source_anchor": chunk_metadata.get("source_anchor"),
            "contains_table": bool(chunk_metadata.get("contains_table", False)),
            "contains_signature": bool(chunk_metadata.get("contains_signature", False)),
            "contains_appendix": bool(chunk_metadata.get("contains_appendix", False)),
            "requires_review": bool(chunk_metadata.get("requires_review", False)),
            "fallback_info": fallback_info,
            "fallback_used": bool(fallback_info.get("used_fallback", False)),
            "fallback_reason": fallback_info.get("fallback_reason"),
            "entities": entities,
            "entity_agency": entities.get("agency"),
            "entity_subject": entities.get("subject"),
            "entity_deadline": entities.get("deadline"),
            "entity_amount": entities.get("amount"),
            "responsible_unit": entities.get("responsible_unit") or [],
        }


WORKER_HEARTBEAT_PATH = Path("/tmp/worker.heartbeat")


def _touch_worker_heartbeat() -> None:
    WORKER_HEARTBEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
    WORKER_HEARTBEAT_PATH.write_text(str(time.time()), encoding="utf-8")


def run_forever(db_factory, poll_seconds: int = 5) -> None:
    while True:
        _touch_worker_heartbeat()
        db = db_factory()
        try:
            processed = OCRWorker(db).run_once()
        finally:
            db.close()
        if not processed:
            time.sleep(poll_seconds)
