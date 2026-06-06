from __future__ import annotations

import argparse
import hashlib
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
from app.models.document import Document, DocumentChunk, DocumentFile, DocumentPage
from app.models.user import User
from app.repositories.contract_repository import ContractRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository
from app.services.chunk_payload import build_qdrant_payload
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService


SMOKE_TITLE_PREFIX = "[SMOKE] API workflow"
SMOKE_USER_EMAIL_PREFIX = "api-workflow-smoke-"
SMOKE_PASSWORD = "smoke-password-123"


def run_smoke(*, api_base: str, keep_data: bool) -> dict[str, str]:
    db = SessionLocal()
    qdrant = QdrantService()
    created_document_id: str | None = None
    created_chunk_ids: list[str] = []
    created_user_id: str | None = None
    try:
        _cleanup_existing_smoke_data(db=db, qdrant=qdrant)
        seed = _seed_smoke_data(db=db, qdrant=qdrant)
        created_document_id = seed["document_id"]
        created_chunk_ids = [seed["appendix_chunk_id"], seed["normal_chunk_id"]]
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

        queue = _request_json(
            "GET",
            f"{api_base}/documents/chunks/review-queue?{urlencode({'limit': 10, 'offset': 0, 'section_role': 'appendix', 'document_id': seed['document_id']})}",
            token=admin_token,
        )
        queue_items = queue.get("items") or []
        _assert(queue.get("total") == 1, f"Expected review queue total=1, got {queue.get('total')}")
        _assert(any(item.get("id") == seed["appendix_chunk_id"] for item in queue_items), "Review queue missing appendix chunk")
        _expect_http_status(
            "GET",
            f"{api_base}/documents/chunks/review-queue?limit=1&offset=0",
            token=user_token,
            expected_status=403,
            label="user review queue permission",
        )

        basic_search = _request_json(
            "POST",
            f"{api_base}/search/semantic",
            token=admin_token,
            payload={"query": "api workflow smoke vat tu", "limit": 5},
        )
        _assert(
            any(result.get("chunk_id") in created_chunk_ids for result in basic_search.get("results", [])),
            "Semantic search did not return smoke chunks",
        )

        appendix_search = _request_json(
            "POST",
            f"{api_base}/search/semantic",
            token=admin_token,
            payload={"query": "api workflow smoke phu luc vat tu", "limit": 5, "section_role": "appendix"},
        )
        appendix_results = appendix_search.get("results", [])
        _assert(any(result.get("chunk_id") == seed["appendix_chunk_id"] for result in appendix_results), "Appendix search missing smoke chunk")
        _assert(
            all(result.get("section_role") == "appendix" for result in appendix_results),
            "Appendix search returned non-appendix result",
        )

        _expect_http_status(
            "PATCH",
            f"{api_base}/documents/{seed['document_id']}/chunks/{seed['appendix_chunk_id']}/reviewed",
            token=user_token,
            expected_status=403,
            label="user review action permission",
        )
        reviewed = _request_json(
            "PATCH",
            f"{api_base}/documents/{seed['document_id']}/chunks/{seed['appendix_chunk_id']}/reviewed",
            token=admin_token,
        )
        _assert(reviewed.get("requires_review") is False, "Review action response did not clear requires_review")
        _assert(_chunk_requires_review(db=db, chunk_id=seed["appendix_chunk_id"]) is False, "DB chunk still requires review")
        _assert(
            _qdrant_requires_review(qdrant=qdrant, point_id=seed["appendix_chunk_id"]) is False,
            "Qdrant payload still has requires_review=true",
        )

        queue_after_review = _request_json(
            "GET",
            f"{api_base}/documents/chunks/review-queue?{urlencode({'limit': 10, 'offset': 0, 'section_role': 'appendix', 'document_id': seed['document_id']})}",
            token=admin_token,
        )
        _assert(queue_after_review.get("total") == 0, "Reviewed chunk still appears in review queue")

        review_filtered_search = _request_json(
            "POST",
            f"{api_base}/search/semantic",
            token=admin_token,
            payload={
                "query": "api workflow smoke phu luc vat tu",
                "limit": 5,
                "section_role": "appendix",
                "requires_review": True,
            },
        )
        _assert(
            all(result.get("chunk_id") != seed["appendix_chunk_id"] for result in review_filtered_search.get("results", [])),
            "Reviewed chunk still appears in requires_review search",
        )

        contract_search = _request_json(
            "POST",
            f"{api_base}/search/semantic",
            token=admin_token,
            payload={
                "query": "api workflow smoke vat tu",
                "limit": 5,
                "supplier_name": seed["supplier_name"],
            },
        )
        contract_results = contract_search.get("results", [])
        _assert(contract_results, "Contract supplier_name search returned no results")
        _assert(
            all(result.get("document_id") == seed["document_id"] for result in contract_results),
            "Contract supplier_name search returned chunks from other documents",
        )
        _assert(
            all(result.get("supplier_name") == seed["supplier_name"] for result in contract_results),
            "Contract supplier_name search missing contract metadata",
        )

        contract_number_search = _request_json(
            "POST",
            f"{api_base}/search/semantic",
            token=admin_token,
            payload={
                "query": "api workflow smoke vat tu",
                "limit": 5,
                "contract_number": seed["contract_number"],
            },
        )
        _assert(
            any(result.get("chunk_id") in created_chunk_ids for result in contract_number_search.get("results", [])),
            "Contract number search did not return smoke chunks",
        )

        unrelated_contract_search = _request_json(
            "POST",
            f"{api_base}/search/semantic",
            token=admin_token,
            payload={
                "query": "api workflow smoke vat tu",
                "limit": 5,
                "supplier_name": "Nha cung cap khong ton tai",
            },
        )
        _assert(
            not unrelated_contract_search.get("results"),
            "Contract supplier_name search should return empty for unrelated supplier",
        )

        if not keep_data:
            _cleanup_created_data(db=db, qdrant=qdrant, document_id=seed["document_id"], user_id=seed["user_id"])
            db.commit()

        return {
            "document_id": seed["document_id"],
            "appendix_chunk_id": seed["appendix_chunk_id"],
            "user_email": seed["user_email"],
            "cleanup": "kept" if keep_data else "removed",
        }
    except Exception:
        db.rollback()
        if not keep_data:
            _cleanup_created_data(db=db, qdrant=qdrant, document_id=created_document_id, user_id=created_user_id)
            db.commit()
        raise
    finally:
        db.close()


