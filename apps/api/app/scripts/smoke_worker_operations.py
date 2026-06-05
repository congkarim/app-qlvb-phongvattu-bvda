from __future__ import annotations

import argparse
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.scripts.smoke_worker_claim_atomic import run_smoke as run_claim_smoke
from app.scripts.smoke_worker_retry_policy import run_smoke as run_retry_smoke


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
    for key in ("pending_ready", "pending_delayed", "running", "failed", "completed", "active"):
        value = queue_status.get(key)
        _assert(isinstance(value, int) and value >= 0, f"Expected non-negative integer for {key}, got {value!r}")

    _expect_http_status("GET", f"{api_base}/ops/worker-queue", expected_status=401, label="ops endpoint unauthenticated")

    return {
        "claim_job_id": claim_result["job_id"],
        "retry_job_id": retry_result["job_id"],
        "retry_attempts": retry_result["attempts"],
        "retry_max_attempts": retry_result["max_attempts"],
        "queue_status": queue_status,
    }


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
) -> None:
    request = Request(url, headers={"Accept": "application/json"}, method=method)
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
        f"queue_active={queue['active']} queue_failed={queue['failed']}"
    )


if __name__ == "__main__":
    main()
