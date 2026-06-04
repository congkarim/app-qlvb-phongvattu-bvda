from __future__ import annotations

import hashlib
from typing import Any, Protocol

from app.services.ocr_chunking.pipeline import chunk_document
from app.services.ocr_chunking.schemas import OCRDocument, OCRPage


class PageContent(Protocol):
    page_number: int
    text: str
    confidence: float


def create_chunk_payloads(
    *,
    doc_id: str,
    document_type: str | None,
    page_contents: list[PageContent],
) -> list[dict[str, Any]]:
    ocr_document = OCRDocument(
        doc_id=doc_id,
        doc_type=document_type,
        pages=[
            OCRPage(
                page_number=page_content.page_number,
                text=page_content.text,
                confidence=page_content.confidence,
            )
            for page_content in page_contents
        ],
        ocr_confidence=_average_confidence(page_contents),
    )
    chunks = chunk_document(ocr_document)
    return [
        {
            "text": chunk.text,
            "section_title": _section_title(chunk.section_path, chunk.section_title),
            "content_hash": hashlib.sha256(chunk.text.encode("utf-8")).hexdigest(),
            "page_from": chunk.page_start,
            "page_to": chunk.page_end,
            "chunk_metadata": chunk.to_dict(),
        }
        for chunk in chunks
    ]


def _average_confidence(page_contents: list[PageContent]) -> float | None:
    values = [page_content.confidence for page_content in page_contents if page_content.confidence is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _section_title(section_path: list[str], section_title: str) -> str:
    title = " > ".join(item for item in section_path if item) or section_title
    return title[:512]