def _seed_smoke_data(*, db, qdrant: QdrantService) -> dict[str, str]:
    suffix = uuid4().hex[:10]
    fixture_text = (
        "PHU LUC I\n"
        f"api workflow smoke phu luc vat tu {suffix}\n"
        "Danh muc vat tu can review va doi chieu trong he thong semantic search."
    )
    normal_text = (
        f"api workflow smoke noi dung chinh {suffix}\n"
        "Van ban kiem tra semantic search co filter co ban va quyen truy cap."
    )
    documents = DocumentRepository(db)
    document = documents.create_document(
        title=f"{SMOKE_TITLE_PREFIX} {suffix}",
        original_filename=f"api-workflow-smoke-{suffix}.txt",
        file_path=f"/tmp/api-workflow-smoke-{suffix}.txt",
        content_type="text/plain",
        document_type="CV",
        document_number=f"API-SMOKE-{suffix}",
        issued_date=date(2026, 6, 5),
        issuing_agency="Phong Vat Tu Smoke",
        business_type="incoming_dispatch",
    )
    documents.create_file(
        document_id=document.id,
        original_filename=f"api-workflow-smoke-{suffix}.txt",
        file_path=f"/tmp/api-workflow-smoke-{suffix}.txt",
        content_type="text/plain",
        file_size=len(fixture_text.encode("utf-8")) + len(normal_text.encode("utf-8")),
        file_order=0,
        status="ocr_completed",
    )
    documents.create_page(document_id=document.id, page_number=1, text=f"{normal_text}\n\n{fixture_text}", confidence=0.55)
    normal_chunk = documents.create_chunk(
        document_id=document.id,
        chunk_index=0,
        text=normal_text,
        content_hash=hashlib.sha256(normal_text.encode("utf-8")).hexdigest(),
        page_from=1,
        page_to=1,
        section_title="NOI DUNG CHINH",
        doc_group="A",
        chunk_level="section",
        section_role="content",
        section_path=["NOI DUNG CHINH"],
        chunk_confidence=0.9,
        requires_review=False,
    )
    appendix_chunk = documents.create_chunk(
        document_id=document.id,
        chunk_index=1,
        text=fixture_text,
        content_hash=hashlib.sha256(fixture_text.encode("utf-8")).hexdigest(),
        page_from=1,
        page_to=1,
        section_title="PHU LUC I",
        doc_group="A",
        chunk_level="section",
        section_role="appendix",
        section_path=["PHU LUC I", "DANH MUC VAT TU"],
        chunk_confidence=0.42,
        requires_review=True,
    )
    documents.update_status(document, "searchable")

    contract_number = f"HD-SMOKE-{suffix}"
    supplier_name = f"Nha cung cap smoke {suffix}"
    contract = ContractRepository(db).create(
        document_id=document.id,
        contract_number=contract_number,
        contract_title="Hop dong smoke api workflow",
        supplier_name=supplier_name,
        sign_date=date(2026, 6, 5),
        status="active",
        currency="VND",
    )

    user_email = f"{SMOKE_USER_EMAIL_PREFIX}{suffix}@example.local"
    user = UserRepository(db).create(
        email=user_email,
        full_name="API Workflow Smoke User",
        password_hash=hash_password(SMOKE_PASSWORD),
        role="user",
        is_active=True,
    )
    db.commit()
    db.refresh(document)
    db.refresh(normal_chunk)
    db.refresh(appendix_chunk)
    db.refresh(user)

    embeddings = EmbeddingService()
    for chunk in (normal_chunk, appendix_chunk):
        qdrant.upsert_chunk(
            point_id=chunk.id,
            vector=embeddings.embed(chunk.text),
            payload=build_qdrant_payload(document, chunk),
        )
        documents.update_chunk_qdrant_point_id(chunk, chunk.id)
    db.commit()
    return {
        "document_id": document.id,
        "normal_chunk_id": normal_chunk.id,
        "appendix_chunk_id": appendix_chunk.id,
        "user_id": user.id,
        "user_email": user.email,
        "contract_id": contract.id,
        "contract_number": contract_number,
        "supplier_name": supplier_name,
    }


