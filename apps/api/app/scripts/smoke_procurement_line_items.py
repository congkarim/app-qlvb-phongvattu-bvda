from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
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
from app.models.materials_catalog import MaterialsCatalogItem
from app.models.procurement import ProcurementRecord
from app.models.procurement_line_item import ProcurementLineItem
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository


SMOKE_TITLE_PREFIX = "[SMOKE] Procurement Line Items"
SMOKE_USER_EMAIL_PREFIX = "procurement-line-items-smoke-"
SMOKE_CATALOG_CODE_PREFIX = "SMOKE_MCAT_"
SMOKE_PASSWORD = "smoke-password-123"


def run_smoke(*, api_base: str, keep_data: bool) -> dict[str, Any]:
    db = SessionLocal()
    created_document_id: str | None = None
    created_user_id: str | None = None
    created_procurement_id: str | None = None
    created_line_item_ids: list[str] = []
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

        procurement = _request_json(
            "POST",
            f"{api_base}/procurements",
            token=user_token,
            payload={
                "document_id": seed["document_id"],
                "procurement_kind": "proposal",
                "reference_number": seed["reference_number"],
                "title_summary": "De xuat mua sam vat tu smoke line items",
                "requesting_unit": "Phong Vat Tu Smoke",
                "estimated_value": "500000.00",
                "currency": "VND",
                "requested_date": "2026-06-08",
                "status": "draft",
            },
            expected_status=201,
        )
        created_procurement_id = procurement["id"]

        catalog_active = _request_json(
            "GET",
            f"{api_base}/materials-catalog?q=VT-001",
            token=user_token,
        )
        _assert(
            any(item.get("code") == "VT-001" for item in catalog_active),
            "Seed VT-001 missing from active materials catalog",
        )
        vt001_id = next(item["id"] for item in catalog_active if item.get("code") == "VT-001")

        _expect_http_status(
            "POST",
            f"{api_base}/materials-catalog",
            token=user_token,
            payload={"code": "X", "name": "Forbidden"},
            expected_status=403,
            label="user materials catalog create permission",
        )

        smoke_catalog_code = f"{SMOKE_CATALOG_CODE_PREFIX}{uuid4().hex[:8]}"
        smoke_catalog = _request_json(
            "POST",
            f"{api_base}/materials-catalog",
            token=admin_token,
            payload={
                "code": smoke_catalog_code,
                "name": f"Smoke Vat Tu {smoke_catalog_code}",
                "default_unit": "Cai",
                "category": "Smoke",
            },
            expected_status=201,
        )

        line1 = _request_json(
            "POST",
            f"{api_base}/procurements/{created_procurement_id}/line-items",
            token=user_token,
            payload={
                "line_number": 1,
                "item_name": "Giay A4",
                "item_code": "VT-001",
                "unit": "Ram",
                "quantity": "10",
                "unit_price": "85000.00",
                "catalog_item_id": vt001_id,
            },
            expected_status=201,
        )
        created_line_item_ids.append(line1["id"])
        _assert(line1["amount"] == "850000.00", f"Line 1 amount mismatch: {line1['amount']}")
        _assert(line1["catalog_item_id"] == vt001_id, "Line 1 catalog_item_id mismatch")

        line2 = _request_json(
            "POST",
            f"{api_base}/procurements/{created_procurement_id}/line-items",
            token=user_token,
            payload={
                "item_name": "Muc in HP",
                "item_code": "VT-002",
                "unit": "Hop",
                "quantity": "5",
                "unit_price": "120000.00",
            },
            expected_status=201,
        )
        created_line_item_ids.append(line2["id"])
        _assert(line2["line_number"] == 2, f"Expected auto line_number=2, got {line2['line_number']}")
        _assert(line2["amount"] == "600000.00", f"Line 2 amount mismatch: {line2['amount']}")

        line3 = _request_json(
            "POST",
            f"{api_base}/procurements/{created_procurement_id}/line-items",
            token=user_token,
            payload={
                "item_name": smoke_catalog["name"],
                "item_code": smoke_catalog_code,
                "unit": "Cai",
                "quantity": "2",
                "unit_price": "10000.00",
                "catalog_item_id": smoke_catalog["id"],
            },
            expected_status=201,
        )
        created_line_item_ids.append(line3["id"])

        _request_json(
            "DELETE",
            f"{api_base}/materials-catalog/{smoke_catalog['id']}",
            token=admin_token,
        )
        catalog_after_delete = _request_json(
            "GET",
            f"{api_base}/materials-catalog?q={smoke_catalog_code}",
            token=user_token,
        )
        _assert(
            not any(item.get("code") == smoke_catalog_code for item in catalog_after_delete),
            "Soft-deleted catalog item still visible in active list",
        )
        line3_detail = _request_json(
            "PATCH",
            f"{api_base}/procurement-line-items/{line3['id']}",
            token=user_token,
            payload={"notes": "catalog deleted snapshot check"},
        )
        _assert(line3_detail["item_name"] == smoke_catalog["name"], "Line item snapshot lost after catalog delete")
        _assert(line3_detail["item_code"] == smoke_catalog_code, "Line item code snapshot lost after catalog delete")

        listed = _request_json(
            "GET",
            f"{api_base}/procurements/{created_procurement_id}/line-items",
            token=user_token,
        )
        _assert(listed["total"] == 3, f"Expected 3 line items, got {listed['total']}")
        _assert(listed["lines_total_amount"] == "1470000.00", f"Total amount mismatch: {listed['lines_total_amount']}")
        line_numbers = [item["line_number"] for item in listed["items"]]
        _assert(line_numbers == [1, 2, 3], f"Line items not ordered by line_number: {line_numbers}")

        updated = _request_json(
            "PATCH",
            f"{api_base}/procurement-line-items/{line1['id']}",
            token=user_token,
            payload={"quantity": "12"},
        )
        _assert(updated["amount"] == "1020000.00", f"Updated line 1 amount mismatch: {updated['amount']}")

        listed_after_update = _request_json(
            "GET",
            f"{api_base}/procurements/{created_procurement_id}/line-items",
            token=user_token,
        )
        _assert(listed_after_update["lines_total_amount"] == "1640000.00", "Total after update mismatch")

        _expect_http_status(
            "DELETE",
            f"{api_base}/procurement-line-items/{line2['id']}",
            token=user_token,
            expected_status=403,
            label="user line item delete permission",
        )

        deleted = _request_json(
            "DELETE",
            f"{api_base}/procurement-line-items/{line2['id']}",
            token=admin_token,
        )
        _assert(deleted["id"] == line2["id"], "Deleted line item id mismatch")

        listed_after_delete = _request_json(
            "GET",
            f"{api_base}/procurements/{created_procurement_id}/line-items",
            token=user_token,
        )
        _assert(listed_after_delete["total"] == 2, f"Expected 2 line items after delete, got {listed_after_delete['total']}")
        _assert(listed_after_delete["items"][0]["line_number"] == 1, "Remaining line item order mismatch")
        remaining_ids = {item["id"] for item in listed_after_delete["items"]}
        _assert(line1["id"] in remaining_ids and line3["id"] in remaining_ids, "Unexpected remaining line items")

        _assert(
            _audit_count(db, created_line_item_ids[0]) >= 2,
            "Expected line item create/update audit logs",
        )
        _assert(
            _audit_count(db, line2["id"]) >= 1,
            "Expected line item delete audit log",
        )

        if not keep_data:
            _cleanup_created_data(db, document_id=created_document_id, user_id=created_user_id)
            db.commit()

        return {
            "document_id": seed["document_id"],
            "procurement_id": created_procurement_id,
            "line_item_ids": created_line_item_ids,
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
        original_filename=f"procurement-line-items-smoke-{suffix}.txt",
        file_path=f"/tmp/procurement-line-items-smoke-{suffix}.txt",
        content_type="text/plain",
        document_type="DX",
        document_number=f"DX-SMOKE-{suffix}",
        issued_date=date(2026, 6, 8),
        issuing_agency="Phong Vat Tu Smoke",
        business_type="procurement",
    )
    user_email = f"{SMOKE_USER_EMAIL_PREFIX}{suffix}@example.local"
    user = UserRepository(db).create(
        email=user_email,
        full_name="Procurement Line Items Smoke User",
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
        "reference_number": f"DX-12/VT-{suffix}",
    }


