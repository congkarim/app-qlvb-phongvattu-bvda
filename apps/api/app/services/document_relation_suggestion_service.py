from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.repositories.document_relation_repository import DocumentRelationRepository
from app.repositories.document_repository import DocumentRepository
from app.utils.document_number import (
    clean_document_value,
    infer_document_type_from_symbol,
    normalize_chunk_text,
    normalize_document_number,
)

MAX_SUGGESTIONS = 8
CONFIDENCE_HIGH_THRESHOLD = 0.80
CONFIDENCE_MIN_THRESHOLD = 0.50
ANCHOR_CONTEXT_WINDOW = 200
QUOTE_MAX_LENGTH = 200

PREFERRED_SECTION_ROLES = frozenset({"article", "unknown"})
EXCLUDED_SECTION_ROLES = frozenset({"appendix", "signature", "recipient", "task"})

STRONG_REFERENCE_RE = re.compile(
    r"(?:Căn\s*cứ\s+)?(?:Quyết\s*định|Q[ĐD]|Công\s*văn|CV|Hợp\s*đồng|H[ĐD]|Thông\s*báo|TB|Chỉ\s*thị|CT|Nghị\s*quyết|NQ)\s*"
    r"(?:số\s*)?(?P<num>\d+)\s*/\s*(?P<sym>[A-ZÀ-ỸĐa-zà-ỹ][A-ZÀ-ỸĐa-zà-ỹ0-9.\-]*)",
    re.IGNORECASE | re.UNICODE,
)
SO_PREFIX_REFERENCE_RE = re.compile(r"\bSố\s*:\s*(?P<full>[^\n]{3,80})", re.IGNORECASE | re.UNICODE)
STANDALONE_REFERENCE_RE = re.compile(
    r"\b(?P<num>\d{1,4})\s*/\s*(?P<sym>Q[ĐD][-\w]*|CV[-\w]*|H[ĐD][-\w]*|TB[-\w]*|NQ[-\w]*|CT[-\w]*|[A-ZĐ]{2,}[-\w]*)",
    re.IGNORECASE | re.UNICODE,
)

ANCHOR_RULES: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (re.compile(r"\bCăn\s*cứ\b|\bcăn\s*cứ\b|\bXét\b", re.IGNORECASE | re.UNICODE), "references", "anchor:can_cu"),
    (
        re.compile(r"\bPhụ\s*lục\b|\bKèm\s*theo\b|\bđính\s*kèm\b", re.IGNORECASE | re.UNICODE),
        "appendix_of",
        "anchor:phu_luc",
    ),
    (
        re.compile(r"\bThực\s*hiện\b|\btriển\s*khai\b|\bTổ\s*chức\s*thực\s*hiện\b", re.IGNORECASE | re.UNICODE),
        "implements",
        "anchor:thuc_hien",
    ),
)

PatternStrength = Literal["strong", "so_prefix", "weak"]


class DocumentRelationSuggestionNotFoundError(ValueError):
    pass


@dataclass(frozen=True)
class ReferenceCandidate:
    matched_reference: str
    normalized_number: str
    pattern_strength: PatternStrength
    match_start: int
    match_end: int


@dataclass(frozen=True)
class SuggestionDraft:
    target_document_id: str
    relation_type: str
    confidence: float
    confidence_tier: str
    matched_reference: str
    source_chunk_id: str
    source_chunk_quote: str
    target_document_preview: dict[str, Any]
    reasons: tuple[str, ...]


