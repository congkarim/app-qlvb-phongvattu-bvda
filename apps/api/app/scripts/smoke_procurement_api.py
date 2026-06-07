from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.procurement import ProcurementRecord
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository


SMOKE_TITLE_PREFIX = "[SMOKE] Procurement API"
SMOKE_USER_EMAIL_PREFIX = "procurement-api-smoke-"
SMOKE_PASSWORD = "smoke-password-123"


def run_smoke(*, api_base: str, keep_data: bool) -> dict[str, Any]:
    db = SessionLocal()
    created_document_id: str | None = None
    created_user_id: str | None = None
    created_procurement_id: str | None = None
    try:
        _cleanup_existing_smoke_data(db)
        seed = _seed_data(db)
        created_document_id = seed["document_id"]
        created_user_id = seed["user_id"]

        admin_token = _login(
            api_base=api_base,
            email=get_settings().admin_email,
            password=get_settings().admin_password,
            expected_role="admin",
        )
        user_token = _login(
            api_base=api_base,
            email=seed["user_email"],
            password=SMOKE_PASSWORD,
            expected_role="user",
        )

        _expect_http_status(
            "GET",
            f"{api_base}/procurements/by-document/{seed['document_id']}",
            token=user_token,
            expected_status=404,
            label="procurement lookup before create",
        )

        created = _request_json(
            "POST",
            f"{api_base}/procurements",
            token=user_token,
            payload={
                "document_id": seed["document_id"],
                "procurement_kind": "plan",
                "reference_number": seed["reference_number"],
                "title_summary": "Ke hoach mua sam vat tu smoke",
                "requesting_unit": "Phong Vat Tu Smoke",
                "estimated_value": "250000000.00",
                "currency": "VND",
                "requested_date": "2026-06-07",
                "status": "submitted",
                "notes": "Smoke procurement API",
            },
            expected_status=201,
        )
        created_procurement_id = created["id"]
        _assert(created["document_id"] == seed["document_id"], "Procurement document_id mismatch")
        _assert(created["procurement_kind"] == "plan", "Procurement kind mismatch")

        _expect_http_status(
            "POST",
            f"{api_base}/procurements",
            token=admin_token,
            payload={"document_id": seed["document_id"], "procurement_kind": "plan", "status": "draft"},
            expected_status=409,
            label="duplicate active procurement",
        )

        query = urlencode({
            "q": "mua sam vat tu",
            "procurement_kind": "plan",
            "status": "submitted",
            "limit": 10,
            "offset": 0,
        })
        listed = _request_json("GET", f"{api_base}/procurements?{query}", token=user_token)
        _assert(listed["total"] == 1, f"Expected one procurement in filtered list, got {listed['total']}")
        _assert(listed["items"][0]["id"] == created_procurement_id, "Filtered list returned unexpected procurement")

        detail = _request_json("GET", f"{api_base}/procurements/{created_procurement_id}", token=user_token)
        _assert(detail["document_title"].startswith(SMOKE_TITLE_PREFIX), "Procurement detail missing document title")
        _assert(detail["document_number"] == seed["document_number"], "Procurement detail missing document number")

        by_document = _request_json(
            "GET",
            f"{api_base}/procurements/by-document/{seed['document_id']}",
            token=user_token,
        )
        _assert(by_document["id"] == created_procurement_id, "Procurement lookup by document_id mismatch")

        updated = _request_json(
            "PATCH",
            f"{api_base}/procurements/{created_procurement_id}",
            token=user_token,
            payload={
                "reference_number": seed["reference_number"],
                "requesting_unit": "Phong Vat Tu Smoke Updated",
                "title_summary": "Ke hoach mua sam vat tu smoke updated",
                "status": "approved",
                "notes": "Updated by smoke",
            },
        )
        _assert(updated["status"] == "approved", "Procurement update did not change status")

        _expect_http_status(
            "DELETE",
            f"{api_base}/procurements/{created_procurement_id}",
            token=user_token,
            expected_status=403,
            label="user procurement delete permission",
        )

        deleted = _request_json("DELETE", f"{api_base}/procurements/{created_procurement_id}", token=admin_token)
        _assert(deleted["id"] == created_procurement_id, "Deleted response id mismatch")
        _expect_http_status(
            "GET",
            f"{api_base}/procurements/{created_procurement_id}",
            token=admin_token,
            expected_status=404,
            label="deleted procurement lookup",
        )
        _expect_http_status(
            "GET",
            f"{api_base}/procurements/by-document/{seed['document_id']}",
            token=admin_token,
            expected_status=404,
            label="deleted procurement lookup by document",
        )
        _assert(_audit_count(db, created_procurement_id) >= 3, "Expected procurement create/update/delete audit logs")

        if not keep_data:
            _cleanup_created_data(db, document_id=created_document_id, user_id=created_user_id)
            db.commit()

        return {
            "document_id": seed["document_id"],
            "procurement_id": created_procurement_id,
            "user_email": seed["user_email"],
            "cleanup": "kept" if keep_data else "removed",
        }
    except Exception:
        db.rollback()
        if not keep_data:
            _cleanup_created_data(db, document_id=created_document_id, user_id=created_user_id)
            db.commit()
        raise
    finally:
        db.close()


