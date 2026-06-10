from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.materials_catalog import MaterialsCatalogItem
from app.models.stock_balance import StockBalance
from app.models.user import User
from app.repositories.user_repository import UserRepository


SMOKE_USER_EMAIL_PREFIX = "inventory-smoke-"
SMOKE_PASSWORD = "smoke-password-123"


def run_smoke(*, api_base: str, keep_data: bool) -> dict[str, Any]:
    db = SessionLocal()
    created_user_id: str | None = None
    created_catalog_id: str | None = None
    created_movement_ids: list[str] = []
    try:
        _cleanup_existing_smoke_data(db)
        seed = _seed_data(db)
        created_user_id = seed["user_id"]
        created_catalog_id = seed["catalog_id"]

        user_token = _login(
            api_base=api_base,
            email=seed["user_email"],
            password=SMOKE_PASSWORD,
            expected_role="user",
        )

        balance_before = _request_json(
            "GET",
            f"{api_base}/stock-balances/{seed['catalog_id']}",
            token=user_token,
        )
        _assert(balance_before["quantity"] == "0" or float(balance_before["quantity"]) == 0, "Initial balance should be 0")

        movement_in = _request_json(
            "POST",
            f"{api_base}/stock-movements",
            token=user_token,
            payload={
                "catalog_item_id": seed["catalog_id"],
                "movement_type": "in",
                "quantity": "25",
                "movement_date": str(date.today()),
                "reference_number": "SMOKE-IN-001",
                "notes": "Smoke inventory inbound",
            },
            expected_status=201,
        )
        created_movement_ids.append(movement_in["id"])
        _assert(movement_in["movement_type"] == "in", "movement_type should be in")
        _assert(float(movement_in["balance_after"]) == 25, "balance_after should be 25 after inbound")

        movement_out = _request_json(
            "POST",
            f"{api_base}/stock-movements",
            token=user_token,
            payload={
                "catalog_item_id": seed["catalog_id"],
                "movement_type": "out",
                "quantity": "5",
                "movement_date": str(date.today()),
                "reference_number": "SMOKE-OUT-001",
            },
            expected_status=201,
        )
        created_movement_ids.append(movement_out["id"])
        _assert(float(movement_out["balance_after"]) == 20, "balance_after should be 20 after outbound")

        balance_after = _request_json(
            "GET",
            f"{api_base}/stock-balances/{seed['catalog_id']}",
            token=user_token,
        )
        _assert(float(balance_after["quantity"]) == 20, "Balance should be 20")

        listed = _request_json(
            "GET",
            f"{api_base}/stock-movements?movement_type=in",
            token=user_token,
        )
        _assert(listed["total"] >= 1, "Should list inbound movements")

        low_stock = _request_json("GET", f"{api_base}/stock-balances/low-stock", token=user_token)
        _assert("items" in low_stock and "total" in low_stock, "low-stock response shape")

        admin_token = _login(
            api_base=api_base,
            email=get_settings().admin_email,
            password=get_settings().admin_password,
            expected_role="admin",
        )
        catalog_list = _request_json(
            "GET",
            f"{api_base}/materials-catalog/all?below_min=true",
            token=admin_token,
        )
        _assert(any(item.get("id") == seed["catalog_id"] for item in catalog_list.get("items", [])), "below_min filter")

        return {
            "status": "pass",
            "catalog_id": seed["catalog_id"],
            "movement_ids": created_movement_ids,
            "final_balance": balance_after["quantity"],
        }
    finally:
        if not keep_data:
            _cleanup_smoke_runtime(db, created_user_id, created_catalog_id, created_movement_ids)
        db.close()


def _seed_data(db) -> dict[str, str]:
    user_repo = UserRepository(db)
    from uuid import uuid4

    email = f"{SMOKE_USER_EMAIL_PREFIX}{uuid4().hex[:8]}@example.local"
    user = user_repo.create(
        email=email,
        password_hash=hash_password(SMOKE_PASSWORD),
        full_name="Inventory Smoke User",
        role="user",
        is_active=True,
    )
    catalog = MaterialsCatalogItem(
        code="SMOKE-INV-001",
        name="Smoke Inventory Item",
        default_unit="Cai",
        category="Smoke",
        is_active=True,
        min_stock_level="30",
    )
    db.add(catalog)
    db.commit()
    db.refresh(user)
    db.refresh(catalog)
    return {"user_id": user.id, "user_email": email, "catalog_id": catalog.id}


def _cleanup_existing_smoke_data(db) -> None:
    deleted_at = datetime.now(timezone.utc)
    users = list(db.scalars(select(User).where(User.email.like(f"{SMOKE_USER_EMAIL_PREFIX}%"))))
    for user in users:
        user.deleted_at = deleted_at
        user.is_active = False
        db.add(user)
    items = list(
        db.scalars(select(MaterialsCatalogItem).where(MaterialsCatalogItem.code.like("SMOKE-INV-%")))
    )
    for item in items:
        item.deleted_at = deleted_at
        db.add(item)
    db.commit()


def _cleanup_smoke_runtime(db, user_id: str | None, catalog_id: str | None, movement_ids: list[str]) -> None:
    from app.models.stock_movement import StockMovement

    deleted_at = datetime.now(timezone.utc)
    for movement_id in movement_ids:
        movement = db.get(StockMovement, movement_id)
        if movement:
            movement.deleted_at = deleted_at
            db.add(movement)
    if catalog_id:
        item = db.get(MaterialsCatalogItem, catalog_id)
        if item:
            item.deleted_at = deleted_at
            db.add(item)
    if user_id:
        user = db.get(User, user_id)
        if user:
            user.deleted_at = deleted_at
            user.is_active = False
            db.add(user)
    db.commit()


def _login(*, api_base: str, email: str, password: str, expected_role: str) -> str:
    response = _request_json(
        "POST",
        f"{api_base}/auth/login",
        payload={"email": email, "password": password},
        expected_status=200,
    )
    user = response.get("user") or {}
    _assert(user.get("role") == expected_role, f"Expected role {expected_role}, got {user.get('role')}")
    token = response.get("access_token")
    _assert(isinstance(token, str) and token, "Missing access_token")
    return token


def _request_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    expected_status: int | None = None,
) -> Any:
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=60) as response:
            status = response.status
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        status = exc.code
        body = exc.read().decode("utf-8")
        if expected_status is not None and status != expected_status:
            raise RuntimeError(f"{method} {url} -> {status}: {body}") from exc
        if expected_status is None:
            raise RuntimeError(f"{method} {url} -> {status}: {body}") from exc
        return json.loads(body) if body else {}
    except URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc}") from exc

    if expected_status is not None and status != expected_status:
        raise RuntimeError(f"{method} {url} -> {status}, expected {expected_status}: {body}")
    return json.loads(body) if body else {}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test inventory stock movements API")
    parser.add_argument("--api-base", default="http://localhost:8000/api/v1")
    parser.add_argument("--keep-data", action="store_true")
    args = parser.parse_args()
    result = run_smoke(api_base=args.api_base.rstrip("/"), keep_data=args.keep_data)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
