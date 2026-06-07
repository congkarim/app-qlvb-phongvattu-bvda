from __future__ import annotations

import argparse
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.scripts.benchmark_search_fixtures import (
    _cleanup_documents,
    _cleanup_existing_benchmark_data,
    _seed_benchmark_data,
)
from app.services.qdrant_service import QdrantService


def run_smoke(*, api_base: str, keep_data: bool) -> dict[str, Any]:
    db = SessionLocal()
    qdrant = QdrantService()
    created_document_ids: list[str] = []
    try:
        _cleanup_existing_benchmark_data(db=db, qdrant=qdrant)
        seeded = _seed_benchmark_data(db=db, qdrant=qdrant)
        created_document_ids = seeded["document_ids"]
        expected_chunk_id = seeded["chunk_ids_by_key"]["article_acceptance"]

        token = _login(api_base=api_base)
        answer = _request_json(
            "POST",
            f"{api_base}/search/answer",
            token=token,
            payload={
                "query": "dieu 3 nghiem thu vat tu",
                "limit": 5,
                "max_citations": 3,
            },
        )
        citations = answer.get("citations") or []
        _assert(answer.get("grounded") is True, f"Expected grounded answer, got {answer}")
        _assert(answer.get("fallback_reason") is None, f"Unexpected fallback: {answer.get('fallback_reason')}")
        _assert(
            any(citation.get("chunk_id") == expected_chunk_id for citation in citations),
            "RAG answer did not cite expected acceptance chunk",
        )
        _assert(
            all(citation.get("document_id") and citation.get("chunk_id") and citation.get("quote") for citation in citations),
            "RAG citations are missing source fields",
        )
        citation_deep_links = [
            _build_document_chunk_url(citation["document_id"], citation["chunk_id"])
            for citation in citations
        ]
        _assert(
            all("#chunk-" in link for link in citation_deep_links),
            "RAG citation deep links must include chunk hash",
        )

        fallback = _request_json(
            "POST",
            f"{api_base}/search/answer",
            token=token,
            payload={
                "query": "noi dung khong ton tai trong fixture smoke",
                "limit": 3,
                "min_score": 10.0,
            },
        )
        _assert(fallback.get("grounded") is False, f"Expected fallback answer, got {fallback}")
        _assert(fallback.get("fallback_reason") == "insufficient_evidence", "Fallback reason mismatch")

        if not keep_data:
            _cleanup_documents(db=db, qdrant=qdrant, document_ids=created_document_ids)
            db.commit()

        return {
            "grounded_citations": len(citations),
            "expected_chunk_id": expected_chunk_id,
            "citation_deep_links": citation_deep_links,
            "fallback_reason": fallback.get("fallback_reason"),
            "cleanup": "kept" if keep_data else "removed",
        }
    except Exception:
        db.rollback()
        if not keep_data:
            _cleanup_documents(db=db, qdrant=qdrant, document_ids=created_document_ids)
            db.commit()
        raise
    finally:
        db.close()


def _login(*, api_base: str) -> str:
    settings = get_settings()
    response = _request_json(
        "POST",
        f"{api_base}/auth/login",
        payload={"email": settings.admin_email, "password": settings.admin_password},
    )
    token = response.get("access_token")
    _assert(isinstance(token, str) and token, "Login did not return an access token")
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
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            status = response.status
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise AssertionError(f"{method} {url} returned {exc.code}: {body}") from exc
    except URLError as exc:
        raise AssertionError(f"{method} {url} failed: {exc}") from exc
    _assert(status == 200, f"{method} {url} returned {status}: {body}")
    return json.loads(body) if body else {}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _build_document_chunk_url(document_id: str, chunk_id: str) -> str:
    return f"/documents/{document_id}#chunk-{chunk_id}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test local RAG answer endpoint.")
    parser.add_argument("--api-base", default="http://localhost:8000/api/v1", help="API base URL.")
    parser.add_argument("--keep-data", action="store_true", help="Keep smoke documents and Qdrant points for debugging.")
    args = parser.parse_args()

    result = run_smoke(api_base=args.api_base.rstrip("/"), keep_data=args.keep_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.keep_data:
        print(
            "Fixture kept for manual UI checks. See docs/RAG_ANSWER_RUNBOOK.md "
            '(dashboard query: "dieu 3 nghiem thu vat tu").'
        )


if __name__ == "__main__":
    main()