class DocumentRelationSuggestionService:
    def __init__(self, db: Session):
        self.db = db
        self.documents = DocumentRepository(db)
        self.relations = DocumentRelationRepository(db)

    def suggest_relations(self, document_id: str) -> dict[str, Any]:
        normalized_document_id = self._normalize_required(document_id, "document_id")
        document = self.documents.get_document(normalized_document_id)
        if document is None:
            raise DocumentRelationSuggestionNotFoundError("Document not found")
        if document.status != "searchable":
            return {
                "document_id": normalized_document_id,
                "suggestions": [],
                "candidate_count": 0,
            }

        chunks = self.documents.list_chunks_for_document(normalized_document_id)
        source_chunks = select_source_chunks(chunks)
        drafts: list[SuggestionDraft] = []
        chunk_by_index = {chunk.chunk_index: chunk for chunk in chunks}

        for chunk in source_chunks:
            prev_chunk = chunk_by_index.get(chunk.chunk_index - 1)
            prev_text = prev_chunk.text if prev_chunk is not None else ""
            for candidate in extract_reference_candidates(chunk.text):
                target = self._resolve_target_document(
                    candidate.normalized_number,
                    exclude_document_id=normalized_document_id,
                )
                if target is None:
                    continue
                context = build_anchor_context(
                    chunk_text=chunk.text,
                    prev_chunk_text=prev_text,
                    match_start=candidate.match_start,
                    match_end=candidate.match_end,
                )
                relation_type, anchor_reason = infer_relation_type_from_context(context, candidate.normalized_number)
                if self._should_exclude(
                    source_document_id=normalized_document_id,
                    target_document_id=target.id,
                    relation_type=relation_type,
                ):
                    continue
                confidence, reasons, confidence_tier = compute_suggestion_confidence(
                    pattern_strength=candidate.pattern_strength,
                    anchor_reason=anchor_reason,
                    chunk=chunk,
                )
                if confidence < CONFIDENCE_MIN_THRESHOLD:
                    continue
                drafts.append(
                    SuggestionDraft(
                        target_document_id=target.id,
                        relation_type=relation_type,
                        confidence=confidence,
                        confidence_tier=confidence_tier,
                        matched_reference=candidate.matched_reference,
                        source_chunk_id=chunk.id,
                        source_chunk_quote=build_chunk_quote(chunk.text, candidate.match_start),
                        target_document_preview=self._document_preview(target),
                        reasons=reasons,
                    )
                )

        suggestions = dedupe_and_cap_suggestions(drafts)
        return {
            "document_id": normalized_document_id,
            "suggestions": [self._draft_to_dict(item) for item in suggestions],
            "candidate_count": len(suggestions),
        }

    def _resolve_target_document(
        self,
        normalized_number: str,
        *,
        exclude_document_id: str,
    ) -> Document | None:
        matches = self.documents.find_searchable_by_document_number(
            normalized_number,
            exclude_document_id=exclude_document_id,
        )
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]

        inferred_type = infer_document_type_from_symbol(normalized_number.split("/", 1)[1])
        if inferred_type:
            typed_matches = [document for document in matches if document.document_type == inferred_type]
            if len(typed_matches) == 1:
                return typed_matches[0]
        return None

    def _should_exclude(
        self,
        *,
        source_document_id: str,
        target_document_id: str,
        relation_type: str,
    ) -> bool:
        if source_document_id == target_document_id:
            return True
        return self.relations.find_active(
            source_document_id=source_document_id,
            target_document_id=target_document_id,
            relation_type=relation_type,
        ) is not None

    def _document_preview(self, document: Document) -> dict[str, Any]:
        return {
            "id": document.id,
            "title": document.title,
            "document_number": document.document_number,
            "document_type": document.document_type,
            "status": document.status,
        }

    def _draft_to_dict(self, draft: SuggestionDraft) -> dict[str, Any]:
        return {
            "target_document_id": draft.target_document_id,
            "relation_type": draft.relation_type,
            "confidence": round(draft.confidence, 4),
            "confidence_tier": draft.confidence_tier,
            "matched_reference": draft.matched_reference,
            "source_chunk_id": draft.source_chunk_id,
            "source_chunk_quote": draft.source_chunk_quote,
            "target_document_preview": draft.target_document_preview,
            "reasons": list(draft.reasons),
        }

    def _normalize_required(self, value: Any, field_name: str) -> str:
        normalized = clean_document_value(str(value).strip() if value is not None else None, 128)
        if normalized is None:
            raise ValueError(f"{field_name} is required")
        return normalized


def select_source_chunks(chunks: list[DocumentChunk]) -> list[DocumentChunk]:
    if not chunks:
        return []

    page_chunks = [chunk for chunk in chunks if _chunk_on_pages_one_or_two(chunk)]
    if not page_chunks:
        page_chunks = chunks[:2]

    preferred = [
        chunk
        for chunk in page_chunks
        if (chunk.section_role or "unknown") in PREFERRED_SECTION_ROLES
        and _chunk_has_reference_signal(chunk.text)
    ]
    if preferred:
        return preferred

    fallback = [
        chunk
        for chunk in page_chunks
        if (chunk.section_role or "unknown") not in EXCLUDED_SECTION_ROLES
        and _chunk_has_reference_signal(chunk.text)
    ]
    if fallback:
        return fallback

    return page_chunks


