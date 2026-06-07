from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings


def run_smoke(*, api_base: str) -> dict[str, Any]:
    live = _request_json("GET", f"{api_base}/health/live")
    _assert(live.get("status") == "ok", f"Unexpected liveness status: {live}")

    health = _request_json("GET", f"{api_base}/health")
    _assert(health.get("status") == "ok", f"Unexpected /health status: {health}")

    ready = _request_json("GET", f"{api_base}/health/ready")
    _assert(ready.get("status") == "ok", f"Unexpected readiness status: {ready}")
    components = ready.get("components") or {}
    for name in ("postgres", "redis", "qdrant", "uploads"):
        component = components.get(name)
        _assert(isinstance(component, dict), f"Missing readiness component: {name}")
        _assert(component.get("status") == "ok", f"Component {name} not ready: {component}")

    system_status = _check_system_status_llm(api_base)

    return {"live": live, "ready": ready, "system_status_llm": system_status}


def _check_system_status_llm(api_base: str) -> dict[str, Any]:
    settings = get_settings()
    token = _login(
        api_base=f"{api_base.rstrip('/')}/api/v1",
        email=settings.admin_email,
        password=settings.admin_password,
    )
    status = _request_json(
        "GET",
        f"{api_base.rstrip('/')}/api/v1/ops/system-status",
        token=token,
    )
    llm = status.get("llm")
    _assert(isinstance(llm, dict), "Missing llm component in system-status")
    _assert(
        llm.get("status") in {"ok", "degraded", "unavailable"},
        f"Unexpected llm status: {llm.get('status')}",
    )
    details = llm.get("details") or {}
    _assert(isinstance(details.get("generation_backend"), str), "Missing llm.generation_backend")
    return {
        "status": llm.get("status"),
        "generation_backend": details.get("generation_backend"),
        "reachable": details.get("reachable"),
    }


def _login(*, api_base: str, email: str, password: str) -> str:
    response = _request_json(
        "POST",
        f"{api_base}/auth/login",
        payload={"email": email, "password": password},
    )
    token = response.get("access_token")
    _assert(isinstance(token, str) and token, "Admin login did not return access_token")
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
    request = Request(url, data=data, method=method, headers=headers)
    try:
        with urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"{method} {url} failed with HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc}") from exc
    return json.loads(body) if body else {}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test health and readiness endpoints.")
    parser.add_argument("--api-base", default="http://localhost:8000")
    args = parser.parse_args()
    result = run_smoke(api_base=args.api_base.rstrip("/"))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