def _cleanup_existing_smoke_data(db) -> None:
    docs = list(db.scalars(select(Document).where(Document.title.like(f"{SMOKE_TITLE_PREFIX}%"))))
    users = list(db.scalars(select(User).where(User.email.like(f"{SMOKE_USER_EMAIL_PREFIX}%"))))
    catalogs = list(
        db.scalars(select(MaterialsCatalogItem).where(MaterialsCatalogItem.code.like(f"{SMOKE_CATALOG_CODE_PREFIX}%")))
    )
    for catalog in catalogs:
        catalog.deleted_at = datetime.now(timezone.utc)
        db.add(catalog)
    for document in docs:
        _cleanup_created_data(db, document_id=document.id, user_id=None)
    for user in users:
        _cleanup_created_data(db, document_id=None, user_id=user.id)
    db.commit()


def _cleanup_created_data(db, *, document_id: str | None, user_id: str | None) -> None:
    deleted_at = datetime.now(timezone.utc)
    if document_id:
        procurements = list(
            db.scalars(select(ProcurementRecord).where(ProcurementRecord.document_id == document_id))
        )
        for procurement in procurements:
            for line_item in db.scalars(
                select(ProcurementLineItem).where(ProcurementLineItem.procurement_id == procurement.id)
            ):
                line_item.deleted_at = deleted_at
                db.add(line_item)
            procurement.deleted_at = deleted_at
            db.add(procurement)
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


def _audit_count(db, line_item_id: str) -> int:
    db.expire_all()
    return len(
        list(
            db.scalars(
                select(AuditLog).where(
                    AuditLog.entity_type == "procurement_line_item",
                    AuditLog.entity_id == line_item_id,
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
    parser = argparse.ArgumentParser(description="Smoke test procurement line items API.")
    parser.add_argument("--api-base", default="http://localhost:8000/api/v1", help="API base URL.")
    parser.add_argument("--keep-data", action="store_true", help="Keep smoke data for debugging.")
    args = parser.parse_args()

    result = run_smoke(api_base=args.api_base.rstrip("/"), keep_data=args.keep_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
