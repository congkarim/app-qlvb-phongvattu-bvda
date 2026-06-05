from __future__ import annotations

from datetime import datetime, timezone
from threading import Event, Thread
from uuid import uuid4

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.document import Document, OCRJob
from app.repositories.document_repository import DocumentRepository, OCRJobRepository


SMOKE_TITLE_PREFIX = "[SMOKE] Worker claim atomic"


def run_smoke() -> dict[str, str | int | None]:
    setup_db = SessionLocal()
    document_id: str | None = None
    job_id: str | None = None
    try:
        _cleanup_existing_smoke_data(setup_db)
        documents = DocumentRepository(setup_db)
        document = documents.create_document(
            title=f"{SMOKE_TITLE_PREFIX} {uuid4().hex[:8]}",
            original_filename="worker-claim-atomic.txt",
            file_path="/tmp/worker-claim-atomic.txt",
            content_type="text/plain",
            document_type="CV",
        )
        job = OCRJobRepository(setup_db).create_job(document.id)
        setup_db.commit()
        document_id = document.id
        job_id = job.id
    finally:
        setup_db.close()

    first_claimed = Event()
    release_first = Event()
    results: dict[str, str | None] = {"first": None, "second": None}
    errors: list[BaseException] = []

    def first_worker() -> None:
        db = SessionLocal()
        try:
            job = OCRJobRepository(db).claim_next_pending_job()
            results["first"] = job.id if job else None
            first_claimed.set()
            release_first.wait(timeout=10)
            db.commit()
        except BaseException as exc:
            db.rollback()
            errors.append(exc)
            first_claimed.set()
        finally:
            db.close()

    def second_worker() -> None:
        db = SessionLocal()
        try:
            if not first_claimed.wait(timeout=10):
                raise AssertionError("First worker did not claim the job in time")
            job = OCRJobRepository(db).claim_next_pending_job()
            results["second"] = job.id if job else None
            db.commit()
        except BaseException as exc:
            db.rollback()
            errors.append(exc)
        finally:
            db.close()

    first = Thread(target=first_worker)
    second = Thread(target=second_worker)
    first.start()
    second.start()
    second.join(timeout=10)
    release_first.set()
    first.join(timeout=10)

    try:
        if errors:
            raise errors[0]
        _assert(results["first"] == job_id, f"First worker claimed {results['first']}, expected {job_id}")
        _assert(results["second"] is None, f"Second worker should not claim locked job, got {results['second']}")

        verify_db = SessionLocal()
        try:
            claimed_job = verify_db.get(OCRJob, job_id)
            _assert(claimed_job is not None, "Claimed job not found")
            _assert(claimed_job.status == "ocr_running", f"Expected status=ocr_running, got {claimed_job.status}")
            _assert(claimed_job.attempts == 1, f"Expected attempts=1, got {claimed_job.attempts}")
            _assert(claimed_job.started_at is not None, "Expected started_at to be set")
            return {
                "document_id": document_id,
                "job_id": job_id,
                "first_claimed": results["first"],
                "second_claimed": results["second"],
                "attempts": claimed_job.attempts,
            }
        finally:
            verify_db.close()
    finally:
        cleanup_db = SessionLocal()
        try:
            if document_id:
                _soft_delete_document_tree(cleanup_db, document_id)
                cleanup_db.commit()
        finally:
            cleanup_db.close()


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
        "worker claim atomic smoke passed: "
        f"document_id={result['document_id']} job_id={result['job_id']} "
        f"first_claimed={result['first_claimed']} second_claimed={result['second_claimed']} attempts={result['attempts']}"
    )


if __name__ == "__main__":
    main()
