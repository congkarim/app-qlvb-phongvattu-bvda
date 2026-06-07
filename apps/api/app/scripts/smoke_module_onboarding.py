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
from app.models.contract import ContractRecord
from app.models.decision import DecisionRecord
from app.models.dispatch import DispatchRecord
from app.models.document import Document
from app.models.procurement import ProcurementRecord
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository


SMOKE_TITLE_PREFIX = "[SMOKE] Module onboarding"
SMOKE_USER_EMAIL_PREFIX = "module-onboarding-smoke-"
SMOKE_PASSWORD = "smoke-password-123"

MODULE_ENDPOINTS = {
    "contract": "/contracts",
    "dispatch": "/dispatches",
    "decision": "/decisions",
    "procurement": "/procurements",
}

FIXTURES: list[dict[str, Any]] = [
    {
        "key": "contract",
        "document_type": "HĐ",
        "document_number": "01/HĐ-SMOKE",
        "excerpt": "Hop dong cung cap vat tu",
        "expected_module": "contract",
        "expected_business_type": "contract",
        "expected_kind": None,
        "field_assertions": {"contract_number": "01/HĐ-SMOKE", "sign_date": "2026-06-07"},
    },
    {
        "key": "dispatch_incoming",
        "document_type": "CV",
        "document_number": "01/CV-SMOKE",
        "recipient": "Ban Giam doc",
        "excerpt": "Cong van de nghi cap vat tu",
        "expected_module": "dispatch",
        "expected_business_type": "incoming_dispatch",
        "expected_kind": "incoming",
        "field_assertions": {"dispatch_type": "incoming", "recipient": "Ban Giam doc"},
    },
    {
        "key": "dispatch_outgoing",
        "document_type": "CV",
        "document_number": "02/CV-SMOKE",
        "excerpt": "V/v bao cao cong tac",
        "expected_module": "dispatch",
        "expected_business_type": "outgoing_dispatch",
        "expected_kind": "outgoing",
        "field_assertions": {"dispatch_type": "outgoing"},
    },
    {
        "key": "decision",
        "document_type": "QĐ",
        "document_number": "01/QĐ-SMOKE",
        "excerpt": "Quy dinh quan ly vat tu",
        "expected_module": "decision",
        "expected_business_type": "decision",
        "expected_kind": "decision",
        "field_assertions": {"decision_kind": "decision", "document_number": "01/QĐ-SMOKE"},
    },
    {
        "key": "procurement",
        "document_type": "KH",
        "document_number": "01/KH-SMOKE",
        "excerpt": "Ke hoach mua sam vat tu",
        "expected_module": "procurement",
        "expected_business_type": "procurement",
        "expected_kind": "plan",
        "field_assertions": {"procurement_kind": "plan", "reference_number": "01/KH-SMOKE"},
    },
]


