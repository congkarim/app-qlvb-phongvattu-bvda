from __future__ import annotations

import re

from app.services.ocr_chunking.schemas import ChunkEntities


def extract_entities(text: str) -> ChunkEntities:
    document_number = _first(r"\bSố\s*:\s*([^\n]+)", text)
    issued_date = _first(r"\bngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}\b", text)
    subject = _first(r"\bV/v\s*[:\-]?\s*([^\n]+)", text) or _title_candidate(text)
    recipient = re.findall(r"Kính gửi\s*[:\-]?\s*([^\n]+)", text, flags=re.IGNORECASE)
    amount = _first(r"(\d[\d\.\,]*\s*(?:đồng|VND))", text)
    deadline = _first(r"(?:trước|đến|từ)\s+ngày\s+\d{1,2}[/-]\d{1,2}[/-]\d{4}", text)

    return ChunkEntities(
        agency=_agency_candidate(text),
        document_number=_clean(document_number),
        issued_date=_clean(issued_date),
        subject=_clean(subject),
        recipient=[_clean(item) for item in recipient if _clean(item)],
        signer=_signer_candidate(text),
        deadline=_clean(deadline),
        amount=_clean(amount),
    )


def _first(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1) if match.lastindex else match.group(0)


def _agency_candidate(text: str) -> str | None:
    for line in text.splitlines()[:8]:
        if 5 <= len(line) <= 160 and not re.search(r"CỘNG HÒA|Độc lập|Số\s*:", line, flags=re.IGNORECASE):
            return _clean(line)
    return None


def _title_candidate(text: str) -> str | None:
    for line in text.splitlines()[:20]:
        if line.isupper() and 5 <= len(line) <= 180:
            return line
    return None


def _signer_candidate(text: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in reversed(lines[-12:]):
        if re.search(r"^[A-ZÀ-Ỹ][A-Za-zÀ-ỹ\s]{4,80}$", line) and not line.isupper():
            return line
    return None


def _clean(value: str | None) -> str | None:
    if not value:
        return None
    return " ".join(value.strip(" .;:,").split()) or None
