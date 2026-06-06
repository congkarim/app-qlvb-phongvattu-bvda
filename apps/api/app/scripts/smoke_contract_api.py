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
from app.models.contract import ContractRecord
from app.models.document import Document
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository


SMOKE_TITLE_PREFIX = "[SMOKE] Contract API"
SMOKE_USER_EMAIL_PREFIX = "contract-api-smoke-"
SMOKE_PASSWORD = "smoke-password-123"


def run_smoke(*, api_base: str, keep_data: bool) -> dict[str, Any]:
    db = SessionLocal()
    created_document_id: str | None = None
    created_user_id: str | None = None
    created_contract_id: str | None = None
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
            f"{api_base}/contracts/by-document/{seed['document_id']}",
            token=user_token,
            expected_status=404,
            label="contract lookup before create",
        )

        created = _request_json(
            "POST",
            f"{api_base}/contracts",
            token=user_token,
            payload={
                "document_id": seed["document_id"],
                "contract_number": seed["contract_number"],
                "contract_title": "Hop dong smoke cap vat tu",
                "supplier_name": "Cong ty Smoke Vat Tu",
                "sign_date": "2026-06-06",
                "effective_from": "2026-06-07",
                "effective_to": "2026-12-31",
                "contract_value": "125000000.50",
                "currency": "vnd",
                "status": "active",
                "notes": "Smoke contract API",
            },
            expected_status=201,
        )
        created_contract_id = created["id"]
        _assert(created["currency"] == "VND", "Contract currency was not normalized")
        _assert(created["document_id"] == seed["document_id"], "Contract document_id mismatch")

        _expect_http_status(
            "POST",
            f"{api_base}/contracts",
            token=admin_token,
            payload={"document_id": seed["document_id"], "status": "draft"},
            expected_status=409,
            label="duplicate active contract",
        )

        query = urlencode({"q": "Smoke Vat Tu", "status": "active", "limit": 10, "offset": 0})
        listed = _request_json("GET", f"{api_base}/contracts?{query}", token=user_token)
        _assert(listed["total"] == 1, f"Expected one contract in filtered list, got {listed['total']}")
        _assert(listed["items"][0]["id"] == created_contract_id, "Filtered list returned unexpected contract")

        detail = _request_json("GET", f"{api_base}/contracts/{created_contract_id}", token=user_token)
        _assert(detail["document_title"].startswith(SMOKE_TITLE_PREFIX), "Contract detail missing document title")

        by_document = _request_json(
            "GET",
            f"{api_base}/contracts/by-document/{seed['document_id']}",
            token=user_token,
        )
        _assert(by_document["id"] == created_contract_id, "Contract lookup by document_id mismatch")
        _assert(by_document["document_id"] == seed["document_id"], "Contract by-document document_id mismatch")

        updated = _request_json(
            "PATCH",
            f"{api_base}/contracts/{created_contract_id}",
            token=user_token,
            payload={
                "contract_number": seed["contract_number"],
                "contract_title": "Hop dong smoke cap vat tu updated",
                "supplier_name": "Cong ty Smoke Vat Tu Updated",
                "sign_date": "2026-06-06",
                "effective_from": "2026-06-07",
                "effective_to": "2027-01-31",
                "contract_value": "130000000",
                "currency": "VND",
                "status": "completed",
                "notes": "Updated by smoke",
            },
        )
        _assert(updated["status"] == "completed", "Contract update did not change status")

        _expect_http_status(
            "DELETE",
            f"{api_base}/contracts/{created_contract_id}",
            token=user_token,
            expected_status=403,
            label="user contract delete permission",
        )

        deleted = _request_json("DELETE", f"{api_base}/contracts/{created_contract_id}", token=admin_token)
        _assert(deleted["id"] == created_contract_id, "Deleted response id mismatch")
        _expect_http_status(
            "GET",
            f"{api_base}/contracts/{created_contract_id}",
            token=admin_token,
            expected_status=404,
            label="deleted contract lookup",
        )
        _expect_http_status(
            "GET",
            f"{api_base}/contracts/by-document/{seed['document_id']}",
            token=admin_token,
            expected_status=404,
            label="deleted contract lookup by document",
        )
        _assert(_audit_count(db, created_contract_id) >= 3, "Expected contract create/update/delete audit logs")

        if not keep_data:
            _cleanup_created_data(db, document_id=created_document_id, user_id=created_user_id)
            db.commit()

        return {
            "document_id": seed["document_id"],
            "contract_id": created_contract_id,
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
        original_filename=f"contract-api-smoke-{suffix}.txt",
        file_path=f"/tmp/contract-api-smoke-{suffix}.txt",
        content_type="text/plain",
        document_type="HD",
        document_number=f"HD-SMOKE-{suffix}",
        issued_date=date(2026, 6, 6),
        issuing_agency="Phong Vat Tu Smoke",
        business_type="contract",
    )
    user_email = f"{SMOKE_USER_EMAIL_PREFIX}{suffix}@example.local"
    user = UserRepository(db).create(
        email=user_email,
        full_name="Contract API Smoke User",
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
        "contract_number": f"HD-API-{suffix}",
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
        for record in db.scalars(select(ContractRecord).where(ContractRecord.document_id == document_id)):
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


def _audit_count(db, contract_id: str) -> int:
    db.expire_all()
    return len(
        list(
            db.scalars(
                select(AuditLog).where(
                    AuditLog.entity_type == "contract",
                    AuditLog.entity_id == contract_id,
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
    parser = argparse.ArgumentParser(description="Smoke test contract metadata API.")
    parser.add_argument("--api-base", default="http://localhost:8000/api/v1", help="API base URL.")
    parser.add_argument("--keep-data", action="store_true", help="Keep smoke document/user/contract for debugging.")
    args = parser.parse_args()

    result = run_smoke(api_base=args.api_base.rstrip("/"), keep_data=args.keep_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