def run_smoke(*, api_base: str, keep_data: bool) -> dict[str, Any]:
    db = SessionLocal()
    created_document_ids: list[str] = []
    created_user_id: str | None = None
    created_module_ids: dict[str, str] = {}
    try:
        _cleanup_existing_smoke_data(db)
        seed = _seed_user(db)
        created_user_id = seed["user_id"]
        token = _login(
            api_base=api_base,
            email=seed["user_email"],
            password=SMOKE_PASSWORD,
            expected_role="user",
        )

        for fixture in FIXTURES:
            document_id = _seed_document(db, fixture)
            created_document_ids.append(document_id)

            suggestion = _request_json(
                "GET",
                f"{api_base}/documents/{document_id}/onboarding-suggestions",
                token=token,
            )
            _assert_suggestion(fixture, suggestion)

            document = _request_json("GET", f"{api_base}/documents/{document_id}", token=token)
            patched = _request_json(
                "PATCH",
                f"{api_base}/documents/{document_id}/metadata",
                token=token,
                payload=_metadata_patch_payload(document, suggestion["suggested_business_type"]),
            )
            _assert(
                patched["business_type"] == suggestion["suggested_business_type"],
                f"{fixture['key']}: business_type was not applied",
            )

            missing_query = urlencode(
                {
                    "q": SMOKE_TITLE_PREFIX,
                    "missing_module_metadata": "true",
                    "limit": 20,
                    "offset": 0,
                }
            )
            missing_list = _request_json("GET", f"{api_base}/documents?{missing_query}", token=token)
            missing_ids = {item["id"] for item in missing_list["items"] if item.get("missing_module_metadata")}
            _assert(
                document_id in missing_ids,
                f"{fixture['key']}: document missing from missing_module_metadata filter",
            )

            module_payload = _module_create_payload(document_id, suggestion)
            endpoint = MODULE_ENDPOINTS[suggestion["target_module"]]
            created_module = _request_json(
                "POST",
                f"{api_base}{endpoint}",
                token=token,
                payload=module_payload,
                expected_status=201,
            )
            created_module_ids[fixture["key"]] = created_module["id"]
            _assert(created_module["document_id"] == document_id, f"{fixture['key']}: module document_id mismatch")

            by_document = _request_json(
                "GET",
                f"{api_base}{endpoint}/by-document/{document_id}",
                token=token,
            )
            _assert(by_document["id"] == created_module["id"], f"{fixture['key']}: module by-document lookup mismatch")

            blocked = _request_json(
                "GET",
                f"{api_base}/documents/{document_id}/onboarding-suggestions",
                token=token,
            )
            _assert(blocked["eligible"] is False, f"{fixture['key']}: onboarding should be blocked after module create")

            missing_after = _request_json("GET", f"{api_base}/documents?{missing_query}", token=token)
            still_missing = {item["id"] for item in missing_after["items"]}
            _assert(
                document_id not in still_missing,
                f"{fixture['key']}: document still listed as missing module metadata",
            )

        if not keep_data:
            _cleanup_created_data(db, document_ids=created_document_ids, user_id=created_user_id)
            db.commit()

        return {
            "fixtures": [fixture["key"] for fixture in FIXTURES],
            "document_ids": created_document_ids,
            "module_ids": created_module_ids,
            "user_email": seed["user_email"],
            "cleanup": "kept" if keep_data else "removed",
        }
    except Exception:
        db.rollback()
        if not keep_data:
            _cleanup_created_data(db, document_ids=created_document_ids, user_id=created_user_id)
            db.commit()
        raise
    finally:
        db.close()


def _seed_user(db) -> dict[str, str]:
    suffix = uuid4().hex[:10]
    user_email = f"{SMOKE_USER_EMAIL_PREFIX}{suffix}@example.local"
    user = UserRepository(db).create(
        email=user_email,
        full_name="Module Onboarding Smoke User",
        password_hash=hash_password(SMOKE_PASSWORD),
        role="user",
        is_active=True,
    )
    db.commit()
    db.refresh(user)
    return {"user_id": user.id, "user_email": user.email}


def _seed_document(db, fixture: dict[str, Any]) -> str:
    suffix = uuid4().hex[:8]
    document = DocumentRepository(db).create_document(
        title=f"{SMOKE_TITLE_PREFIX} {fixture['key']} {suffix}",
        original_filename=f"module-onboarding-{fixture['key']}-{suffix}.txt",
        file_path=f"/tmp/module-onboarding-{fixture['key']}-{suffix}.txt",
        content_type="text/plain",
        document_type=fixture["document_type"],
        document_number=fixture.get("document_number"),
        issued_date=date(2026, 6, 7),
        issuing_agency="Phong Vat Tu Smoke",
        business_type=None,
    )
    document.excerpt = fixture.get("excerpt")
    document.recipient = fixture.get("recipient")
    document.classification_confidence = 0.92
    document.metadata_source = "auto"
    document.status = "searchable"
    db.add(document)
    db.commit()
    db.refresh(document)
    return document.id


