from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.document_relation import DocumentRelation
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository


SMOKE_TITLE_PREFIX = "[SMOKE] Document relations"
SMOKE_USER_EMAIL_PREFIX = "document-relations-smoke-"
SMOKE_OTHER_USER_EMAIL_PREFIX = "document-relations-other-"
SMOKE_PASSWORD = "smoke-password-123"


def run_smoke(*, api_base: str, keep_data: bool) -> dict[str, Any]:
    db = SessionLocal()
    created_document_ids: list[str] = []
    created_user_ids: list[str] = []
    created_relation_id: str | None = None
    try:
        _cleanup_existing_smoke_data(db)
        seed = _seed_data(db)
        created_document_ids = [seed["document_a_id"], seed["document_b_id"]]
        created_user_ids = [seed["user_id"], seed["other_user_id"]]

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
        other_user_token = _login(
            api_base=api_base,
            email=seed["other_user_email"],
            password=SMOKE_PASSWORD,
            expected_role="user",
        )

        empty_a = _request_json(
            "GET",
            f"{api_base}/documents/{seed['document_a_id']}/relations",
            token=user_token,
        )
        _assert(empty_a["outgoing"] == [], "Expected empty outgoing before create")
        _assert(empty_a["incoming"] == [], "Expected empty incoming before create")

        created = _request_json(
            "POST",
            f"{api_base}/documents/{seed['document_b_id']}/relations",
            token=user_token,
            payload={
                "target_document_id": seed["document_a_id"],
                "relation_type": "references",
                "notes": "CV tham chieu QD",
            },
            expected_status=201,
        )
        created_relation_id = created["id"]
        _assert(created["relation_type"] == "references", "Created relation type mismatch")
        _assert(created["target_document"]["id"] == seed["document_a_id"], "Target document mismatch")

        outgoing_b = _request_json(
            "GET",
            f"{api_base}/documents/{seed['document_b_id']}/relations",
            token=user_token,
        )
        _assert(len(outgoing_b["outgoing"]) == 1, f"Expected 1 outgoing on B, got {len(outgoing_b['outgoing'])}")
        _assert(outgoing_b["outgoing"][0]["id"] == created_relation_id, "Outgoing relation id mismatch")
        _assert(outgoing_b["incoming"] == [], "Expected no incoming on B")

        incoming_a = _request_json(
            "GET",
            f"{api_base}/documents/{seed['document_a_id']}/relations",
            token=user_token,
        )
        _assert(incoming_a["incoming"] == [] or len(incoming_a["incoming"]) == 1, "Unexpected incoming count on A")
        _assert(len(incoming_a["incoming"]) == 1, f"Expected 1 incoming on A, got {len(incoming_a['incoming'])}")
        _assert(incoming_a["incoming"][0]["id"] == created_relation_id, "Incoming relation id mismatch")
        _assert(incoming_a["outgoing"] == [], "Expected no outgoing on A")

        _expect_http_status(
            "POST",
            f"{api_base}/documents/{seed['document_b_id']}/relations",
            token=user_token,
            payload={
                "target_document_id": seed["document_a_id"],
                "relation_type": "references",
            },
            expected_status=409,
            label="duplicate document relation",
        )

        _expect_http_status(
            "DELETE",
            f"{api_base}/document-relations/{created_relation_id}",
            token=other_user_token,
            expected_status=403,
            label="non-creator delete permission",
        )

        deleted = _request_json(
            "DELETE",
            f"{api_base}/document-relations/{created_relation_id}",
            token=user_token,
        )
        _assert(deleted["id"] == created_relation_id, "Deleted relation id mismatch")

        after_delete_b = _request_json(
            "GET",
            f"{api_base}/documents/{seed['document_b_id']}/relations",
            token=user_token,
        )
        _assert(after_delete_b["outgoing"] == [], "Expected empty outgoing after delete")
        after_delete_a = _request_json(
            "GET",
            f"{api_base}/documents/{seed['document_a_id']}/relations",
            token=user_token,
        )
        _assert(after_delete_a["incoming"] == [], "Expected empty incoming after delete")

        _expect_http_status(
            "DELETE",
            f"{api_base}/document-relations/{created_relation_id}",
            token=admin_token,
            expected_status=404,
            label="deleted relation delete",
        )

        audit_count = _audit_count(db, created_relation_id)
        _assert(audit_count >= 2, f"Expected create+delete audit logs, got {audit_count}")

        return {
            "document_a_id": seed["document_a_id"],
            "document_b_id": seed["document_b_id"],
            "relation_id": created_relation_id,
            "user_email": seed["user_email"],
            "cleanup": "kept" if keep_data else "removed",
        }
    except Exception:
        db.rollback()
        if not keep_data:
            _cleanup_created_data(
                db,
                document_ids=created_document_ids,
                user_ids=created_user_ids,
                relation_id=created_relation_id,
            )
            db.commit()
        raise
    finally:
        if not keep_data:
            _cleanup_created_data(
                db,
                document_ids=created_document_ids,
                user_ids=created_user_ids,
                relation_id=created_relation_id,
            )
            db.commit()
        db.close()


