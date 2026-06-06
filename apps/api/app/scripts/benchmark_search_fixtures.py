from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.document import Document, DocumentChunk, DocumentFile, DocumentPage
from app.repositories.document_repository import DocumentRepository
from app.services.chunk_payload import build_qdrant_payload
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService
from app.services.search_service import SearchService


BENCHMARK_TITLE_PREFIX = "[BENCHMARK] Search fixture"


@dataclass(frozen=True)
class ChunkFixture:
    key: str
    text: str
    page_from: int
    page_to: int
    section_title: str
    doc_group: str
    section_role: str
    section_path: list[str]
    chunk_confidence: float = 0.92
    requires_review: bool = False


@dataclass(frozen=True)
class DocumentFixture:
    key: str
    title: str
    document_type: str
    document_number: str
    issued_date: date
    issuing_agency: str
    business_type: str
    chunks: list[ChunkFixture]


@dataclass(frozen=True)
class BenchmarkCase:
    key: str
    query: str
    expected_chunk_key: str
    top_k: int = 5
    filters: dict[str, Any] = field(default_factory=dict)


DOCUMENT_FIXTURES = (
    DocumentFixture(
        key="procurement_plan",
        title="Ke hoach mua sam vat tu may bom nam 2026",
        document_type="KH",
        document_number="KH-42/VT",
        issued_date=date(2026, 5, 10),
        issuing_agency="Phong Vat Tu",
        business_type="incoming_dispatch",
        chunks=[
            ChunkFixture(
                key="vat_tu_list",
                text=(
                    "Danh muc vat tu uu tien gom may bom cap nuoc, ong thep DN50, "
                    "van khoa va phu kien lap dat cho kho vat tu thang 5 nam 2026."
                ),
                page_from=1,
                page_to=1,
                section_title="Danh muc vat tu",
                doc_group="B",
                section_role="content",
                section_path=["Ke hoach mua sam", "Danh muc vat tu"],
            ),
            ChunkFixture(
                key="date_plan",
                text=(
                    "Ke hoach mua sam ban hanh ngay 2026-05-10 ap dung cho dot bo sung "
                    "vat tu sua chua he thong bom tai kho trung tam."
                ),
                page_from=1,
                page_to=1,
                section_title="Thoi gian thuc hien",
                doc_group="B",
                section_role="content",
                section_path=["Ke hoach mua sam", "Thoi gian"],
            ),
        ],
    ),
    DocumentFixture(
        key="contract_appendix",
        title="Hop dong cung cap vat tu va phu luc danh muc thiet bi",
        document_type="HD",
        document_number="HD-17/2026",
        issued_date=date(2026, 4, 22),
        issuing_agency="Cong ty Co khi Song Da",
        business_type="contract",
        chunks=[
            ChunkFixture(
                key="appendix_equipment",
                text=(
                    "PHU LUC I. Danh muc thiet bi kem theo hop dong: may nen khi, "
                    "bo loc dau, day curoa va vat tu thay the can ban giao."
                ),
                page_from=4,
                page_to=5,
                section_title="PHU LUC I",
                doc_group="A",
                section_role="appendix",
                section_path=["PHU LUC I", "Danh muc thiet bi"],
                chunk_confidence=0.86,
            )
        ],
    ),
    DocumentFixture(
        key="contract_terms",
        title="Quy dinh nghiem thu va thanh toan vat tu",
        document_type="QD",
        document_number="QD-09/VT",
        issued_date=date(2026, 3, 18),
        issuing_agency="Ban Quan ly Du an",
        business_type="decision",
        chunks=[
            ChunkFixture(
                key="article_acceptance",
                text=(
                    "Dieu 3. Nghiem thu vat tu. Ben giao hang phai cung cap bien ban "
                    "nghiem thu, chung chi xuat xu va ket qua kiem tra chat luong truoc khi thanh toan."
                ),
                page_from=2,
                page_to=2,
                section_title="Dieu 3. Nghiem thu vat tu",
                doc_group="A",
                section_role="article",
                section_path=["Dieu 3", "Nghiem thu vat tu"],
            )
        ],
    ),
    DocumentFixture(
        key="issuing_agency",
        title="Thong bao quy trinh cap phat vat tu",
        document_type="TB",
        document_number="TB-12/PVT",
        issued_date=date(2026, 5, 28),
        issuing_agency="Phong Vat Tu",
        business_type="outgoing_dispatch",
        chunks=[
            ChunkFixture(
                key="agency_process",
                text=(
                    "Phong Vat Tu ban hanh quy trinh cap phat vat tu cho cac don vi su dung. "
                    "Moi yeu cau linh kien phai co phieu de nghi va xac nhan ton kho."
                ),
                page_from=1,
                page_to=1,
                section_title="Quy trinh cap phat",
                doc_group="B",
                section_role="content",
                section_path=["Thong bao", "Quy trinh cap phat"],
            )
        ],
    ),
)


