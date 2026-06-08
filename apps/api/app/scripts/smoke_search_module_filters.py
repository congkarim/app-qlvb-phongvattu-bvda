from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.contract import ContractRecord
from app.models.decision import DecisionRecord
from app.models.dispatch import DispatchRecord
from app.models.procurement import ProcurementRecord
from app.models.procurement_line_item import ProcurementLineItem
from app.models.document import Document, DocumentChunk, DocumentFile, DocumentPage
from app.repositories.contract_repository import ContractRepository
from app.repositories.decision_repository import DecisionRepository
from app.repositories.dispatch_repository import DispatchRepository
from app.repositories.procurement_repository import ProcurementRepository
from app.repositories.document_repository import DocumentRepository
from app.services.chunk_payload import build_qdrant_payload
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService


SMOKE_TITLE_PREFIX = "[SMOKE] Search module filter"
SMOKE_PASSWORD = "smoke-password-123"


def run_smoke(*, api_base: str, keep_data: bool) -> dict[str, Any]:
    db = SessionLocal()
    qdrant = QdrantService()
    created_document_ids: list[str] = []
    try:
        _cleanup_existing_smoke_data(db=db, qdrant=qdrant)
        seed = _seed_smoke_data(db=db, qdrant=qdrant)
        created_document_ids = [
            seed["dispatch_document_id"],
            seed["decision_document_id"],
            seed["procurement_document_id"],
        ]

        admin_token = _login(
            api_base=api_base,
            email=get_settings().admin_email,
            password=get_settings().admin_password,
        )

        dispatch_search = _request_json(
            "POST",
            f"{api_base}/search/semantic",
            token=admin_token,
            payload={
                "query": seed["dispatch_query"],
                "limit": 5,
                "dispatch_type": "incoming",
                "dispatch_status": "registered",
            },
        )
        dispatch_results = dispatch_search.get("results", [])
        _assert(dispatch_results, "Dispatch module filter returned no results")
        _assert(
            all(result.get("document_id") == seed["dispatch_document_id"] for result in dispatch_results),
            "Dispatch filter returned chunks from other documents",
        )
        _assert(
            all(result.get("dispatch_id") == seed["dispatch_id"] for result in dispatch_results),
            "Dispatch filter missing dispatch metadata enrichment",
        )

        empty_dispatch_search = _request_json(
            "POST",
            f"{api_base}/search/semantic",
            token=admin_token,
            payload={
                "query": seed["dispatch_query"],
                "limit": 5,
                "dispatch_type": "incoming",
                "dispatch_status": "archived",
            },
        )
        _assert(
            not empty_dispatch_search.get("results"),
            "Dispatch status archived should return empty for registered smoke record",
        )

        decision_search = _request_json(
            "POST",
            f"{api_base}/search/semantic",
            token=admin_token,
            payload={
                "query": seed["decision_query"],
                "limit": 5,
                "decision_kind": "decision",
                "decision_status": "effective",
            },
        )
        decision_results = decision_search.get("results", [])
        _assert(decision_results, "Decision module filter returned no results")
        _assert(
            all(result.get("document_id") == seed["decision_document_id"] for result in decision_results),
            "Decision filter returned chunks from other documents",
        )
        _assert(
            all(result.get("decision_id") == seed["decision_id"] for result in decision_results),
            "Decision filter missing decision metadata enrichment",
        )

        empty_decision_search = _request_json(
            "POST",
            f"{api_base}/search/semantic",
            token=admin_token,
            payload={
                "query": seed["decision_query"],
                "limit": 5,
                "decision_kind": "notification",
            },
        )
        _assert(
            not empty_decision_search.get("results"),
            "Decision kind notification should return empty for decision smoke record",
        )

        contract_search = _request_json(
            "POST",
            f"{api_base}/search/semantic",
            token=admin_token,
            payload={
                "query": seed["dispatch_query"],
                "limit": 5,
                "supplier_name": seed["supplier_name"],
            },
        )
        contract_results = contract_search.get("results", [])
        _assert(contract_results, "Contract supplier_name regression returned no results")
        _assert(
            all(result.get("document_id") == seed["dispatch_document_id"] for result in contract_results),
            "Contract filter regression returned unexpected document ids",
        )

        procurement_search = _request_json(
            "POST",
            f"{api_base}/search/semantic",
            token=admin_token,
            payload={
                "query": seed["procurement_query"],
                "limit": 5,
                "procurement_kind": "plan",
                "procurement_status": "approved",
            },
        )
        procurement_results = procurement_search.get("results", [])
        _assert(procurement_results, "Procurement module filter returned no results")
        _assert(
            all(result.get("document_id") == seed["procurement_document_id"] for result in procurement_results),
            "Procurement filter returned chunks from other documents",
        )
        _assert(
            all(result.get("procurement_id") == seed["procurement_id"] for result in procurement_results),
            "Procurement filter missing procurement metadata enrichment",
        )

        empty_procurement_search = _request_json(
            "POST",
            f"{api_base}/search/semantic",
            token=admin_token,
            payload={
                "query": seed["procurement_query"],
                "limit": 5,
                "procurement_kind": "acceptance",
            },
        )
        _assert(
            not empty_procurement_search.get("results"),
            "Procurement kind acceptance should return empty for plan smoke record",
        )

        item_name_filter = f"Giay A4 filter smoke {seed['item_suffix']}"
        procurement_item_search = _request_json(
            "POST",
            f"{api_base}/search/semantic",
            token=admin_token,
            payload={
                "query": seed["procurement_query"],
                "limit": 5,
                "procurement_item_name": item_name_filter,
            },
        )
        procurement_item_results = procurement_item_search.get("results", [])
        _assert(procurement_item_results, "Procurement item_name filter returned no results")
        _assert(
            all(result.get("document_id") == seed["procurement_document_id"] for result in procurement_item_results),
            "Procurement item_name filter returned chunks from other documents",
        )

        empty_item_search = _request_json(
            "POST",
            f"{api_base}/search/semantic",
            token=admin_token,
            payload={
                "query": seed["procurement_query"],
                "limit": 5,
                "procurement_item_name": "VT-NONEXISTENT-ITEM",
            },
        )
        _assert(
            not empty_item_search.get("results"),
            "Procurement item_name nonexistent should return empty",
        )

        rag_answer = _request_json(
            "POST",
            f"{api_base}/search/answer",
            token=admin_token,
            payload={
                "query": seed["decision_query"],
                "limit": 4,
                "decision_kind": "decision",
                "decision_status": "effective",
            },
        )
        citations = rag_answer.get("citations") or []
        _assert(citations, "RAG answer with decision filter returned no citations")
        _assert(
            all(citation.get("document_id") == seed["decision_document_id"] for citation in citations),
            "RAG decision filter citations came from unexpected documents",
        )

        procurement_rag_answer = _request_json(
            "POST",
            f"{api_base}/search/answer",
            token=admin_token,
            payload={
                "query": seed["procurement_query"],
                "limit": 4,
                "procurement_kind": "plan",
                "procurement_status": "approved",
                "reference_number": seed["reference_number"],
            },
        )
        procurement_citations = procurement_rag_answer.get("citations") or []
        _assert(procurement_citations, "RAG answer with procurement filter returned no citations")
        _assert(
            all(citation.get("document_id") == seed["procurement_document_id"] for citation in procurement_citations),
            "RAG procurement filter citations came from unexpected documents",
        )

        if not keep_data:
            for document_id in created_document_ids:
                _cleanup_created_data(db=db, qdrant=qdrant, document_id=document_id)
            db.commit()

        return {
            "dispatch_document_id": seed["dispatch_document_id"],
            "decision_document_id": seed["decision_document_id"],
            "procurement_document_id": seed["procurement_document_id"],
            "cleanup": "kept" if keep_data else "removed",
        }
    except Exception:
        db.rollback()
        if not keep_data:
            for document_id in created_document_ids:
                _cleanup_created_data(db=db, qdrant=qdrant, document_id=document_id)
            db.commit()
        raise
    finally:
        db.close()


