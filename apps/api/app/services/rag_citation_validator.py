from __future__ import annotations

import re
from dataclasses import dataclass


INSUFFICIENT_EVIDENCE_PHRASE = "Không đủ căn cứ trong các đoạn đã cung cấp"
MARKER_PATTERN = re.compile(r"\[(\d+)\]")


@dataclass(frozen=True)
class CitationValidationResult:
    valid: bool
    marker_indices: tuple[int, ...]


class CitationValidator:
    def is_insufficient_claim(self, raw_answer: str) -> bool:
        normalized = " ".join(raw_answer.split())
        return INSUFFICIENT_EVIDENCE_PHRASE.casefold() in normalized.casefold()

    def validate(self, raw_answer: str, evidence_count: int) -> CitationValidationResult:
        if evidence_count <= 0:
            return CitationValidationResult(valid=False, marker_indices=())

        if self.is_insufficient_claim(raw_answer):
            return CitationValidationResult(valid=False, marker_indices=())

        marker_indices: list[int] = []
        for match in MARKER_PATTERN.finditer(raw_answer):
            index = int(match.group(1))
            if index < 1 or index > evidence_count:
                return CitationValidationResult(valid=False, marker_indices=())
            marker_indices.append(index)

        if not marker_indices:
            return CitationValidationResult(valid=False, marker_indices=())

        return CitationValidationResult(valid=True, marker_indices=tuple(dict.fromkeys(marker_indices)))
