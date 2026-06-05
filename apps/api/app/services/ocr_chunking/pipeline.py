from __future__ import annotations

from dataclasses import replace
import hashlib
import re

from app.services.ocr_chunking.anchors import (
    APPENDIX_RE,
    ARTICLE_RE,
    CHAPTER_RE,
    CLAUSE_RE,
    POINT_RE,
    ROMAN_SECTION_RE,
    SIGNATURE_RE,
    TABLE_HINT_RE,
)
from app.services.ocr_chunking.classifier import detect_doc_type
from app.services.ocr_chunking.entities import extract_entities
from app.services.ocr_chunking.mappings import DOC_TYPE_TO_GROUP
from app.services.ocr_chunking.normalizer import normalize_for_detection, normalize_vietnamese_text, token_count
from app.services.ocr_chunking.schemas import Chunk, FallbackInfo, OCRBlock, OCRDocument

DEFAULT_BBOX = (0.0, 0.0, 0.0, 0.0)
APPENDIX_HEADING_RE = re.compile(
    r"^\s*phu\s+luc(?:\s+(?P<number>[ivxlcdm]+|\d{1,3}|[a-z]))?(?:\s*[:.\-–]\s*(?P<title>.*))?\s*$",
    re.IGNORECASE,
)
APPENDIX_ATTACHMENT_RE = re.compile(
    r"\b(?:ban\s+hanh\s+kem\s+theo|kem\s+theo\s+(?:quyet\s+dinh|cong\s+van|thong\s+tu|nghi\s+dinh)\s+so)\b",
    re.IGNORECASE,
)


class _Line:
    def __init__(self, text: str, page: int, bbox: tuple[float, float, float, float] | None, confidence: float | None):
        self.text = text
        self.page = page
        self.bbox = bbox
        self.confidence = confidence


class _Section:
    def __init__(
        self,
        role: str,
        title: str,
        lines: list[_Line],
        level: str = "section",
        article_number: str | None = None,
        clause_number: str | None = None,
        point_number: str | None = None,
        source_anchor: str = "",
        path: list[str] | None = None,
        requires_review: bool = False,
    ):
        self.role = role
        self.title = title
        self.lines = lines
        self.level = level
        self.article_number = article_number
        self.clause_number = clause_number
        self.point_number = point_number
        self.source_anchor = source_anchor
        self.path = path or ([title] if title else [])
        self.requires_review = requires_review


def chunk_document(input: OCRDocument) -> list[Chunk]:
    lines = _flatten_lines(input)
    full_text = "\n".join(line.text for line in lines)
    normalized = normalize_vietnamese_text(full_text)
    doc_type, doc_group, classification_confidence, detected_anchor = detect_doc_type(normalized, input.doc_type)

    fallback = _fallback_info(doc_type, normalized, detected_anchor)
    if fallback.used_fallback:
        sections = _split_unknown(lines, fallback)
    elif doc_group == "A":
        sections = _split_group_a(lines)
    elif doc_group == "B":
        sections = _split_group_b(lines, doc_type)
    elif doc_group == "C":
        sections = _split_group_c(lines, doc_type)
    elif doc_group == "D":
        sections = _split_group_d(lines, doc_type)
    else:
        sections = _split_unknown(lines, fallback)

    if not sections:
        sections = _split_unknown(lines, replace(fallback, used_fallback=True, fallback_reason="empty_or_unstructured_text"))

    chunks: list[Chunk] = []
    for section in sections:
        chunks.extend(
            _section_to_chunks(
                section=section,
                doc_id=input.doc_id,
                doc_type=doc_type,
                doc_group=DOC_TYPE_TO_GROUP.get(doc_type, "E"),
                ocr_confidence=input.ocr_confidence,
                layout_confidence=input.layout_confidence,
                classification_confidence=classification_confidence,
                fallback_info=fallback if fallback.used_fallback else FallbackInfo(candidate_doc_type=doc_type),
            )
        )

    return _link_neighbors(chunks)


def _flatten_lines(input: OCRDocument) -> list[_Line]:
    lines: list[_Line] = []
    if input.pages:
        for page in input.pages:
            if page.blocks:
                for block in page.blocks:
                    for text_line in normalize_vietnamese_text(block.text).splitlines():
                        lines.append(_Line(text_line, block.page or page.page_number, block.bbox, block.confidence))
            else:
                for text_line in normalize_vietnamese_text(page.text).splitlines():
                    lines.append(_Line(text_line, page.page_number, None, page.confidence))
    else:
        for text_line in normalize_vietnamese_text(input.text).splitlines():
            lines.append(_Line(text_line, 1, None, input.ocr_confidence))
    return [line for line in lines if line.text.strip()]