BENCHMARK_CASES = (
    BenchmarkCase(
        key="vat_tu",
        query="danh muc vat tu may bom",
        expected_chunk_key="vat_tu_list",
    ),
    BenchmarkCase(
        key="phu_luc",
        query="phu luc danh muc thiet bi kem theo",
        expected_chunk_key="appendix_equipment",
        filters={"section_role": "appendix"},
    ),
    BenchmarkCase(
        key="dieu_khoan",
        query="dieu 3 nghiem thu vat tu",
        expected_chunk_key="article_acceptance",
    ),
    BenchmarkCase(
        key="ngay_ban_hanh",
        query="ke hoach mua sam ngay 2026-05-10",
        expected_chunk_key="date_plan",
        filters={"issued_date": date(2026, 5, 10)},
    ),
    BenchmarkCase(
        key="don_vi_ban_hanh",
        query="phong vat tu ban hanh quy trinh cap phat",
        expected_chunk_key="agency_process",
    ),
)


def run_benchmark(*, keep_data: bool, top_k: int, json_output: bool) -> dict[str, Any]:
    db = SessionLocal()
    qdrant = QdrantService()
    created_document_ids: list[str] = []
    try:
        _cleanup_existing_benchmark_data(db=db, qdrant=qdrant)
        seeded = _seed_benchmark_data(db=db, qdrant=qdrant)
        created_document_ids = seeded["document_ids"]
        chunk_ids_by_key = seeded["chunk_ids_by_key"]

        case_reports = [
            _run_case(
                db=db,
                case=case,
                expected_chunk_id=chunk_ids_by_key[case.expected_chunk_key],
                top_k=top_k,
            )
            for case in BENCHMARK_CASES
        ]
        passed = all(report["passed"] for report in case_reports)
        summary = {
            "passed": passed,
            "total": len(case_reports),
            "passed_count": sum(1 for report in case_reports if report["passed"]),
            "failed_count": sum(1 for report in case_reports if not report["passed"]),
            "cases": case_reports,
            "cleanup": "kept" if keep_data else "removed",
        }

        if not keep_data:
            _cleanup_documents(db=db, qdrant=qdrant, document_ids=created_document_ids)
            db.commit()

        if json_output:
            print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
        else:
            _print_report(summary)

        if not passed:
            raise AssertionError(f"Search benchmark failed: {summary['failed_count']} case(s) failed")
        return summary
    except Exception:
        db.rollback()
        if not keep_data:
            _cleanup_documents(db=db, qdrant=qdrant, document_ids=created_document_ids)
            db.commit()
        raise
    finally:
        db.close()


def _seed_benchmark_data(*, db, qdrant: QdrantService) -> dict[str, Any]:
    suffix = uuid4().hex[:10]
    documents = DocumentRepository(db)
    embeddings = EmbeddingService()
    document_ids: list[str] = []
    chunk_ids_by_key: dict[str, str] = {}

    for fixture in DOCUMENT_FIXTURES:
        document = documents.create_document(
            title=f"{BENCHMARK_TITLE_PREFIX} {fixture.title} {suffix}",
            original_filename=f"search-benchmark-{fixture.key}-{suffix}.txt",
            file_path=f"/tmp/search-benchmark-{fixture.key}-{suffix}.txt",
            content_type="text/plain",
            document_type=fixture.document_type,
            document_number=f"{fixture.document_number}-{suffix}",
            issued_date=fixture.issued_date,
            issuing_agency=fixture.issuing_agency,
            business_type=fixture.business_type,
        )
        documents.create_file(
            document_id=document.id,
            original_filename=f"search-benchmark-{fixture.key}-{suffix}.txt",
            file_path=f"/tmp/search-benchmark-{fixture.key}-{suffix}.txt",
            content_type="text/plain",
            file_size=sum(len(chunk.text.encode("utf-8")) for chunk in fixture.chunks),
            file_order=0,
            status="ocr_completed",
        )
        documents.create_page(
            document_id=document.id,
            page_number=1,
            text="\n\n".join(chunk.text for chunk in fixture.chunks),
            confidence=0.91,
        )
        for chunk_index, chunk_fixture in enumerate(fixture.chunks):
            content_hash = hashlib.sha256(f"{suffix}:{chunk_fixture.text}".encode("utf-8")).hexdigest()
            chunk = documents.create_chunk(
                document_id=document.id,
                chunk_index=chunk_index,
                text=chunk_fixture.text,
                content_hash=content_hash,
                page_from=chunk_fixture.page_from,
                page_to=chunk_fixture.page_to,
                section_title=chunk_fixture.section_title,
                doc_group=chunk_fixture.doc_group,
                chunk_level="section",
                section_role=chunk_fixture.section_role,
                section_path=chunk_fixture.section_path,
                chunk_confidence=chunk_fixture.chunk_confidence,
                requires_review=chunk_fixture.requires_review,
            )
            chunk_ids_by_key[chunk_fixture.key] = chunk.id
        documents.update_status(document, "searchable")
        document_ids.append(document.id)

    db.commit()

    for chunk in db.scalars(
        select(DocumentChunk).where(DocumentChunk.document_id.in_(document_ids))
    ):
        qdrant.upsert_chunk(
            point_id=chunk.id,
            vector=embeddings.embed(chunk.text),
            payload=build_qdrant_payload(chunk.document, chunk),
        )
        documents.update_chunk_qdrant_point_id(chunk, chunk.id)
    db.commit()
    return {"document_ids": document_ids, "chunk_ids_by_key": chunk_ids_by_key}