def _seed_data(db) -> dict[str, str]:
    suffix = uuid4().hex[:10]
    document = DocumentRepository(db).create_document(
        title=f"{SMOKE_TITLE_PREFIX} {suffix}",
        original_filename=f"procurement-api-smoke-{suffix}.txt",
        file_path=f"/tmp/procurement-api-smoke-{suffix}.txt",
        content_type="text/plain",
        document_type="KH",
        document_number=f"KH-SMOKE-{suffix}",
        issued_date=date(2026, 6, 7),
        issuing_agency="Phong Vat Tu Smoke",
        business_type="procurement",
    )
    user_email = f"{SMOKE_USER_EMAIL_PREFIX}{suffix}@example.local"
    user = UserRepository(db).create(
        email=user_email,
        full_name="Procurement API Smoke User",
        password_hash=hash_password(SMOKE_PASSWORD),
        role="user",
        is_active=True,
    )
    db.commit()
    db.refresh(document)
    db.refresh(user)
    return {
        "document_id": document.id,
        "user_id": user.id,
        "user_email": user.email,
        "document_number": f"KH-SMOKE-{suffix}",
        "reference_number": f"KH-42/VT-{suffix}",
    }


def _cleanup_existing_smoke_data(db) -> None:
    docs = list(db.scalars(select(Document).where(Document.title.like(f"{SMOKE_TITLE_PREFIX}%"))))
    users = list(db.scalars(select(User).where(User.email.like(f"{SMOKE_USER_EMAIL_PREFIX}%"))))
    for document in docs:
        _cleanup_created_data(db, document_id=document.id, user_id=None)
    for user in users:
        _cleanup_created_data(db, document_id=None, user_id=user.id)
    db.commit()


def _cleanup_created_data(db, *, document_id: str | None, user_id: str | None) -> None:
    deleted_at = datetime.now(timezone.utc)
    if document_id:
        for record in db.scalars(select(ProcurementRecord).where(ProcurementRecord.document_id == document_id)):
            record.deleted_at = deleted_at
            db.add(record)
        document = db.get(Document, document_id)
        if document:
            document.deleted_at = deleted_at
            db.add(document)
    if user_id:
        user = db.get(User, user_id)
        if user:
            user.deleted_at = deleted_at
            user.is_active = False
            db.add(user)


def _audit_count(db, procurement_id: str) -> int:
    db.expire_all()
    return len(
        list(
            db.scalars(
                select(AuditLog).where(
                    AuditLog.entity_type == "procurement",
                    AuditLog.entity_id == procurement_id,
                    AuditLog.deleted_at.is_(None),
                )
            )
        )
    )


def _login(*, api_base: str, email: str, password: str, expected_role: str) -> str:
    response = _request_json("POST", f"{api_base}/auth/login", payload={"email": email, "password": password})
    user = response.get("user") or {}
    _assert(user.get("role") == expected_role, f"Expected {email} role={expected_role}, got {user.get('role')}")
    token = response.get("access_token")
    _assert(isinstance(token, str) and token, f"Login did not return token for {email}")
    return token


def _request_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    expected_status: int = 200,
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
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            status = response.status
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code == expected_status:
            return json.loads(body) if body else {}
        raise AssertionError(f"{method} {url} returned {exc.code}, expected {expected_status}: {body}") from exc
    except URLError as exc:
        raise AssertionError(f"{method} {url} failed: {exc}") from exc
    _assert(status == expected_status, f"{method} {url} returned {status}, expected {expected_status}: {body}")
    return json.loads(body) if body else {}


def _expect_http_status(
    method: str,
    url: str,
    *,
    token: str,
    expected_status: int,
    label: str,
    payload: dict[str, Any] | None = None,
) -> None:
    _request_json(method, url, token=token, payload=payload, expected_status=expected_status)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test procurement metadata API.")
    parser.add_argument("--api-base", default="http://localhost:8000/api/v1", help="API base URL.")
    parser.add_argument("--keep-data", action="store_true", help="Keep smoke document/user/procurement for debugging.")
    args = parser.parse_args()

    result = run_smoke(api_base=args.api_base.rstrip("/"), keep_data=args.keep_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