def _fallback_info(doc_type: str, text: str, detected_anchor: str | None) -> FallbackInfo:
    plain = normalize_for_detection(text)
    used = doc_type == "UNKNOWN"
    reason = None
    if used:
        reason = "missing_formal_title_or_low_anchor_confidence"
    if len(plain) > 80 and len(re.findall(r"\w+", plain)) < 10:
        used = True
        reason = "ocr_text_too_sparse"
    return FallbackInfo(used_fallback=used, fallback_reason=reason, candidate_doc_type=None if used else doc_type)


def _split_group_a(lines: list[_Line]) -> list[_Section]:
    sections: list[_Section] = []
    current: list[_Line] = []
    current_role = "header"
    current_title = "Header"
    current_article: str | None = None
    current_path: list[str] = []

    def flush(level: str = "section") -> None:
        nonlocal current
        if current:
            sections.append(
                _Section(
                    current_role,
                    current_title,
                    current,
                    level=level,
                    article_number=current_article if current_role == "article" else None,
                    source_anchor=current_title.split(" ", 1)[0],
                    path=current_path[:] or [current_title],
                )
            )
            current = []

    def start(role: str, title: str, line: _Line, path: list[str] | None = None) -> None:
        nonlocal current_role, current_title, current, current_path
        flush()
        current_role = role
        current_title = title
        if path is not None:
            current_path = path
        current = [line]

    for line in lines:
        article = ARTICLE_RE.match(line.text)
        chapter = CHAPTER_RE.match(line.text)
        appendix = _appendix_anchor(line)
        if appendix is not None:
            start(
                "appendix",
                appendix[0],
                line,
                [appendix[0]],
            )
            if appendix[1]:
                current.append(_Line(appendix[1], line.page, line.bbox, line.confidence))
            continue
        if chapter:
            start("chapter", line.text, line, [f"Chương {chapter.group('number')}"])
            flush("section")
            continue
        if re.search(r"^\s*Căn cứ\b", line.text, flags=re.IGNORECASE):
            if current_role != "legal_basis":
                start("legal_basis", line.text, line, ["Căn cứ"])
            else:
                current.append(line)
            continue
        if re.search(r"^\s*Xét đề nghị\b", line.text, flags=re.IGNORECASE):
            start("promulgation", line.text, line, ["Xét đề nghị"])
            continue
        if article:
            current_article = article.group("number")
            path = [*current_path[:1], f"Điều {current_article}"] if _in_appendix_context(current_path) else [f"Điều {current_article}"]
            start("article", line.text, line, path)
            continue
        if SIGNATURE_RE.search(line.text):
            start("signature", line.text, line, ["Chữ ký/Nơi nhận"])
            flush("signature")
            continue
        current.append(line)
    flush()
    return _refine_article_sections(sections)


def _refine_article_sections(sections: list[_Section]) -> list[_Section]:
    refined: list[_Section] = []
    for section in sections:
        if section.role != "article":
            refined.append(section)
            continue
        article_match = ARTICLE_RE.match(section.lines[0].text)
        article_number = article_match.group("number") if article_match else None
        bucket: list[_Line] = []
        clause_number: str | None = None
        for line in section.lines:
            clause = CLAUSE_RE.match(line.text)
            if clause and bucket and not ARTICLE_RE.match(line.text):
                refined.append(
                    _Section(
                        "clause",
                        bucket[0].text,
                        bucket,
                        level="subsection",
                        article_number=article_number,
                        clause_number=clause_number,
                        source_anchor="Khoản",
                        path=[*section.path, f"Khoản {clause_number}"] if clause_number else section.path,
                    )
                )
                bucket = []
            if clause and not ARTICLE_RE.match(line.text):
                clause_number = clause.group("number")
            bucket.append(line)
        if bucket:
            role = "clause" if clause_number else "article"
            refined.append(
                _Section(
                    role,
                    bucket[0].text,
                    bucket,
                    level="subsection" if clause_number else "section",
                    article_number=article_number,
                    clause_number=clause_number,
                    source_anchor="Điều",
                    path=[*section.path, f"Khoản {clause_number}"] if clause_number else section.path,
                )
            )
    return refined


