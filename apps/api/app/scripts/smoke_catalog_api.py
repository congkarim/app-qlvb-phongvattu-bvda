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
from app.models.catalog import AdminCatalogItem
from app.models.department import Department
from app.models.user import User
from app.repositories.user_repository import UserRepository


SMOKE_CODE_PREFIX = "SMOKE_CAT_"
SMOKE_USER_EMAIL_PREFIX = "catalog-api-smoke-"
SMOKE_PASSWORD = "smoke-password-123"


def run_smoke(*, api_base: str, keep_data: bool) -> dict[str, Any]:
    db = SessionLocal()
    created_user_id: str | None = None
    created_department_id: str | None = None
    created_item_id: str | None = None
    try:
        _cleanup_existing_smoke_data(db)
        seed = _seed_user(db)
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

        business_types = _request_json("GET", f"{api_base}/catalogs/business-types", token=user_token)
        _assert(any(item["code"] == "contract" for item in business_types), "business-types missing contract seed")

        document_types = _request_json("GET", f"{api_base}/catalogs/document-types", token=user_token)
        _assert(any(item["code"] == "CV" for item in document_types), "document-types missing CV seed")

        departments = _request_json("GET", f"{api_base}/catalogs/departments", token=user_token)
        _assert(any(item["code"] == "VT" for item in departments), "departments missing VT seed")

        suffix = uuid4().hex[:8]
        department_code = f"{SMOKE_CODE_PREFIX}DEP_{suffix}"
        item_code = f"{SMOKE_CODE_PREFIX}BUS_{suffix}"

        _expect_http_status(
            "POST",
            f"{api_base}/admin/catalogs/departments",
            token=user_token,
            payload={"code": department_code, "name": "Smoke Department"},
            expected_status=403,
            label="user department create permission",
        )

        department = _request_json(
            "POST",
            f"{api_base}/admin/catalogs/departments",
            token=admin_token,
            payload={
                "code": department_code,
                "name": f"Smoke Department {suffix}",
                "description": "Catalog smoke department",
                "sort_order": 700,
                "is_active": True,
            },
            expected_status=201,
        )
        created_department_id = department["id"]
        _assert(department["code"] == department_code, "Department create returned unexpected code")

        _expect_http_status(
            "POST",
            f"{api_base}/admin/catalogs/departments",
            token=admin_token,
            payload={"code": department_code, "name": f"Smoke Department Duplicate {suffix}"},
            expected_status=409,
            label="duplicate department code",
        )

        department = _request_json(
            "PATCH",
            f"{api_base}/admin/catalogs/departments/{created_department_id}",
            token=admin_token,
            payload={
                "code": department_code,
                "name": f"Smoke Department Updated {suffix}",
                "description": "Updated by smoke",
                "sort_order": 701,
                "is_active": True,
            },
        )
        _assert(department["sort_order"] == 701, "Department update did not change sort_order")

        item = _request_json(
            "POST",
            f"{api_base}/admin/catalogs/items",
            token=admin_token,
            payload={
                "catalog_type": "business_type",
                "code": item_code,
                "label": f"Smoke nghiệp vụ {suffix}",
                "description": "Catalog smoke item",
                "sort_order": 800,
                "is_active": True,
            },
            expected_status=201,
        )
        created_item_id = item["id"]
        _assert(item["catalog_type"] == "business_type", "Catalog item create returned unexpected type")

        _expect_http_status(
            "POST",
            f"{api_base}/admin/catalogs/items",
            token=admin_token,
            payload={"catalog_type": "business_type", "code": item_code, "label": "Duplicate"},
            expected_status=409,
            label="duplicate catalog item code",
        )

        item = _request_json(
            "PATCH",
            f"{api_base}/admin/catalogs/items/{created_item_id}",
            token=admin_token,
            payload={
                "catalog_type": "business_type",
                "code": item_code,
                "label": f"Smoke nghiệp vụ updated {suffix}",
                "description": "Updated by smoke",
                "sort_order": 801,
                "is_active": True,
            },
        )
        _assert(item["sort_order"] == 801, "Catalog item update did not change sort_order")

        listed_items = _request_json("GET", f"{api_base}/admin/catalogs/items?catalog_type=business_type&q={item_code}", token=admin_token)
        _assert(any(item["id"] == created_item_id for item in listed_items), "Admin item list missing smoke item")

        deleted_item = _request_json("DELETE", f"{api_base}/admin/catalogs/items/{created_item_id}", token=admin_token)
        _assert(deleted_item["id"] == created_item_id, "Deleted item response id mismatch")

        deleted_department = _request_json("DELETE", f"{api_base}/admin/catalogs/departments/{created_department_id}", token=admin_token)
        _assert(deleted_department["id"] == created_department_id, "Deleted department response id mismatch")

        _assert(_audit_count(db, "admin_catalog_item", created_item_id) >= 3, "Expected catalog item audit logs")
        _assert(_audit_count(db, "department", created_department_id) >= 3, "Expected department audit logs")

        if not keep_data:
            _cleanup_created_data(db, user_id=created_user_id)
            db.commit()

        return {
            "department_id": created_department_id,
            "item_id": created_item_id,
            "user_email": seed["user_email"],
            "cleanup": "kept" if keep_data else "removed",
        }
    except Exception:
        db.rollback()
        if not keep_data:
            _cleanup_created_data(db, user_id=created_user_id)
            db.commit()
        raise
    finally:
        db.close()


