from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class OcrLine:
    text: str
    confidence: float
    box: tuple[tuple[float, float], ...] | None = None


class OcrEngine(Protocol):
    def recognize(self, image_array: np.ndarray) -> list[OcrLine]:
        ...
