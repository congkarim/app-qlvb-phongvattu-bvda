from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.document import Document, OCRJob
from app.repositories.document_repository import DocumentRepository, OCRJobRepository
from app.workers.ocr_worker import OCRWorker


SMOKE_TITLE_PREFIX = "[SMOKE] Worker retry policy"


def run_smoke() -> dict[str, str | int | None]:
    setup_db = SessionLocal()
    document_id: str | None = None
    job_id: str | None = None
    try:
        _cleanup_existing_smoke_data(setup_db)
        document = DocumentRepository(setup_db).create_document(
            title=f"{SMOKE_TITLE_PREFIX} {uuid4().hex[:8]}",
            original_filename="worker-retry-policy.txt",
            file_path="/tmp/worker-retry-policy.txt",
            content_type="text/plain",
            document_type="CV",
        )
        job = OCRJobRepository(setup_db).create_job(document.id, max_attempts=2)
        setup_db.commit()
        document_id = document.id
        job_id = job.id
    finally:
        setup_db.close()

    _run_failing_attempt(expected_job_id=job_id)

    verify_retry_db = SessionLocal()
    try:
        retry_job = verify_retry_db.get(OCRJob, job_id)
        retry_document = verify_retry_db.get(Document, document_id)
        _assert(retry_job is not None, "Retry job not found after first attempt")
        _assert(retry_document is not None, "Retry document not found after first attempt")
        _assert(retry_job.status == "pending", f"Expected first failure to retry as pending, got {retry_job.status}")
        _assert(retry_job.attempts == 1, f"Expected attempts=1 after first failure, got {retry_job.attempts}")
        _assert(retry_job.max_attempts == 2, f"Expected max_attempts=2, got {retry_job.max_attempts}")
        _assert(retry_job.failed_reason == "processing_error", f"Unexpected failed_reason={retry_job.failed_reason}")
        _assert(retry_job.error_message == "transient smoke failure", "Unexpected first error message")
        _assert(retry_job.next_run_at is not None, "Expected next_run_at after retryable failure")
        _assert(retry_document.status == "ocr_pending", f"Expected document ocr_pending, got {retry_document.status}")
        skipped_job = OCRJobRepository(verify_retry_db).claim_next_pending_job()
        _assert(skipped_job is None, "Claim should skip pending job before next_run_at")
        retry_job.next_run_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        verify_retry_db.add(retry_job)
        verify_retry_db.commit()
    finally:
        verify_retry_db.close()

    _run_failing_attempt(expected_job_id=job_id)

    try:
        final_db = SessionLocal()
        try:
            final_job = final_db.get(OCRJob, job_id)
            final_document = final_db.get(Document, document_id)
            _assert(final_job is not None, "Final job not found")
            _assert(final_document is not None, "Final document not found")
            _assert(final_job.status == "failed", f"Expected final status=failed, got {final_job.status}")
            _assert(final_job.attempts == 2, f"Expected attempts=2, got {final_job.attempts}")
            _assert(final_job.failed_reason == "processing_error", f"Unexpected final reason={final_job.failed_reason}")
            _assert(final_job.next_run_at is None, "Expected next_run_at cleared on final failure")
            _assert(final_job.completed_at is not None, "Expected completed_at on final failure")
            _assert(final_document.status == "failed", f"Expected document failed, got {final_document.status}")
            return {
                "document_id": document_id,
                "job_id": job_id,
                "attempts": final_job.attempts,
                "max_attempts": final_job.max_attempts,
                "failed_reason": final_job.failed_reason,
            }
        finally:
            final_db.close()
    finally:
        cleanup_db = SessionLocal()
        try:
            if document_id:
                _soft_delete_document_tree(cleanup_db, document_id)
                cleanup_db.commit()
        finally:
            cleanup_db.close()


def _run_failing_attempt(*, expected_job_id: str | None) -> None:
    db = SessionLocal()
    try:
        job = OCRJobRepository(db).claim_next_pending_job()
        _assert(job is not None, "Expected a claimable retry smoke job")
        _assert(job.id == expected_job_id, f"Claimed unexpected job {job.id}, expected {expected_job_id}")
        db.commit()

        worker = OCRWorker(db)

        def fail_extract_pages(document: Document):
            raise RuntimeError("transient smoke failure")

        worker._extract_document_pages = fail_extract_pages  # type: ignore[method-assign]
        worker.process_job(job)
    finally:
        db.close()


def _cleanup_existing_smoke_data(db) -> None:
    docs = list(db.scalars(select(Document).where(Document.title.like(f"{SMOKE_TITLE_PREFIX}%"))))
    for document in docs:
        _soft_delete_document_tree(db, document.id)
    db.commit()


def _soft_delete_document_tree(db, document_id: str) -> None:
    deleted_at = datetime.now(timezone.utc)
    for job in db.scalars(select(OCRJob).where(OCRJob.document_id == document_id)):
        job.deleted_at = deleted_at
        db.add(job)
    document = db.get(Document, document_id)
    if document is not None:
        document.deleted_at = deleted_at
        db.add(document)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    result = run_smoke()
    print(
        "worker retry policy smoke passed: "
        f"document_id={result['document_id']} job_id={result['job_id']} "
        f"attempts={result['attempts']}/{result['max_attempts']} failed_reason={result['failed_reason']}"
    )


if __name__ == "__main__":
    main()