def _assert_suggestion(fixture: dict[str, Any], suggestion: dict[str, Any]) -> None:
    _assert(suggestion["eligible"] is True, f"{fixture['key']}: expected eligible suggestion")
    _assert(
        suggestion["target_module"] == fixture["expected_module"],
        f"{fixture['key']}: target_module mismatch",
    )
    _assert(
        suggestion["suggested_business_type"] == fixture["expected_business_type"],
        f"{fixture['key']}: suggested_business_type mismatch",
    )
    if fixture["expected_kind"] is not None:
        _assert(
            suggestion["module_kind"] == fixture["expected_kind"],
            f"{fixture['key']}: module_kind mismatch",
        )
    suggested_fields = suggestion.get("suggested_module_fields") or {}
    for field, expected in fixture.get("field_assertions", {}).items():
        _assert(
            suggested_fields.get(field) == expected,
            f"{fixture['key']}: suggested_module_fields[{field}] expected {expected}, got {suggested_fields.get(field)}",
        )


def _metadata_patch_payload(document: dict[str, Any], business_type: str) -> dict[str, Any]:
    return {
        "title": document["title"],
        "document_type": document["document_type"],
        "classification_confidence": document.get("classification_confidence"),
        "document_number": document.get("document_number"),
        "document_symbol": document.get("document_symbol"),
        "issued_date": document.get("issued_date"),
        "issued_place": document.get("issued_place"),
        "issuing_agency": document.get("issuing_agency"),
        "excerpt": document.get("excerpt"),
        "recipient": document.get("recipient"),
        "signer_name": document.get("signer_name"),
        "signer_title": document.get("signer_title"),
        "seals_present": document.get("seals_present"),
        "attachment_present": document.get("attachment_present"),
        "page_count": document.get("page_count"),
        "business_type": business_type,
    }


def _module_create_payload(document_id: str, suggestion: dict[str, Any]) -> dict[str, Any]:
    target_module = suggestion["target_module"]
    payload: dict[str, Any] = {"document_id": document_id}
    payload.update(suggestion.get("suggested_module_fields") or {})
    module_kind = suggestion.get("module_kind")
    if target_module == "dispatch" and "dispatch_type" not in payload and module_kind:
        payload["dispatch_type"] = module_kind
    if target_module == "decision" and "decision_kind" not in payload and module_kind:
        payload["decision_kind"] = module_kind
    if target_module == "procurement" and "procurement_kind" not in payload and module_kind:
        payload["procurement_kind"] = module_kind
    payload.setdefault("status", "draft")
    return payload


def _cleanup_existing_smoke_data(db) -> None:
    docs = list(db.scalars(select(Document).where(Document.title.like(f"{SMOKE_TITLE_PREFIX}%"))))
    users = list(db.scalars(select(User).where(User.email.like(f"{SMOKE_USER_EMAIL_PREFIX}%"))))
    for document in docs:
        _cleanup_created_data(db, document_ids=[document.id], user_id=None)
    for user in users:
        _cleanup_created_data(db, document_ids=[], user_id=user.id)
    db.commit()


def _cleanup_created_data(db, *, document_ids: list[str], user_id: str | None) -> None:
    deleted_at = datetime.now(timezone.utc)
    for document_id in document_ids:
        for model in (ContractRecord, DispatchRecord, DecisionRecord, ProcurementRecord):
            for record in db.scalars(select(model).where(model.document_id == document_id)):
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
        with urlopen(request, timeout=30) as response:
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


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test module onboarding workflow.")
    parser.add_argument("--api-base", default="http://localhost:8000/api/v1", help="API base URL.")
    parser.add_argument("--keep-data", action="store_true", help="Keep smoke documents/modules for debugging.")
    args = parser.parse_args()

    result = run_smoke(api_base=args.api_base.rstrip("/"), keep_data=args.keep_data)
    print(
        "module onboarding smoke passed: "
        f"fixtures={len(result['fixtures'])} cleanup={result['cleanup']}"
    )


if __name__ == "__main__":
    main()