def _seed_smoke_data(*, db, qdrant: QdrantService) -> dict[str, str]:
    suffix = uuid4().hex[:10]
    dispatch_query = f"search module filter dispatch smoke {suffix}"
    decision_query = f"search module filter decision smoke {suffix}"
    procurement_query = f"search module filter procurement smoke {suffix}"
    dispatch_text = f"{dispatch_query}\nNoi dung cong van den kiem tra filter metadata dispatch."
    decision_text = f"{decision_query}\nNoi dung quyet dinh kiem tra filter metadata decision."
    procurement_text = f"{procurement_query}\nNoi dung ke hoach mua sam kiem tra filter metadata procurement."

    documents = DocumentRepository(db)
    dispatch_document = documents.create_document(
        title=f"{SMOKE_TITLE_PREFIX} dispatch {suffix}",
        original_filename=f"search-filter-dispatch-{suffix}.txt",
        file_path=f"/tmp/search-filter-dispatch-{suffix}.txt",
        content_type="text/plain",
        document_type="CV",
        document_number=f"CV-FILTER-{suffix}",
        issued_date=date(2026, 6, 7),
        issuing_agency="Phong Vat Tu Smoke",
        business_type="incoming_dispatch",
    )
    decision_document = documents.create_document(
        title=f"{SMOKE_TITLE_PREFIX} decision {suffix}",
        original_filename=f"search-filter-decision-{suffix}.txt",
        file_path=f"/tmp/search-filter-decision-{suffix}.txt",
        content_type="text/plain",
        document_type="QĐ",
        document_number=f"QD-FILTER-{suffix}",
        issued_date=date(2026, 6, 7),
        issuing_agency="Phong Vat Tu Smoke",
        business_type="decision",
    )
    procurement_document = documents.create_document(
        title=f"{SMOKE_TITLE_PREFIX} procurement {suffix}",
        original_filename=f"search-filter-procurement-{suffix}.txt",
        file_path=f"/tmp/search-filter-procurement-{suffix}.txt",
        content_type="text/plain",
        document_type="KH",
        document_number=f"KH-FILTER-{suffix}",
        issued_date=date(2026, 6, 7),
        issuing_agency="Phong Vat Tu Smoke",
        business_type="procurement",
    )

    for document, text in (
        (dispatch_document, dispatch_text),
        (decision_document, decision_text),
        (procurement_document, procurement_text),
    ):
        documents.create_file(
            document_id=document.id,
            original_filename=document.original_filename,
            file_path=document.file_path,
            content_type="text/plain",
            file_size=len(text.encode("utf-8")),
            file_order=0,
            status="ocr_completed",
        )
        documents.create_page(document_id=document.id, page_number=1, text=text, confidence=0.9)

    dispatch_chunk = documents.create_chunk(
        document_id=dispatch_document.id,
        chunk_index=0,
        text=dispatch_text,
        content_hash=hashlib.sha256(dispatch_text.encode("utf-8")).hexdigest(),
        page_from=1,
        page_to=1,
        section_title="NOI DUNG",
        doc_group="B",
        chunk_level="section",
        section_role="content",
        section_path=["NOI DUNG"],
        chunk_confidence=0.9,
        requires_review=False,
    )
    decision_chunk = documents.create_chunk(
        document_id=decision_document.id,
        chunk_index=0,
        text=decision_text,
        content_hash=hashlib.sha256(decision_text.encode("utf-8")).hexdigest(),
        page_from=1,
        page_to=1,
        section_title="DIEU 1",
        doc_group="A",
        chunk_level="article",
        section_role="article",
        section_path=["DIEU 1"],
        chunk_confidence=0.9,
        requires_review=False,
    )
    procurement_chunk = documents.create_chunk(
        document_id=procurement_document.id,
        chunk_index=0,
        text=procurement_text,
        content_hash=hashlib.sha256(procurement_text.encode("utf-8")).hexdigest(),
        page_from=1,
        page_to=1,
        section_title="MUC 1",
        doc_group="D",
        chunk_level="section",
        section_role="content",
        section_path=["MUC 1"],
        chunk_confidence=0.9,
        requires_review=False,
    )
    documents.update_status(dispatch_document, "searchable")
    documents.update_status(decision_document, "searchable")
    documents.update_status(procurement_document, "searchable")

    supplier_name = f"Nha cung cap filter smoke {suffix}"
    ContractRepository(db).create(
        document_id=dispatch_document.id,
        contract_number=f"HD-FILTER-{suffix}",
        contract_title="Hop dong smoke search filter",
        supplier_name=supplier_name,
        sign_date=date(2026, 6, 7),
        status="active",
        currency="VND",
    )
    dispatch = DispatchRepository(db).create(
        document_id=dispatch_document.id,
        dispatch_type="incoming",
        document_number=f"CV-FILTER-{suffix}",
        issuing_agency="Phong Vat Tu Smoke",
        excerpt="Cong van smoke search filter",
        status="registered",
    )
    decision = DecisionRepository(db).create(
        document_id=decision_document.id,
        decision_kind="decision",
        document_number=f"QD-FILTER-{suffix}",
        issuing_agency="Phong Vat Tu Smoke",
        excerpt="Quyet dinh smoke search filter",
        effective_from=date(2026, 1, 1),
        status="effective",
    )
    reference_number = f"KH-FILTER-{suffix}"
    procurement = ProcurementRepository(db).create(
        document_id=procurement_document.id,
        procurement_kind="plan",
        reference_number=reference_number,
        title_summary="Ke hoach mua sam smoke search filter",
        requesting_unit="Phong Vat Tu Smoke",
        requested_date=date(2026, 6, 7),
        status="approved",
        currency="VND",
    )
    item_name = f"Giay A4 filter smoke {suffix}"
    db.add(
        ProcurementLineItem(
            procurement_id=procurement.id,
            line_number=1,
            item_name=item_name,
            item_code=f"VT-FILTER-{suffix}",
            unit="Ram",
            quantity=10,
            unit_price=85000,
            amount=850000,
        )
    )
    db.commit()
    db.refresh(dispatch_chunk)
    db.refresh(decision_chunk)
    db.refresh(procurement_chunk)

    embeddings = EmbeddingService()
    for document, chunk in (
        (dispatch_document, dispatch_chunk),
        (decision_document, decision_chunk),
        (procurement_document, procurement_chunk),
    ):
        qdrant.upsert_chunk(
            point_id=chunk.id,
            vector=embeddings.embed(chunk.text),
            payload=build_qdrant_payload(document, chunk),
        )
        documents.update_chunk_qdrant_point_id(chunk, chunk.id)
    db.commit()

    return {
        "dispatch_document_id": dispatch_document.id,
        "decision_document_id": decision_document.id,
        "procurement_document_id": procurement_document.id,
        "dispatch_chunk_id": dispatch_chunk.id,
        "decision_chunk_id": decision_chunk.id,
        "procurement_chunk_id": procurement_chunk.id,
        "dispatch_id": dispatch.id,
        "decision_id": decision.id,
        "procurement_id": procurement.id,
        "dispatch_query": dispatch_query,
        "decision_query": decision_query,
        "procurement_query": procurement_query,
        "supplier_name": supplier_name,
        "reference_number": reference_number,
        "item_suffix": suffix,
    }


