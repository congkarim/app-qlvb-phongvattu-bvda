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
from app.models.decision import DecisionRecord
from app.models.document import Document
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository


SMOKE_TITLE_PREFIX = "[SMOKE] Decision API"
SMOKE_USER_EMAIL_PREFIX = "decision-api-smoke-"
SMOKE_PASSWORD = "smoke-password-123"


def run_smoke(*, api_base: str, keep_data: bool) -> dict[str, Any]:
    db = SessionLocal()
    created_document_id: str | None = None
    created_user_id: str | None = None
    created_decision_id: str | None = None
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
            f"{api_base}/decisions/by-document/{seed['document_id']}",
            token=user_token,
            expected_status=404,
            label="decision lookup before create",
        )

        created = _request_json(
            "POST",
            f"{api_base}/decisions",
            token=user_token,
            payload={
                "document_id": seed["document_id"],
                "decision_kind": "decision",
                "document_number": seed["document_number"],
                "document_symbol": "QD-VT",
                "issued_date": "2026-06-07",
                "issuing_agency": "Phong Vat Tu Smoke",
                "excerpt": "Quyet dinh smoke ban hanh quy che vat tu",
                "effective_from": "2026-07-01",
                "status": "registered",
                "notes": "Smoke decision API",
            },
            expected_status=201,
        )
        created_decision_id = created["id"]
        _assert(created["document_id"] == seed["document_id"], "Decision document_id mismatch")
        _assert(created["decision_kind"] == "decision", "Decision kind mismatch")

        _expect_http_status(
            "POST",
            f"{api_base}/decisions",
            token=admin_token,
            payload={"document_id": seed["document_id"], "decision_kind": "decision", "status": "draft"},
            expected_status=409,
            label="duplicate active decision",
        )

        query = urlencode({"q": "quy che vat tu", "decision_kind": "decision", "status": "registered", "limit": 10, "offset": 0})
        listed = _request_json("GET", f"{api_base}/decisions?{query}", token=user_token)
        _assert(listed["total"] == 1, f"Expected one decision in filtered list, got {listed['total']}")
        _assert(listed["items"][0]["id"] == created_decision_id, "Filtered list returned unexpected decision")

        detail = _request_json("GET", f"{api_base}/decisions/{created_decision_id}", token=user_token)
        _assert(detail["document_title"].startswith(SMOKE_TITLE_PREFIX), "Decision detail missing document title")
        _assert(detail["document_type"] == "QĐ", "Decision detail missing document type")

        by_document = _request_json(
            "GET",
            f"{api_base}/decisions/by-document/{seed['document_id']}",
            token=user_token,
        )
        _assert(by_document["id"] == created_decision_id, "Decision lookup by document_id mismatch")

        updated = _request_json(
            "PATCH",
            f"{api_base}/decisions/{created_decision_id}",
            token=user_token,
            payload={
                "document_number": seed["document_number"],
                "issuing_agency": "Phong Vat Tu Smoke Updated",
                "excerpt": "Quyet dinh smoke ban hanh quy che vat tu updated",
                "status": "effective",
                "notes": "Updated by smoke",
            },
        )
        _assert(updated["status"] == "effective", "Decision update did not change status")

        _expect_http_status(
            "DELETE",
            f"{api_base}/decisions/{created_decision_id}",
            token=user_token,
            expected_status=403,
            label="user decision delete permission",
        )

        deleted = _request_json("DELETE", f"{api_base}/decisions/{created_decision_id}", token=admin_token)
        _assert(deleted["id"] == created_decision_id, "Deleted response id mismatch")
        _expect_http_status(
            "GET",
            f"{api_base}/decisions/{created_decision_id}",
            token=admin_token,
            expected_status=404,
            label="deleted decision lookup",
        )
        _expect_http_status(
            "GET",
            f"{api_base}/decisions/by-document/{seed['document_id']}",
            token=admin_token,
            expected_status=404,
            label="deleted decision lookup by document",
        )
        _assert(_audit_count(db, created_decision_id) >= 3, "Expected decision create/update/delete audit logs")

        if not keep_data:
            _cleanup_created_data(db, document_id=created_document_id, user_id=created_user_id)
            db.commit()

        return {
            "document_id": seed["document_id"],
            "decision_id": created_decision_id,
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
        original_filename=f"decision-api-smoke-{suffix}.txt",
        file_path=f"/tmp/decision-api-smoke-{suffix}.txt",
        content_type="text/plain",
        document_type="QĐ",
        document_number=f"QD-SMOKE-{suffix}",
        issued_date=date(2026, 6, 7),
        issuing_agency="Phong Vat Tu Smoke",
        business_type="decision",
    )
    user_email = f"{SMOKE_USER_EMAIL_PREFIX}{suffix}@example.local"
    user = UserRepository(db).create(
        email=user_email,
        full_name="Decision API Smoke User",
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
        "document_number": f"02/QD-VT-{suffix}",
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
        for record in db.scalars(select(DecisionRecord).where(DecisionRecord.document_id == document_id)):
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


def _audit_count(db, decision_id: str) -> int:
    db.expire_all()
    return len(
        list(
            db.scalars(
                select(AuditLog).where(
                    AuditLog.entity_type == "decision",
                    AuditLog.entity_id == decision_id,
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
    parser = argparse.ArgumentParser(description="Smoke test decision metadata API.")
    parser.add_argument("--api-base", default="http://localhost:8000/api/v1", help="API base URL.")
    parser.add_argument("--keep-data", action="store_true", help="Keep smoke document/user/decision for debugging.")
    args = parser.parse_args()

    result = run_smoke(api_base=args.api_base.rstrip("/"), keep_data=args.keep_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
