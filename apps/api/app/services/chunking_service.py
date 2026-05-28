import hashlib
import re


class ChunkingService:
    def create_chunks(self, text: str) -> list[dict[str, str | int | None]]:
        cleaned = " ".join(text.split())
        if not cleaned:
            return []

        sections = self._split_legal_sections(cleaned)
        chunks: list[dict[str, str | int | None]] = []
        for section_title, section_text in sections:
            for part in self._split_by_words(section_text, max_words=900, overlap_words=120):
                chunks.append(
                    {
                        "text": part,
                        "section_title": section_title,
                        "content_hash": hashlib.sha256(part.encode("utf-8")).hexdigest(),
                    }
                )
        return chunks

    def _split_legal_sections(self, text: str) -> list[tuple[str | None, str]]:
        matches = list(re.finditer(r"(?i)(Điều\s+\d+[^.]*\.?)", text))
        if not matches:
            return [(None, text)]

        sections: list[tuple[str | None, str]] = []
        for index, match in enumerate(matches):
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections.append((match.group(1).strip(), text[start:end].strip()))
        return sections

    def _split_by_words(self, text: str, max_words: int, overlap_words: int) -> list[str]:
        words = text.split()
        if len(words) <= max_words:
            return [text]

        chunks: list[str] = []
        start = 0
        while start < len(words):
            end = min(start + max_words, len(words))
            chunks.append(" ".join(words[start:end]))
            if end == len(words):
                break
            start = max(end - overlap_words, start + 1)
        return chunks