def _login(*, api_base: str, email: str, password: str) -> str:
    response = _request_json(
        "POST",
        f"{api_base}/auth/login",
        payload={"email": email, "password": password},
    )
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
        raise AssertionError(f"{method} {url} returned {exc.code}, expected {expected_status}: {body}") from exc
    except URLError as exc:
        raise AssertionError(f"{method} {url} failed: {exc}") from exc
    _assert(status == expected_status, f"{method} {url} returned {status}, expected {expected_status}: {body}")
    return json.loads(body) if body else {}


def _cleanup_existing_smoke_data(*, db, qdrant: QdrantService) -> None:
    docs = list(db.scalars(select(Document).where(Document.title.like(f"{SMOKE_TITLE_PREFIX}%"))))
    for document in docs:
        _cleanup_created_data(db=db, qdrant=qdrant, document_id=document.id)
    db.commit()


def _cleanup_created_data(*, db, qdrant: QdrantService, document_id: str) -> None:
    deleted_at = datetime.now(timezone.utc)
    point_ids = [
        chunk.qdrant_point_id or chunk.id
        for chunk in db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document_id))
        if chunk.qdrant_point_id or chunk.id
    ]
    qdrant.delete_points(point_ids)
    for model in (DocumentChunk, DocumentPage, DocumentFile):
        for row in db.scalars(select(model).where(model.document_id == document_id)):
            row.deleted_at = deleted_at
            db.add(row)
    for record in db.scalars(select(ContractRecord).where(ContractRecord.document_id == document_id)):
        record.deleted_at = deleted_at
        db.add(record)
    for record in db.scalars(select(DispatchRecord).where(DispatchRecord.document_id == document_id)):
        record.deleted_at = deleted_at
        db.add(record)
    for record in db.scalars(select(DecisionRecord).where(DecisionRecord.document_id == document_id)):
        record.deleted_at = deleted_at
        db.add(record)
    for record in db.scalars(select(ProcurementRecord).where(ProcurementRecord.document_id == document_id)):
        for line_item in db.scalars(
            select(ProcurementLineItem).where(ProcurementLineItem.procurement_id == record.id)
        ):
            line_item.deleted_at = deleted_at
            db.add(line_item)
        record.deleted_at = deleted_at
        db.add(record)
    document = db.get(Document, document_id)
    if document is not None:
        document.deleted_at = deleted_at
        db.add(document)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke semantic search/RAG filters for dispatch, decision and procurement modules."
    )
    parser.add_argument("--api-base", default="http://localhost:8000/api/v1")
    parser.add_argument("--keep-data", action="store_true")
    args = parser.parse_args()

    result = run_smoke(api_base=args.api_base.rstrip("/"), keep_data=args.keep_data)
    print(
        "search module filter smoke passed: "
        f"dispatch_document_id={result['dispatch_document_id']} "
        f"decision_document_id={result['decision_document_id']} "
        f"procurement_document_id={result['procurement_document_id']} "
        f"cleanup={result['cleanup']}"
    )


if __name__ == "__main__":
    main()
