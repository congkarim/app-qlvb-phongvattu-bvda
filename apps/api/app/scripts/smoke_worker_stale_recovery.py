from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.document import Document, DocumentPage, OCRJob
from app.repositories.document_repository import DocumentRepository, OCRJobRepository
from app.scripts.smoke_worker_claim_atomic import run_smoke as run_claim_smoke
from app.scripts.smoke_worker_retry_policy import run_smoke as run_retry_smoke
from app.workers.ocr_worker import OCRWorker


SMOKE_TITLE_PREFIX = "[SMOKE] Worker stale recovery"


def run_smoke() -> dict[str, Any]:
    setup_db = SessionLocal()
    stale_job_id: str | None = None
    stale_document_id: str | None = None
    fresh_job_id: str | None = None
    fresh_document_id: str | None = None
    try:
        _cleanup_existing_smoke_data(setup_db)
        stale_job_id, stale_document_id = _seed_stale_running_job(setup_db)
        fresh_job_id, fresh_document_id = _seed_fresh_running_job(setup_db)
        setup_db.commit()
    finally:
        setup_db.close()

    worker_db = SessionLocal()
    try:
        processed = OCRWorker(worker_db).run_once()
        worker_db.commit()
        _assert(processed is False, f"Expected run_once to skip claim before next_run_at, got processed={processed}")

        stale_job = worker_db.get(OCRJob, stale_job_id)
        stale_document = worker_db.get(Document, stale_document_id)
        fresh_job = worker_db.get(OCRJob, fresh_job_id)
        fresh_document = worker_db.get(Document, fresh_document_id)
        _assert(stale_job is not None, "Stale job not found after worker recovery")
        _assert(stale_document is not None, "Stale document not found after worker recovery")
        _assert(fresh_job is not None, "Fresh running job not found after worker recovery")
        _assert(fresh_document is not None, "Fresh running document not found after worker recovery")

        _assert(stale_job.status == "pending", f"Expected stale job pending, got {stale_job.status}")
        _assert(
            stale_job.failed_reason == "worker_lease_expired",
            f"Unexpected stale failed_reason={stale_job.failed_reason}",
        )
        _assert(stale_job.attempts == 1, f"Expected attempts unchanged at 1, got {stale_job.attempts}")
        _assert(stale_job.started_at is None, "Expected stale job started_at cleared after recovery")
        _assert(stale_job.next_run_at is not None, "Expected stale job next_run_at after recovery")
        _assert(
            stale_document.status == "ocr_pending",
            f"Expected stale document ocr_pending, got {stale_document.status}",
        )
        stale_pages = DocumentRepository(worker_db).list_pages_for_document(stale_document.id)
        _assert(len(stale_pages) == 0, f"Expected partial pages cleaned up, got {len(stale_pages)}")

        _assert(fresh_job.status == "ocr_running", f"Expected fresh job still running, got {fresh_job.status}")
        _assert(fresh_job.started_at is not None, "Expected fresh job started_at to remain set")
        _assert(
            fresh_document.status == "ocr_running",
            f"Expected fresh document still ocr_running, got {fresh_document.status}",
        )

        audit_logs = list(
            worker_db.scalars(
                select(AuditLog).where(
                    AuditLog.entity_type == "ocr_job",
                    AuditLog.entity_id == stale_job_id,
                    AuditLog.action == "ocr_job.stale_recovered",
                    AuditLog.deleted_at.is_(None),
                )
            )
        )
        _assert(len(audit_logs) == 1, f"Expected one stale recovery audit log, got {len(audit_logs)}")
        metadata = audit_logs[0].metadata_ or {}
        _assert(metadata.get("outcome") == "retry_pending", f"Unexpected audit outcome={metadata.get('outcome')}")
        _assert(metadata.get("source") == "worker", f"Unexpected audit source={metadata.get('source')}")
    finally:
        worker_db.close()

    claim_result = run_claim_smoke()
    retry_result = run_retry_smoke()

    cleanup_db = SessionLocal()
    try:
        for document_id in (stale_document_id, fresh_document_id):
            if document_id:
                _soft_delete_document_tree(cleanup_db, document_id)
        cleanup_db.commit()
    finally:
        cleanup_db.close()

    return {
        "stale_job_id": stale_job_id,
        "stale_document_id": stale_document_id,
        "fresh_job_id": fresh_job_id,
        "fresh_document_id": fresh_document_id,
        "stale_job_status": "pending",
        "fresh_job_status": "ocr_running",
        "claim_job_id": claim_result["job_id"],
        "retry_job_id": retry_result["job_id"],
    }


def _seed_stale_running_job(db) -> tuple[str, str]:
    documents = DocumentRepository(db)
    document = documents.create_document(
        title=f"{SMOKE_TITLE_PREFIX} stale {uuid4().hex[:8]}",
        original_filename="worker-stale-recovery-stale.txt",
        file_path="/tmp/worker-stale-recovery-stale.txt",
        content_type="text/plain",
        document_type="CV",
    )
    documents.update_status(document, "ocr_running")
    documents.create_page(
        document_id=document.id,
        page_number=1,
        text="partial stale smoke page",
        confidence=0.9,
    )
    job = OCRJobRepository(db).create_job(document.id)
    lease_timeout = max(1, int(get_settings().ocr_job_lease_timeout_seconds))
    job.status = "ocr_running"
    job.attempts = 1
    job.started_at = datetime.now(timezone.utc) - timedelta(seconds=lease_timeout + 120)
    db.add(job)
    db.add(document)
    db.flush()
    return job.id, document.id


def _seed_fresh_running_job(db) -> tuple[str, str]:
    documents = DocumentRepository(db)
    document = documents.create_document(
        title=f"{SMOKE_TITLE_PREFIX} fresh {uuid4().hex[:8]}",
        original_filename="worker-stale-recovery-fresh.txt",
        file_path="/tmp/worker-stale-recovery-fresh.txt",
        content_type="text/plain",
        document_type="CV",
    )
    documents.update_status(document, "ocr_running")
    job = OCRJobRepository(db).create_job(document.id)
    job.status = "ocr_running"
    job.attempts = 1
    job.started_at = datetime.now(timezone.utc)
    db.add(job)
    db.add(document)
    db.flush()
    return job.id, document.id


def _cleanup_existing_smoke_data(db) -> None:
    docs = list(db.scalars(select(Document).where(Document.title.like(f"{SMOKE_TITLE_PREFIX}%"))))
    for document in docs:
        _soft_delete_document_tree(db, document.id)
    db.commit()


def _soft_delete_document_tree(db, document_id: str) -> None:
    deleted_at = datetime.now(timezone.utc)
    for page in db.scalars(select(DocumentPage).where(DocumentPage.document_id == document_id)):
        page.deleted_at = deleted_at
        db.add(page)
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
    parser = argparse.ArgumentParser(description="Smoke worker stale job recovery after simulated crash.")
    args = parser.parse_args()
    _ = args

    result = run_smoke()
    print(
        "worker stale recovery smoke passed: "
        f"stale_job_id={result['stale_job_id']} stale_status={result['stale_job_status']} "
        f"fresh_job_id={result['fresh_job_id']} fresh_status={result['fresh_job_status']} "
        f"claim_job_id={result['claim_job_id']} retry_job_id={result['retry_job_id']}"
    )


if __name__ == "__main__":
    main()
