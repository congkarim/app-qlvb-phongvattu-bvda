from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.document import Document, OCRJob
from app.models.user import User
from app.repositories.document_repository import DocumentRepository, OCRJobRepository
from app.repositories.user_repository import UserRepository
from app.scripts.smoke_worker_claim_atomic import run_smoke as run_claim_smoke
from app.scripts.smoke_worker_retry_policy import run_smoke as run_retry_smoke


SMOKE_TITLE_PREFIX = "[SMOKE] Worker ops stale"
SMOKE_USER_EMAIL_PREFIX = "worker-ops-smoke-user-"
SMOKE_PASSWORD = "smoke-password-123"


def run_smoke(*, api_base: str) -> dict[str, Any]:
    claim_result = run_claim_smoke()
    retry_result = run_retry_smoke()

    settings = get_settings()
    admin_token = _login(
        api_base=api_base,
        email=settings.admin_email,
        password=settings.admin_password,
        expected_role="admin",
    )
    queue_status = _request_json("GET", f"{api_base}/ops/worker-queue", token=admin_token)
    _assert(queue_status.get("status") == "ok", f"Unexpected worker queue status: {queue_status}")
    for key in (
        "pending_ready",
        "pending_delayed",
        "running",
        "stale_running",
        "failed",
        "completed",
        "active",
        "lease_timeout_seconds",
        "stale_recovery_enabled",
    ):
        value = queue_status.get(key)
        if key in {"lease_timeout_seconds"}:
            _assert(isinstance(value, int) and value >= 1, f"Expected positive integer for {key}, got {value!r}")
        elif key == "stale_recovery_enabled":
            _assert(isinstance(value, bool), f"Expected bool for {key}, got {value!r}")
        else:
            _assert(isinstance(value, int) and value >= 0, f"Expected non-negative integer for {key}, got {value!r}")

    _expect_http_status("GET", f"{api_base}/ops/worker-queue", expected_status=401, label="ops endpoint unauthenticated")

    setup_db = SessionLocal()
    stale_job_id: str | None = None
    stale_document_id: str | None = None
    smoke_user_email: str | None = None
    try:
        _cleanup_existing_smoke_data(setup_db)
        smoke_user_email = _seed_smoke_user(setup_db)
        stale_job_id, stale_document_id = _seed_stale_job(setup_db)
        setup_db.commit()
    finally:
        setup_db.close()

    user_token = _login(
        api_base=api_base,
        email=smoke_user_email or "",
        password=SMOKE_PASSWORD,
        expected_role="user",
    )
    _expect_http_status(
        "GET",
        f"{api_base}/ops/worker-queue/stale-jobs",
        token=user_token,
        expected_status=403,
        label="user stale jobs permission",
    )
    _expect_http_status(
        "POST",
        f"{api_base}/ops/worker-queue/recover-stale",
        token=user_token,
        expected_status=403,
        label="user recover stale permission",
    )

    stale_list = _request_json("GET", f"{api_base}/ops/worker-queue/stale-jobs", token=admin_token)
    _assert(stale_list.get("status") == "ok", f"Unexpected stale jobs status: {stale_list}")
    _assert(stale_list.get("total") == 1, f"Expected one stale job, got total={stale_list.get('total')}")
    items = stale_list.get("items") or []
    _assert(len(items) == 1, f"Expected one stale job item, got {len(items)}")
    _assert(items[0].get("job_id") == stale_job_id, "Stale list missing seeded job")
    _assert(items[0].get("document_id") == stale_document_id, "Stale list missing seeded document")
    _assert(items[0].get("document_status") == "ocr_running", "Stale list missing document status")
    _assert(items[0].get("stale_for_seconds", 0) > 0, "Expected stale_for_seconds > 0")

    recover_one = _request_json(
        "POST",
        f"{api_base}/ops/worker-queue/stale-jobs/{stale_job_id}/recover",
        token=admin_token,
    )
    _assert(recover_one.get("recovered_count") == 1, f"Expected recovered_count=1, got {recover_one}")
    _assert(recover_one.get("recovered_job_ids") == [stale_job_id], "Unexpected recovered job ids")

    verify_db = SessionLocal()
    try:
        recovered_job = verify_db.get(OCRJob, stale_job_id)
        recovered_document = verify_db.get(Document, stale_document_id)
        _assert(recovered_job is not None, "Recovered job not found")
        _assert(recovered_document is not None, "Recovered document not found")
        _assert(recovered_job.status == "pending", f"Expected job pending after recover, got {recovered_job.status}")
        _assert(
            recovered_job.failed_reason == "worker_lease_expired",
            f"Unexpected failed_reason={recovered_job.failed_reason}",
        )
        _assert(recovered_document.status == "ocr_pending", f"Expected document ocr_pending, got {recovered_document.status}")

        empty_stale_list = _request_json("GET", f"{api_base}/ops/worker-queue/stale-jobs", token=admin_token)
        _assert(empty_stale_list.get("total") == 0, f"Expected no stale jobs after recover, got {empty_stale_list.get('total')}")
    finally:
        verify_db.close()

    cleanup_db = SessionLocal()
    try:
        if stale_document_id:
            _soft_delete_document_tree(cleanup_db, stale_document_id)
        if smoke_user_email:
            user = cleanup_db.scalar(select(User).where(User.email == smoke_user_email))
            if user is not None:
                user.deleted_at = datetime.now(timezone.utc)
                cleanup_db.add(user)
        cleanup_db.commit()
    finally:
        cleanup_db.close()

    return {
        "claim_job_id": claim_result["job_id"],
        "retry_job_id": retry_result["job_id"],
        "retry_attempts": retry_result["attempts"],
        "retry_max_attempts": retry_result["max_attempts"],
        "queue_status": queue_status,
        "stale_job_id": stale_job_id,
        "recovered_job_ids": recover_one.get("recovered_job_ids"),
    }


