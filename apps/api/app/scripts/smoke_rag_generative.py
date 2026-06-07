from __future__ import annotations

import argparse
import json
import unittest
from typing import Any

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.scripts.benchmark_search_fixtures import (
    _cleanup_documents,
    _cleanup_existing_benchmark_data,
    _seed_benchmark_data,
)
from app.scripts.smoke_rag_answer import (
    _assert,
    _build_document_chunk_url,
    _login,
    _request_json,
)
from app.services.local_llm_service import LocalLLMService
from app.services.qdrant_service import QdrantService


def preflight() -> dict[str, Any]:
    settings = get_settings()
    _assert(
        settings.rag_generation_backend == "ollama",
        (
            "RAG_GENERATION_BACKEND must be 'ollama' for generative smoke. "
            "Set env and recreate api: RAG_GENERATION_BACKEND=ollama docker compose --profile llm up -d api"
        ),
    )
    llm = LocalLLMService(settings)
    _assert(
        llm.is_available(),
        (
            "Ollama is not reachable. Start profile llm: "
            "docker compose --profile llm up -d ollama"
        ),
    )
    _assert(
        llm.is_model_loaded(),
        (
            f"Model {settings.rag_llm_model!r} is not loaded. Run: "
            f"docker compose exec ollama ollama pull {settings.rag_llm_model}"
        ),
    )
    return {
        "generation_backend": settings.rag_generation_backend,
        "model": settings.rag_llm_model,
        "ollama_base_url": settings.ollama_base_url,
    }


def run_smoke(*, api_base: str, keep_data: bool) -> dict[str, Any]:
    preflight_info = preflight()
    db = SessionLocal()
    qdrant = QdrantService()
    created_document_ids: list[str] = []
    try:
        _cleanup_existing_benchmark_data(db=db, qdrant=qdrant)
        seeded = _seed_benchmark_data(db=db, qdrant=qdrant)
        created_document_ids = seeded["document_ids"]
        expected_chunk_id = seeded["chunk_ids_by_key"]["article_acceptance"]

        token = _login(api_base=api_base)
        settings = get_settings()
        request_timeout = float(settings.rag_llm_timeout_seconds) + 30
        answer = _request_json(
            "POST",
            f"{api_base}/search/answer",
            token=token,
            payload={
                "query": "dieu 3 nghiem thu vat tu",
                "limit": 5,
                "max_citations": 3,
            },
            timeout=request_timeout,
        )

        _assert(answer.get("generation_mode") == "generative", f"Expected generative mode, got {answer}")
        _assert(answer.get("grounded") is True, f"Expected grounded generative answer, got {answer}")
        _assert(answer.get("fallback_reason") is None, f"Unexpected fallback: {answer.get('fallback_reason')}")
        _assert(isinstance(answer.get("model_name"), str) and answer.get("model_name"), "Missing model_name")
        _assert(isinstance(answer.get("latency_ms"), int) and answer.get("latency_ms") > 0, "Missing latency_ms")

        citations = answer.get("citations") or []
        _assert(len(citations) >= 1, "Generative answer must include at least one citation")
        _assert(
            any(citation.get("chunk_id") == expected_chunk_id for citation in citations),
            "Generative answer did not cite expected acceptance chunk",
        )
        _assert(
            all(citation.get("document_id") and citation.get("chunk_id") and citation.get("quote") for citation in citations),
            "Generative citations are missing source fields",
        )
        citation_deep_links = [
            _build_document_chunk_url(citation["document_id"], citation["chunk_id"])
            for citation in citations
        ]
        _assert(
            all("#chunk-" in link for link in citation_deep_links),
            "Generative citation deep links must include chunk hash",
        )
        _assert(isinstance(answer.get("answer"), str) and answer.get("answer").strip(), "Empty generative answer")

        if not keep_data:
            _cleanup_documents(db=db, qdrant=qdrant, document_ids=created_document_ids)
            db.commit()

        return {
            **preflight_info,
            "generation_mode": answer.get("generation_mode"),
            "model_name": answer.get("model_name"),
            "latency_ms": answer.get("latency_ms"),
            "grounded_citations": len(citations),
            "expected_chunk_id": expected_chunk_id,
            "citation_deep_links": citation_deep_links,
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


def verify_fallback_unit() -> None:
    import io

    from app.services.tests.test_rag_answer_service import RagAnswerServiceTests

    suite = unittest.TestSuite()
    suite.addTest(RagAnswerServiceTests("test_llm_unavailable_falls_back_to_extractive"))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
    _assert(result.wasSuccessful(), f"LLM unavailable fallback unit test failed: {stream.getvalue()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test generative RAG answer via local Ollama.")
    parser.add_argument("--api-base", default="http://localhost:8000/api/v1", help="API base URL.")
    parser.add_argument("--keep-data", action="store_true", help="Keep smoke documents and Qdrant points for debugging.")
    parser.add_argument(
        "--verify-fallback",
        action="store_true",
        help="Also run unit test for llm_unavailable extractive fallback.",
    )
    args = parser.parse_args()

    if args.verify_fallback:
        verify_fallback_unit()

    result = run_smoke(api_base=args.api_base.rstrip("/"), keep_data=args.keep_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.keep_data:
        print(
            "Fixture kept for manual UI checks. See docs/RAG_ANSWER_RUNBOOK.md "
            '(dashboard query: "dieu 3 nghiem thu vat tu").'
        )


if __name__ == "__main__":
    main()
