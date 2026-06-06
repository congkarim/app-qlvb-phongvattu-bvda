from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


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

    return {"live": live, "ready": ready}


def _request_json(method: str, url: str) -> dict[str, Any]:
    request = Request(url, method=method, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"{method} {url} failed with HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc}") from exc
    return json.loads(body)


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
