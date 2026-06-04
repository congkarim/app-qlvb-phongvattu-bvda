from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

BBox = tuple[float, float, float, float]


@dataclass(frozen=True)
class OCRBlock:
    text: str
    page: int = 1
    bbox: BBox | None = None
    confidence: float | None = None
    block_type: str | None = None


@dataclass(frozen=True)
class OCRPage:
    page_number: int
    text: str = ""
    confidence: float | None = None
    blocks: list[OCRBlock] = field(default_factory=list)


@dataclass(frozen=True)
class OCRDocument:
    doc_id: str
    text: str = ""
    pages: list[OCRPage] = field(default_factory=list)
    doc_type: str | None = None
    ocr_confidence: float | None = None
    layout_confidence: float | None = None


@dataclass(frozen=True)
class ChunkEntities:
    agency: str | None = None
    document_number: str | None = None
    issued_date: str | None = None
    subject: str | None = None
    recipient: list[str] = field(default_factory=list)
    signer: str | None = None
    deadline: str | None = None
    responsible_unit: list[str] = field(default_factory=list)
    amount: str | None = None
    person_names: list[str] = field(default_factory=list)
    organizations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FallbackInfo:
    used_fallback: bool = False
    fallback_reason: str | None = None
    candidate_doc_type: str | None = None


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    doc_type: str
    doc_group: str
    chunk_level: Literal["document", "section", "subsection", "paragraph", "table", "signature"]
    section_role: str
    section_title: str
    section_path: list[str]
    article_number: str | None
    clause_number: str | None
    point_number: str | None
    page_start: int
    page_end: int
    bbox_start: BBox | None
    bbox_end: BBox | None
    text: str
    text_normalized: str
    source_anchor: str
    confidence: float
    ocr_confidence: float
    layout_confidence: float
    classification_confidence: float
    parent_chunk_id: str | None = None
    previous_chunk_id: str | None = None
    next_chunk_id: str | None = None
    contains_table: bool = False
    contains_signature: bool = False
    contains_appendix: bool = False
    requires_review: bool = False
    entities: ChunkEntities = field(default_factory=ChunkEntities)
    fallback_info: FallbackInfo = field(default_factory=FallbackInfo)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.bbox_start is not None:
            payload["bbox_start"] = list(self.bbox_start)
        if self.bbox_end is not None:
            payload["bbox_end"] = list(self.bbox_end)
        return payload
