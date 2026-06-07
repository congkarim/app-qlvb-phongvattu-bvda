from __future__ import annotations

import re
import unicodedata


def clean_document_value(value: str | None, max_length: int = 128) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.strip(" .;,:").split())
    return normalized[:max_length] or None


def normalize_document_number(value: str) -> str | None:
    cleaned = clean_document_value(value, 128)
    if not cleaned:
        return None
    cleaned = re.split(r"\s{2,}|(?=\b[A-ZÀ-Ỹ][a-zà-ỹ]+,\s*ngày\b)", cleaned, maxsplit=1)[0].strip(" .;,")
    if "/" not in cleaned:
        return cleaned or None
    number, symbol = cleaned.split("/", 1)
    number = number.strip()
    symbol = _fix_symbol_ocr(symbol.strip(" .;,"))
    if not number or not symbol:
        return cleaned or None
    return f"{number}/{symbol}"


def infer_document_type_from_symbol(symbol: str) -> str | None:
    upper = symbol.upper()
    if upper.startswith(("QĐ", "QD")):
        return "QĐ"
    if upper.startswith("CV"):
        return "CV"
    if upper.startswith(("HĐ", "HD")):
        return "HĐ"
    if upper.startswith("TB"):
        return "TB"
    if upper.startswith("NQ"):
        return "NQ"
    if upper.startswith("CT"):
        return "CT"
    return None


def normalize_chunk_text(text: str) -> str:
    return unicodedata.normalize("NFC", text or "")


def _fix_symbol_ocr(symbol: str) -> str:
    if symbol.upper().startswith("QD"):
        return "QĐ" + symbol[2:]
    if symbol.upper().startswith("HD"):
        return "HĐ" + symbol[2:]
    return symbol