def _split_group_b(lines: list[_Line], doc_type: str) -> list[_Section]:
    sections: list[_Section] = []
    current: list[_Line] = []
    current_title = "Header"
    current_role = "header"
    for line in lines:
        role = _role_group_b(line.text, doc_type)
        starts_section = ROMAN_SECTION_RE.match(line.text) or re.match(r"^\s*\d+\.\s+\S+", line.text) or role in {
            "recipient",
            "objective",
            "requirement",
            "task",
            "timeline",
            "budget",
            "recommendation",
            "signature",
            "appendix",
        }
        if starts_section and current:
            sections.append(_Section(current_role, current_title, current, path=[current_title]))
            current = []
        if starts_section:
            current_title = line.text
            current_role = role
        current.append(line)
    if current:
        sections.append(_Section(current_role, current_title, current, path=[current_title]))
    return sections


def _split_group_c(lines: list[_Line], doc_type: str) -> list[_Section]:
    if doc_type == "HĐ":
        return _split_group_a(lines)

    sections: list[_Section] = []
    current: list[_Line] = []
    current_role = "header"
    current_title = "Header"
    current_path: list[str] = []
    for line in lines:
        appendix = _appendix_anchor(line)
        if appendix is not None:
            if current:
                sections.append(_Section(current_role, current_title, current, path=current_path[:] or [current_title]))
                current = []
            current_role = "appendix"
            current_title = appendix[0]
            current_path = [appendix[0]]
            current.append(line)
            if appendix[1]:
                current.append(_Line(appendix[1], line.page, line.bbox, line.confidence))
            continue
        role = _role_group_c(line.text)
        starts_section = role != "content" and (not current or role != current_role)
        if starts_section and current:
            sections.append(_Section(current_role, current_title, current, path=current_path[:] or [current_title]))
            current = []
        if starts_section:
            current_role = role
            current_title = line.text
            current_path = [line.text]
        current.append(line)
    if current:
        sections.append(_Section(current_role, current_title, current, path=current_path[:] or [current_title]))
    return sections


def _split_group_d(lines: list[_Line], doc_type: str) -> list[_Section]:
    text = "\n".join(line.text for line in lines)
    if token_count(text) <= 1000:
        return [_Section("single_doc_chunk", doc_type, lines, level="document", source_anchor=doc_type, path=[doc_type])]
    return _split_unknown(lines, FallbackInfo(True, "short_document_too_long", doc_type))


def _split_unknown(lines: list[_Line], fallback: FallbackInfo) -> list[_Section]:
    sections: list[_Section] = []
    current: list[_Line] = []
    current_page = lines[0].page if lines else 1
    current_role = "page_chunk"
    current_title = f"Trang {current_page}"
    current_path = [current_title]

    def flush() -> None:
        nonlocal current
        if not current:
            return
        role = current_role
        title = current_title
        path = current_path[:]
        if role == "page_chunk":
            role = "table_candidate_chunk" if any(TABLE_HINT_RE.search(line.text) for line in current) else "paragraph_chunk"
        sections.append(_Section(role, title, current, level="paragraph", path=path))
        current = []

    for line in lines:
        appendix = _appendix_anchor(line)
        if appendix is not None:
            flush()
            current_page = line.page
            current_role = "appendix"
            current_title = appendix[0]
            current_path = [appendix[0]]
            current = [line]
            if appendix[1]:
                current.append(_Line(appendix[1], line.page, line.bbox, line.confidence))
            continue
        if line.page != current_page and current:
            flush()
            current_page = line.page
            if current_role != "appendix":
                current_role = "page_chunk"
                current_title = f"Trang {current_page}"
                current_path = [current_title]
        current.append(line)
    flush()
    return sections


def _role_group_b(text: str, doc_type: str) -> str:
    if _appendix_anchor_text(text) is not None:
        return "appendix"
    if re.search(r"\bKính gửi\b", text, flags=re.IGNORECASE):
        return "recipient"
    if re.search(r"\b(?:Mục đích|Yêu cầu)\b", text, flags=re.IGNORECASE):
        return "objective" if "Mục đích" in text else "requirement"
    if re.search(r"\b(?:Nhiệm vụ|Tổ chức thực hiện|Giải pháp|Nội dung)\b", text, flags=re.IGNORECASE):
        return "task" if "Nhiệm vụ" in text or "Tổ chức" in text else "content"
    if re.search(r"\bTiến độ\b", text, flags=re.IGNORECASE):
        return "timeline"
    if re.search(r"\bKinh phí\b", text, flags=re.IGNORECASE):
        return "budget"
    if re.search(r"\b(?:Kiến nghị|Đề xuất)\b", text, flags=re.IGNORECASE):
        return "recommendation"
    if SIGNATURE_RE.search(text):
        return "signature"
    if TABLE_HINT_RE.search(text):
        return "table"
    return "content" if doc_type != "CV" else "context"