def _seed_data(db) -> dict[str, str]:
    suffix = uuid4().hex[:10]
    documents = DocumentRepository(db)
    document_a = documents.create_document(
        title=f"{SMOKE_TITLE_PREFIX} QD {suffix}",
        original_filename=f"relations-smoke-qd-{suffix}.txt",
        file_path=f"/tmp/relations-smoke-qd-{suffix}.txt",
        content_type="text/plain",
        document_type="QĐ",
        document_number=f"01/QD-REL-{suffix}",
        business_type="decision",
    )
    document_b = documents.create_document(
        title=f"{SMOKE_TITLE_PREFIX} CV {suffix}",
        original_filename=f"relations-smoke-cv-{suffix}.txt",
        file_path=f"/tmp/relations-smoke-cv-{suffix}.txt",
        content_type="text/plain",
        document_type="CV",
        document_number=f"01/CV-REL-{suffix}",
        business_type="incoming_dispatch",
    )
    user_email = f"{SMOKE_USER_EMAIL_PREFIX}{suffix}@example.local"
    other_user_email = f"{SMOKE_OTHER_USER_EMAIL_PREFIX}{suffix}@example.local"
    user = UserRepository(db).create(
        email=user_email,
        full_name="Document Relations Smoke User",
        password_hash=hash_password(SMOKE_PASSWORD),
        role="user",
        is_active=True,
    )
    other_user = UserRepository(db).create(
        email=other_user_email,
        full_name="Document Relations Other User",
        password_hash=hash_password(SMOKE_PASSWORD),
        role="user",
        is_active=True,
    )
    db.commit()
    return {
        "document_a_id": document_a.id,
        "document_b_id": document_b.id,
        "user_id": user.id,
        "other_user_id": other_user.id,
        "user_email": user.email,
        "other_user_email": other_user.email,
    }


def _cleanup_existing_smoke_data(db) -> None:
    docs = list(db.scalars(select(Document).where(Document.title.like(f"{SMOKE_TITLE_PREFIX}%"))))
    users = list(
        db.scalars(
            select(User).where(
                (User.email.like(f"{SMOKE_USER_EMAIL_PREFIX}%"))
                | (User.email.like(f"{SMOKE_OTHER_USER_EMAIL_PREFIX}%"))
            )
        )
    )
    for document in docs:
        _cleanup_created_data(db, document_ids=[document.id], user_ids=[], relation_id=None)
    for user in users:
        _cleanup_created_data(db, document_ids=[], user_ids=[user.id], relation_id=None)
    db.commit()


def _cleanup_created_data(
    db,
    *,
    document_ids: list[str],
    user_ids: list[str],
    relation_id: str | None,
) -> None:
    deleted_at = datetime.now(timezone.utc)
    if relation_id:
        relation = db.get(DocumentRelation, relation_id)
        if relation and relation.deleted_at is None:
            relation.deleted_at = deleted_at
            db.add(relation)
    for document_id in document_ids:
        for relation in db.scalars(
            select(DocumentRelation).where(
                DocumentRelation.deleted_at.is_(None),
                (
                    (DocumentRelation.source_document_id == document_id)
                    | (DocumentRelation.target_document_id == document_id)
                ),
            )
        ):
            relation.deleted_at = deleted_at
            db.add(relation)
        document = db.get(Document, document_id)
        if document and document.deleted_at is None:
            document.deleted_at = deleted_at
            db.add(document)
    for user_id in user_ids:
        user = db.get(User, user_id)
        if user and user.deleted_at is None:
            user.deleted_at = deleted_at
            user.is_active = False
            db.add(user)


def _audit_count(db, relation_id: str) -> int:
    db.expire_all()
    return len(
        list(
            db.scalars(
                select(AuditLog).where(
                    AuditLog.entity_type == "document_relation",
                    AuditLog.entity_id == relation_id,
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
    parser = argparse.ArgumentParser(description="Smoke test document relations API.")
    parser.add_argument("--api-base", default="http://localhost:8000/api/v1", help="API base URL.")
    parser.add_argument("--keep-data", action="store_true", help="Keep smoke documents/users/relations for debugging.")
    args = parser.parse_args()

    result = run_smoke(api_base=args.api_base.rstrip("/"), keep_data=args.keep_data)
    print("smoke_document_relations: OK")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