def extract_reference_candidates(text: str) -> list[ReferenceCandidate]:
    normalized_text = normalize_chunk_text(text)
    candidates: list[ReferenceCandidate] = []
    seen_numbers: set[str] = set()

    for pattern, strength in (
        (STRONG_REFERENCE_RE, "strong"),
        (SO_PREFIX_REFERENCE_RE, "so_prefix"),
        (STANDALONE_REFERENCE_RE, "weak"),
    ):
        for match in pattern.finditer(normalized_text):
            if strength == "so_prefix":
                full_value = clean_document_value(match.group("full"), 128)
                if not full_value or "/" not in full_value:
                    continue
                number, symbol = full_value.split("/", 1)
                normalized_number = normalize_document_number(f"{number.strip()}/{symbol.strip()}")
                matched_reference = clean_document_value(match.group(0), 128) or full_value
            else:
                normalized_number = normalize_document_number(f"{match.group('num')}/{match.group('sym')}")
                matched_reference = clean_document_value(match.group(0), 128)
            if not normalized_number or not matched_reference:
                continue
            if normalized_number in seen_numbers:
                continue
            seen_numbers.add(normalized_number)
            candidates.append(
                ReferenceCandidate(
                    matched_reference=matched_reference,
                    normalized_number=normalized_number,
                    pattern_strength=strength,
                    match_start=match.start(),
                    match_end=match.end(),
                )
            )
    return candidates


def build_anchor_context(*, chunk_text: str, prev_chunk_text: str, match_start: int, match_end: int) -> str:
    local_start = max(0, match_start - ANCHOR_CONTEXT_WINDOW)
    local_context = chunk_text[local_start:match_end]
    remaining = ANCHOR_CONTEXT_WINDOW - len(local_context)
    if remaining > 0 and prev_chunk_text:
        prefix = prev_chunk_text[-remaining:]
        return f"{prefix}{local_context}"
    return local_context


def infer_relation_type_from_context(context: str, normalized_number: str) -> tuple[str, str | None]:
    symbol = normalized_number.split("/", 1)[1] if "/" in normalized_number else ""
    symbol_upper = symbol.upper()
    for pattern, relation_type, reason in ANCHOR_RULES:
        if pattern.search(context):
            if relation_type == "appendix_of" and not symbol_upper.startswith(("HĐ", "HD")):
                continue
            return relation_type, reason
    return "related", None


def compute_suggestion_confidence(
    *,
    pattern_strength: PatternStrength,
    anchor_reason: str | None,
    chunk: DocumentChunk,
) -> tuple[float, tuple[str, ...], str]:
    score = 0.55
    reasons: list[str] = ["exact_document_number_match"]

    if pattern_strength == "strong":
        score += 0.20
        reasons.append("strong_reference_pattern")
    elif pattern_strength == "so_prefix":
        score += 0.10
        reasons.append("weak_reference_pattern")
    else:
        score += 0.10
        reasons.append("weak_reference_pattern")

    if anchor_reason:
        score += 0.15
        reasons.append(anchor_reason)

    if _chunk_on_page_one(chunk):
        score += 0.05
        reasons.append("source_page_1")

    if (chunk.section_role or "unknown") == "article":
        score += 0.05
        reasons.append("source_section_article")

    confidence = min(score, 1.0)
    tier = "high" if confidence >= CONFIDENCE_HIGH_THRESHOLD else "review"
    return confidence, tuple(reasons), tier


def build_chunk_quote(text: str, match_start: int) -> str:
    start = max(0, match_start - 80)
    end = min(len(text), match_start + 120)
    quote = " ".join(text[start:end].split())
    return quote[:QUOTE_MAX_LENGTH]


def dedupe_and_cap_suggestions(drafts: list[SuggestionDraft]) -> list[SuggestionDraft]:
    best_by_key: dict[tuple[str, str], SuggestionDraft] = {}
    for draft in drafts:
        key = (draft.target_document_id, draft.relation_type)
        existing = best_by_key.get(key)
        if existing is None or draft.confidence > existing.confidence:
            best_by_key[key] = draft
    ordered = sorted(best_by_key.values(), key=lambda item: item.confidence, reverse=True)
    return ordered[:MAX_SUGGESTIONS]


def _chunk_on_pages_one_or_two(chunk: DocumentChunk) -> bool:
    if chunk.page_from is not None:
        return chunk.page_from <= 2
    if chunk.page_to is not None:
        return chunk.page_to <= 2
    return chunk.chunk_index < 2


def _chunk_on_page_one(chunk: DocumentChunk) -> bool:
    if chunk.page_from is not None:
        return chunk.page_from == 1
    return chunk.chunk_index == 0


def _chunk_has_reference_signal(text: str) -> bool:
    normalized_text = normalize_chunk_text(text)
    if STRONG_REFERENCE_RE.search(normalized_text):
        return True
    if SO_PREFIX_REFERENCE_RE.search(normalized_text):
        return True
    if STANDALONE_REFERENCE_RE.search(normalized_text):
        return True
    return any(pattern.search(normalized_text) for pattern, _, _ in ANCHOR_RULES)