def _role_group_c(text: str) -> str:
    if _appendix_anchor_text(text) is not None:
        return "appendix"
    if re.search(r"\b(?:Hôm nay|vào hồi|Tại)\b", text, flags=re.IGNORECASE):
        return "time_location"
    if re.search(r"\b(?:Thành phần|Đại diện)\b", text, flags=re.IGNORECASE):
        return "participants"
    if re.search(r"\bBên A\b", text, flags=re.IGNORECASE):
        return "party_a"
    if re.search(r"\bBên B\b", text, flags=re.IGNORECASE):
        return "party_b"
    if re.search(r"\b(?:Bàn giao|Số lượng|Đơn giá|Thành tiền)\b", text, flags=re.IGNORECASE):
        return "table_items"
    if re.search(r"\bThanh toán\b", text, flags=re.IGNORECASE):
        return "payment_terms"
    if SIGNATURE_RE.search(text):
        return "signature_parties"
    return "content"


def _section_to_chunks(
    section: _Section,
    doc_id: str,
    doc_type: str,
    doc_group: str,
    ocr_confidence: float | None,
    layout_confidence: float | None,
    classification_confidence: float,
    fallback_info: FallbackInfo,
) -> list[Chunk]:
    text = "\n".join(line.text for line in section.lines).strip()
    if not text:
        return []
    limit, overlap = _retrieval_policy(doc_group, section.role, fallback_info)
    if token_count(text) <= limit or section.role in {"table", "table_items", "single_doc_chunk"}:
        return [
            _build_chunk(
                section,
                section.lines,
                doc_id,
                doc_type,
                doc_group,
                ocr_confidence,
                layout_confidence,
                classification_confidence,
                fallback_info,
                None,
            )
        ]

    parent = _build_chunk(
        section,
        section.lines,
        doc_id,
        doc_type,
        doc_group,
        ocr_confidence,
        layout_confidence,
        classification_confidence,
        fallback_info,
        None,
        level="section",
    )
    chunks = [parent]
    words = text.split()
    start = 0
    while start < len(words):
        end = min(start + limit, len(words))
        child_text = " ".join([*section.path, *words[start:end]])
        child_line = _Line(child_text, section.lines[0].page, section.lines[0].bbox, section.lines[0].confidence)
        chunks.append(
            _build_chunk(
                section,
                [child_line],
                doc_id,
                doc_type,
                doc_group,
                ocr_confidence,
                layout_confidence,
                classification_confidence,
                fallback_info,
                parent.chunk_id,
                level="paragraph",
            )
        )
        if end == len(words):
            break
        start = max(end - overlap, start + 1)
    return chunks


def _build_chunk(
    section: _Section,
    lines: list[_Line],
    doc_id: str,
    doc_type: str,
    doc_group: str,
    ocr_confidence: float | None,
    layout_confidence: float | None,
    classification_confidence: float,
    fallback_info: FallbackInfo,
    parent_chunk_id: str | None,
    level: str | None = None,
) -> Chunk:
    text = "\n".join(line.text for line in lines).strip()
    avg_ocr = _avg_conf(line.confidence for line in lines) or ocr_confidence or 0.0
    layout = layout_confidence if layout_confidence is not None else 0.0
    confidence = round(min(avg_ocr or 0.75, classification_confidence, layout or 1.0), 2)
    requires_review = section.requires_review or fallback_info.used_fallback or avg_ocr < 0.65 or classification_confidence < 0.65
    appendix_context = _section_is_appendix_context(section)
    return Chunk(
        chunk_id=_chunk_id(doc_id, section.role, text),
        doc_id=doc_id,
        doc_type=doc_type,
        doc_group=doc_group,
        chunk_level=_chunk_level(level or section.level, section.role),
        section_role=_public_role(section.role),
        section_title=section.title[:512],
        section_path=section.path,
        article_number=section.article_number,
        clause_number=section.clause_number,
        point_number=section.point_number,
        page_start=min(line.page for line in lines),
        page_end=max(line.page for line in lines),
        bbox_start=lines[0].bbox or DEFAULT_BBOX,
        bbox_end=lines[-1].bbox or DEFAULT_BBOX,
        text=text,
        text_normalized=normalize_vietnamese_text(text),
        source_anchor=section.source_anchor or section.title.split(" ", 1)[0],
        confidence=confidence,
        ocr_confidence=round(avg_ocr, 2),
        layout_confidence=round(layout, 2),
        classification_confidence=round(classification_confidence, 2),
        parent_chunk_id=parent_chunk_id,
        contains_table=section.role in {"table", "table_items"} or bool(TABLE_HINT_RE.search(text)),
        contains_signature=section.role in {"signature", "signature_parties"} or bool(SIGNATURE_RE.search(text)),
        contains_appendix=appendix_context,
        requires_review=requires_review,
        entities=extract_entities(text),
        fallback_info=fallback_info,
    )


