import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document, OCRJob
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.document_repository import DocumentRepository, OCRJobRepository
from app.services.qdrant_service import QdrantService


logger = logging.getLogger(__name__)

STALE_JOB_FAILED_REASON = "worker_lease_expired"
STALE_JOB_RETRY_DELAY_SECONDS = 30
PROCESSING_DOCUMENT_STATUSES = {
    "ocr_pending",
    "ocr_running",
    "reprocess_pending",
    "reprocess_running",
    "chunking",
}


class OCRJobRecoveryService:
    def __init__(self, db: Session):
        self.settings = get_settings()
        self.db = db
        self.audit_logs = AuditLogRepository(db)
        self.documents = DocumentRepository(db)
        self.ocr_jobs = OCRJobRepository(db)
        self.qdrant = QdrantService()

    def recover_stale_jobs(self, *, actor_user_id: str | None = None) -> list[str]:
        if not self.settings.ocr_job_stale_recovery_enabled:
            return []

        recovered_ids: list[str] = []
        while True:
            job = self.ocr_jobs.lock_next_stale_running_job(stale_before=self._stale_before())
            if job is None:
                break
            self._recover_locked_job(job, actor_user_id=actor_user_id)
            recovered_ids.append(job.id)
        return recovered_ids

    def recover_stale_job_by_id(self, job_id: str, *, actor_user_id: str | None = None) -> str | None:
        if not self.settings.ocr_job_stale_recovery_enabled:
            return None

        job = self.ocr_jobs.lock_stale_running_job(job_id=job_id, stale_before=self._stale_before())
        if job is None:
            return None

        self._recover_locked_job(job, actor_user_id=actor_user_id)
        return job.id

    def _stale_before(self, now: datetime | None = None) -> datetime:
        current = now or datetime.now(timezone.utc)
        lease_timeout = max(1, int(self.settings.ocr_job_lease_timeout_seconds))
        return current - timedelta(seconds=lease_timeout)

    def _recover_locked_job(self, job: OCRJob, *, actor_user_id: str | None) -> None:
        now = datetime.now(timezone.utc)
        lease_timeout = max(1, int(self.settings.ocr_job_lease_timeout_seconds))
        document = self.documents.get_document(job.document_id)
        should_retry = job.attempts < job.max_attempts
        previous_started_at = job.started_at
        outcome = "retry_pending" if should_retry else "failed"

        if should_retry:
            self._cleanup_partial_processing_state(
                document_id=job.document_id,
                job_type=job.job_type,
                document_status=document.status if document is not None else None,
            )
            job.status = "pending"
            job.started_at = None
            job.next_run_at = now + timedelta(seconds=STALE_JOB_RETRY_DELAY_SECONDS)
            job.failed_reason = STALE_JOB_FAILED_REASON
            job.error_message = (
                f"OCR job lease expired after {lease_timeout}s; scheduled for retry "
                f"(attempts={job.attempts}/{job.max_attempts})"
            )
            if document is not None:
                pending_status = "reprocess_pending" if job.job_type == "reprocess" else "ocr_pending"
                self.documents.update_status(document, pending_status)
                self._reset_incomplete_files_pending(document.id)
        else:
            job.status = "failed"
            job.completed_at = now
            job.next_run_at = None
            job.failed_reason = STALE_JOB_FAILED_REASON
            job.error_message = (
                f"OCR job lease expired after {lease_timeout}s with no retry attempts remaining "
                f"(attempts={job.attempts}/{job.max_attempts})"
            )
            if document is not None:
                self._mark_document_failed_after_stale(job, document)

        self.db.add(job)
        self.db.flush()

        logger.info(
            "Recovered stale OCR job: job_id=%s document_id=%s job_type=%s outcome=%s "
            "attempts=%s/%s started_at=%s lease_timeout_seconds=%s source=%s",
            job.id,
            job.document_id,
            job.job_type,
            outcome,
            job.attempts,
            job.max_attempts,
            previous_started_at,
            lease_timeout,
            "admin_ops" if actor_user_id else "worker",
        )
        self.audit_logs.create(
            action="ocr_job.stale_recovered",
            entity_type="ocr_job",
            entity_id=job.id,
            actor_user_id=actor_user_id,
            metadata={
                "document_id": job.document_id,
                "job_type": job.job_type,
                "outcome": outcome,
                "attempts": job.attempts,
                "max_attempts": job.max_attempts,
                "previous_started_at": previous_started_at.isoformat() if previous_started_at else None,
                "lease_timeout_seconds": lease_timeout,
                "failed_reason": STALE_JOB_FAILED_REASON,
                "source": "admin_ops" if actor_user_id else "worker",
            },
        )

    def _cleanup_partial_processing_state(
        self,
        *,
        document_id: str,
        job_type: str,
        document_status: str | None,
    ) -> None:
        deleted_chunks = []
        if job_type == "ocr":
            self.documents.soft_delete_all_pages_for_document(document_id)
            deleted_chunks = self.documents.soft_delete_all_chunks_for_document(document_id)
        elif document_status == "chunking":
            deleted_chunks = self.documents.soft_delete_all_chunks_for_document(document_id)

        point_ids = [chunk.qdrant_point_id or chunk.id for chunk in deleted_chunks if chunk.qdrant_point_id or chunk.id]
        if point_ids:
            self.qdrant.delete_points(point_ids)

    def _reset_incomplete_files_pending(self, document_id: str) -> None:
        for document_file in self.documents.list_files_for_document(document_id):
            if document_file.status != "completed":
                self.documents.update_file_status(document_file, "pending")

    def _mark_incomplete_files_failed(self, document_id: str) -> None:
        for document_file in self.documents.list_files_for_document(document_id):
            if document_file.status != "completed":
                self.documents.update_file_status(document_file, "failed")

    def _mark_document_failed_after_stale(self, job: OCRJob, document: Document) -> None:
        if job.job_type == "reprocess":
            if document.status == "chunking":
                fallback_status = "failed"
            elif self.documents.list_chunks_for_document(document.id):
                fallback_status = "searchable"
            else:
                fallback_status = "failed"
        else:
            fallback_status = "failed"

        if fallback_status in PROCESSING_DOCUMENT_STATUSES:
            fallback_status = "failed"

        self.documents.update_status(document, fallback_status)
        self._mark_incomplete_files_failed(document.id)
