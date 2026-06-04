from __future__ import annotations

import re
import unicodedata

from app.services.ocr_chunking.mappings import FUZZY_REPLACEMENTS


def normalize_vietnamese_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text or "")
    for pattern, replacement in FUZZY_REPLACEMENTS:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    lines = [" ".join(line.strip().split()) for line in normalized.splitlines()]
    return "\n".join(line for line in lines if line)


def strip_vietnamese_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text or "")
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return without_marks.replace("đ", "d").replace("Đ", "D")


def normalize_for_detection(text: str) -> str:
    return strip_vietnamese_accents(normalize_vietnamese_text(text)).lower()


def token_count(text: str) -> int:
    return len((text or "").split())