def _retrieval_policy(doc_group: str, role: str, fallback: FallbackInfo) -> tuple[int, int]:
    if doc_group == "A":
        return (900, 100) if role == "clause" else (1000, 50)
    if doc_group == "B":
        return (900, 120)
    if doc_group == "C":
        return (900, 80)
    if doc_group == "D":
        return (1000, 0)
    return (700, 180 if fallback.fallback_reason == "ocr_text_too_sparse" else 130)


def _chunk_level(level: str, role: str) -> str:
    if role in {"table", "table_items"}:
        return "table"
    if role in {"signature", "signature_parties"}:
        return "signature"
    if level in {"document", "section", "subsection", "paragraph"}:
        return level
    return "section"


def _public_role(role: str) -> str:
    aliases = {
        "single_doc_chunk": "unknown",
        "page_chunk": "unknown",
        "paragraph_chunk": "unknown",
        "heading_candidate_chunk": "unknown",
        "table_candidate_chunk": "table",
        "signature_candidate_chunk": "signature",
        "signature_parties": "signature",
        "table_items": "table",
    }
    return aliases.get(role, role)


def _appendix_anchor(line: _Line) -> tuple[str, str | None] | None:
    return _appendix_anchor_text(line.text)


def _appendix_anchor_text(text: str) -> tuple[str, str | None] | None:
    stripped = " ".join((text or "").strip().split())
    if not stripped:
        return None
    plain = normalize_for_detection(stripped)
    match = APPENDIX_HEADING_RE.match(plain)
    if match and _looks_like_appendix_heading(stripped, plain):
        title = _appendix_title(stripped, match.group("number"))
        suffix = (match.group("title") or "").strip()
        return title, suffix or None
    if (
        "phu luc" in plain
        and APPENDIX_ATTACHMENT_RE.search(plain)
        and len(plain.split()) <= 24
        and not _starts_like_body_clause(stripped)
    ):
        return stripped[:512], None
    return None


def _looks_like_appendix_heading(original: str, plain: str) -> bool:
    words = plain.split()
    if len(words) <= 6:
        return True
    if original.isupper() and len(words) <= 12:
        return True
    return False


def _appendix_title(original: str, number: str | None) -> str:
    prefix_match = re.match(r"^\s*(phụ\s+lục(?:\s+[^\s:.\-–]+)?)", original, flags=re.IGNORECASE)
    if prefix_match:
        return prefix_match.group(1).strip()[:512]
    return f"Phụ lục {number.upper()}"[:512] if number else "Phụ lục"


def _starts_like_body_clause(text: str) -> bool:
    return bool(ARTICLE_RE.match(text) or CLAUSE_RE.match(text) or POINT_RE.match(text) or ROMAN_SECTION_RE.match(text))


def _in_appendix_context(path: list[str]) -> bool:
    return bool(path) and normalize_for_detection(path[0]).startswith("phu luc")


def _section_is_appendix_context(section: _Section) -> bool:
    return section.role == "appendix" or _in_appendix_context(section.path)


def _avg_conf(values: object) -> float | None:
    nums = [float(value) for value in values if value is not None]
    if not nums:
        return None
    return sum(nums) / len(nums)


def _chunk_id(doc_id: str, role: str, text: str) -> str:
    digest = hashlib.sha256(f"{doc_id}:{role}:{text}".encode("utf-8")).hexdigest()[:16]
    return f"chk_{digest}"


def _link_neighbors(chunks: list[Chunk]) -> list[Chunk]:
    linked: list[Chunk] = []
    for index, chunk in enumerate(chunks):
        linked.append(
            replace(
                chunk,
                previous_chunk_id=chunks[index - 1].chunk_id if index > 0 else None,
                next_chunk_id=chunks[index + 1].chunk_id if index + 1 < len(chunks) else None,
            )
        )
    return linked