def _login(*, api_base: str, email: str, password: str, expected_role: str) -> str:
    response = _request_json(
        "POST",
        f"{api_base}/auth/login",
        payload={"email": email, "password": password},
    )
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
        raise AssertionError(f"{method} {url} returned {exc.code}, expected {expected_status}: {body}") from exc
    except URLError as exc:
        raise AssertionError(f"{method} {url} failed: {exc}") from exc
    _assert(status == expected_status, f"{method} {url} returned {status}, expected {expected_status}: {body}")
    return json.loads(body) if body else {}


def _expect_http_status(method: str, url: str, *, token: str, expected_status: int, label: str) -> None:
    request = Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}, method=method)
    try:
        with urlopen(request, timeout=20) as response:
            status = response.status
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        status = exc.code
        body = exc.read().decode("utf-8", errors="replace")
    except URLError as exc:
        raise AssertionError(f"{label} failed: {exc}") from exc
    _assert(status == expected_status, f"{label} returned {status}, expected {expected_status}: {body}")


def _chunk_requires_review(*, db, chunk_id: str) -> bool:
    db.expire_all()
    chunk = db.get(DocumentChunk, chunk_id)
    _assert(chunk is not None, f"Chunk not found: {chunk_id}")
    return bool(chunk.requires_review)


def _qdrant_requires_review(*, qdrant: QdrantService, point_id: str) -> bool:
    qdrant.ensure_collection()
    points = qdrant.client.retrieve(
        collection_name=qdrant.settings.qdrant_collection,
        ids=[point_id],
        with_payload=True,
        with_vectors=False,
    )
    _assert(points, f"Qdrant point not found: {point_id}")
    return bool((points[0].payload or {}).get("requires_review"))


def _cleanup_existing_smoke_data(*, db, qdrant: QdrantService) -> None:
    docs = list(db.scalars(select(Document).where(Document.title.like(f"{SMOKE_TITLE_PREFIX}%"))))
    users = list(db.scalars(select(User).where(User.email.like(f"{SMOKE_USER_EMAIL_PREFIX}%"))))
    for document in docs:
        _cleanup_created_data(db=db, qdrant=qdrant, document_id=document.id, user_id=None)
    for user in users:
        user.deleted_at = datetime.now(timezone.utc)
        user.is_active = False
        db.add(user)
    db.commit()


def _cleanup_created_data(*, db, qdrant: QdrantService, document_id: str | None, user_id: str | None) -> None:
    deleted_at = datetime.now(timezone.utc)
    if document_id:
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
        document = db.get(Document, document_id)
        if document is not None:
            document.deleted_at = deleted_at
            db.add(document)
    if user_id:
        user = db.get(User, user_id)
        if user is not None:
            user.deleted_at = deleted_at
            user.is_active = False
            db.add(user)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run reusable HTTP smoke checks for auth, search, review queue, and review action.")
    parser.add_argument("--api-base", default="http://localhost:8000/api/v1", help="API base URL, default is the api container localhost.")
    parser.add_argument("--keep-data", action="store_true", help="Keep smoke document and user for debugging.")
    args = parser.parse_args()

    result = run_smoke(api_base=args.api_base.rstrip("/"), keep_data=args.keep_data)
    print(
        "api workflow smoke passed: "
        f"document_id={result['document_id']} appendix_chunk_id={result['appendix_chunk_id']} "
        f"user_email={result['user_email']} cleanup={result['cleanup']}"
    )


if __name__ == "__main__":
    main()
