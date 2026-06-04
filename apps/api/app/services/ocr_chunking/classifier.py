from __future__ import annotations

import re

from app.services.ocr_chunking.mappings import DOC_TYPE_PATTERNS, DOC_TYPE_TO_GROUP
from app.services.ocr_chunking.normalizer import normalize_for_detection, normalize_vietnamese_text


def detect_doc_type(text: str, declared_doc_type: str | None = None) -> tuple[str, str, float, str | None]:
    normalized = normalize_vietnamese_text(text)
    detection_text = "\n".join(normalized.splitlines()[:45]) or normalized[:4000]
    plain = normalize_for_detection(detection_text)

    for doc_type, pattern, confidence in DOC_TYPE_PATTERNS:
        match = re.search(pattern, plain, flags=re.IGNORECASE)
        if match:
            return doc_type, DOC_TYPE_TO_GROUP[doc_type], confidence, match.group(0)

    if declared_doc_type in DOC_TYPE_TO_GROUP and declared_doc_type != "UNKNOWN":
        return declared_doc_type, DOC_TYPE_TO_GROUP[declared_doc_type], 0.70, declared_doc_type

    return "UNKNOWN", "E", 0.35, None