def _seed_smoke_user(db) -> str:
    users = UserRepository(db)
    email = f"{SMOKE_USER_EMAIL_PREFIX}{uuid4().hex[:8]}@example.com"
    users.create(
        email=email,
        password_hash=hash_password(SMOKE_PASSWORD),
        full_name="Worker Ops Smoke User",
        role="user",
    )
    return email


def _seed_stale_job(db) -> tuple[str, str]:
    documents = DocumentRepository(db)
    document = documents.create_document(
        title=f"{SMOKE_TITLE_PREFIX} {uuid4().hex[:8]}",
        original_filename="worker-ops-stale.txt",
        file_path="/tmp/worker-ops-stale.txt",
        content_type="text/plain",
        document_type="CV",
    )
    documents.update_status(document, "ocr_running")
    job = OCRJobRepository(db).create_job(document.id)
    lease_timeout = max(1, int(get_settings().ocr_job_lease_timeout_seconds))
    job.status = "ocr_running"
    job.attempts = 1
    job.started_at = datetime.now(timezone.utc) - timedelta(seconds=lease_timeout + 120)
    db.add(job)
    db.add(document)
    db.flush()
    return job.id, document.id


def _cleanup_existing_smoke_data(db) -> None:
    docs = list(db.scalars(select(Document).where(Document.title.like(f"{SMOKE_TITLE_PREFIX}%"))))
    for document in docs:
        _soft_delete_document_tree(db, document.id)
    users = list(db.scalars(select(User).where(User.email.like(f"{SMOKE_USER_EMAIL_PREFIX}%"))))
    deleted_at = datetime.now(timezone.utc)
    for user in users:
        user.deleted_at = deleted_at
        db.add(user)
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


def _login(*, api_base: str, email: str, password: str, expected_role: str) -> str:
    response = _request_json(
        "POST",
        f"{api_base}/auth/login",
        payload={"email": email, "password": password},
    )
    token = response.get("access_token")
    user = response.get("user") or {}
    _assert(isinstance(token, str) and token, "Login did not return access_token")
    _assert(user.get("role") == expected_role, f"Expected role={expected_role}, got {user.get('role')}")
    return token


def _request_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AssertionError(f"{method} {url} returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise AssertionError(f"{method} {url} failed: {exc}") from exc
    return json.loads(body) if body else {}


def _expect_http_status(
    method: str,
    url: str,
    *,
    expected_status: int,
    label: str,
    token: str | None = None,
) -> None:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            status = response.status
    except HTTPError as exc:
        status = exc.code
    except URLError as exc:
        raise AssertionError(f"{label}: request failed: {exc}") from exc
    _assert(status == expected_status, f"{label}: expected HTTP {expected_status}, got {status}")


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke worker claim, retry, and ops queue status.")
    parser.add_argument("--api-base", default="http://localhost:8000/api/v1")
    args = parser.parse_args()

    result = run_smoke(api_base=args.api_base.rstrip("/"))
    queue = result["queue_status"]
    print(
        "worker operations smoke passed: "
        f"claim_job_id={result['claim_job_id']} "
        f"retry_job_id={result['retry_job_id']} "
        f"retry_attempts={result['retry_attempts']}/{result['retry_max_attempts']} "
        f"queue_active={queue['active']} queue_stale={queue['stale_running']} "
        f"stale_job_id={result['stale_job_id']} recovered_job_ids={result['recovered_job_ids']}"
    )


if __name__ == "__main__":
    main()