def _run_case(*, db, case: BenchmarkCase, expected_chunk_id: str, top_k: int) -> dict[str, Any]:
    filters = dict(case.filters)
    results = SearchService(db).semantic_search(
        query=case.query,
        limit=max(case.top_k, top_k),
        **_search_filters(filters),
    )
    result_chunk_ids = [result["chunk_id"] for result in results[: case.top_k]]
    rank = result_chunk_ids.index(expected_chunk_id) + 1 if expected_chunk_id in result_chunk_ids else None
    return {
        "key": case.key,
        "query": case.query,
        "filters": _serializable_filters(filters),
        "expected_chunk_id": expected_chunk_id,
        "expected_top_k": case.top_k,
        "rank": rank,
        "passed": rank is not None,
        "top_results": [_format_result(result, index + 1) for index, result in enumerate(results[:top_k])],
    }


def _search_filters(filters: dict[str, Any]) -> dict[str, Any]:
    defaults = {
        "document_type": None,
        "department_id": None,
        "business_type": None,
        "document_number": None,
        "issued_date": None,
        "doc_group": None,
        "section_role": None,
        "requires_review": None,
    }
    defaults.update(filters)
    return defaults


def _serializable_filters(filters: dict[str, Any]) -> dict[str, Any]:
    return {key: value.isoformat() if isinstance(value, date) else value for key, value in filters.items()}


def _format_result(result: dict[str, Any], rank: int) -> dict[str, Any]:
    return {
        "rank": rank,
        "chunk_id": result["chunk_id"],
        "score": result["score"],
        "title": result.get("title"),
        "document_number": result.get("document_number"),
        "issued_date": str(result.get("issued_date")) if result.get("issued_date") else None,
        "issuing_agency": result.get("issuing_agency"),
        "page": _format_page(result),
        "section_role": result.get("section_role"),
        "section_path": result.get("section_path") or [],
        "text_preview": str(result.get("text") or "")[:160],
    }


def _format_page(result: dict[str, Any]) -> str | None:
    page_from = result.get("page_from")
    page_to = result.get("page_to")
    if page_from is None:
        return None
    if page_to and page_to != page_from:
        return f"{page_from}-{page_to}"
    return str(page_from)


def _print_report(summary: dict[str, Any]) -> None:
    print(
        "search benchmark fixtures: "
        f"{summary['passed_count']}/{summary['total']} passed, cleanup={summary['cleanup']}"
    )
    for case in summary["cases"]:
        status = "PASS" if case["passed"] else "FAIL"
        rank = case["rank"] or "-"
        print(f"[{status}] {case['key']} rank={rank}/{case['expected_top_k']} query={case['query']!r}")
        if case["filters"]:
            print(f"  filters={case['filters']}")
        for result in case["top_results"]:
            citation = (
                f"{result['title']} | so={result['document_number']} | ngay={result['issued_date']} | "
                f"don_vi={result['issuing_agency']} | trang={result['page']} | "
                f"{result['section_role']}:{' > '.join(result['section_path'])}"
            )
            print(f"  #{result['rank']} score={result['score']:.4f} chunk={result['chunk_id']} | {citation}")


def _cleanup_existing_benchmark_data(*, db, qdrant: QdrantService) -> None:
    docs = list(db.scalars(select(Document).where(Document.title.like(f"{BENCHMARK_TITLE_PREFIX}%"))))
    _cleanup_documents(db=db, qdrant=qdrant, document_ids=[document.id for document in docs])
    db.commit()


def _cleanup_documents(*, db, qdrant: QdrantService, document_ids: list[str]) -> None:
    if not document_ids:
        return
    deleted_at = datetime.now(timezone.utc)
    point_ids = [
        chunk.qdrant_point_id or chunk.id
        for chunk in db.scalars(select(DocumentChunk).where(DocumentChunk.document_id.in_(document_ids)))
        if chunk.qdrant_point_id or chunk.id
    ]
    qdrant.delete_points(point_ids)
    for model in (DocumentChunk, DocumentPage, DocumentFile):
        for row in db.scalars(select(model).where(model.document_id.in_(document_ids))):
            row.deleted_at = deleted_at
            db.add(row)
    for document in db.scalars(select(Document).where(Document.id.in_(document_ids))):
        document.deleted_at = deleted_at
        db.add(document)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local semantic search benchmark fixtures.")
    parser.add_argument("--keep-data", action="store_true", help="Keep benchmark documents and Qdrant points for debugging.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top results to print per benchmark case.")
    parser.add_argument("--json", action="store_true", help="Print benchmark report as JSON.")
    args = parser.parse_args()

    run_benchmark(keep_data=args.keep_data, top_k=max(1, args.top_k), json_output=args.json)


if __name__ == "__main__":
    main()