def _seed_user(db) -> dict[str, str]:
    suffix = uuid4().hex[:10]
    user_email = f"{SMOKE_USER_EMAIL_PREFIX}{suffix}@example.local"
    user = UserRepository(db).create(
        email=user_email,
        full_name="Catalog API Smoke User",
        password_hash=hash_password(SMOKE_PASSWORD),
        role="user",
        is_active=True,
    )
    db.commit()
    db.refresh(user)
    return {"user_id": user.id, "user_email": user.email}


def _cleanup_existing_smoke_data(db) -> None:
    deleted_at = datetime.now(timezone.utc)
    for item in db.scalars(select(AdminCatalogItem).where(AdminCatalogItem.code.like(f"{SMOKE_CODE_PREFIX}%"))):
        item.deleted_at = deleted_at
        item.is_active = False
        db.add(item)
    for department in db.scalars(select(Department).where(Department.code.like(f"{SMOKE_CODE_PREFIX}%"))):
        department.deleted_at = deleted_at
        department.is_active = False
        db.add(department)
    for user in db.scalars(select(User).where(User.email.like(f"{SMOKE_USER_EMAIL_PREFIX}%"))):
        user.deleted_at = deleted_at
        user.is_active = False
        db.add(user)
    db.commit()


def _cleanup_created_data(db, *, user_id: str | None) -> None:
    if user_id:
        user = db.get(User, user_id)
        if user:
            user.deleted_at = datetime.now(timezone.utc)
            user.is_active = False
            db.add(user)


def _audit_count(db, entity_type: str, entity_id: str) -> int:
    db.expire_all()
    return len(
        list(
            db.scalars(
                select(AuditLog).where(
                    AuditLog.entity_type == entity_type,
                    AuditLog.entity_id == entity_id,
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
) -> Any:
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
            response_status = response.status
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code == expected_status:
            return json.loads(body) if body else {}
        raise AssertionError(f"{method} {url} returned {exc.code}, expected {expected_status}: {body}") from exc
    except URLError as exc:
        raise AssertionError(f"{method} {url} failed: {exc}") from exc
    _assert(response_status == expected_status, f"{method} {url} returned {response_status}, expected {expected_status}: {body}")
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
    parser = argparse.ArgumentParser(description="Smoke test admin catalog API.")
    parser.add_argument("--api-base", default="http://localhost:8000/api/v1", help="API base URL.")
    parser.add_argument("--keep-data", action="store_true", help="Keep smoke user/catalog rows for debugging.")
    args = parser.parse_args()

    result = run_smoke(api_base=args.api_base.rstrip("/"), keep_data=args.keep_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
