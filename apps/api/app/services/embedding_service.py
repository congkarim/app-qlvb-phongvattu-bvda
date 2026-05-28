import hashlib
import math

from app.core.config import get_settings


class EmbeddingService:
    def __init__(self) -> None:
        self.dimensions = get_settings().embedding_dimensions

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values = []
        for index in range(self.dimensions):
            byte = digest[index % len(digest)]
            values.append((byte / 255.0) - 0.5)

        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        return [value / norm for value in values]
