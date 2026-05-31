import hashlib
import re


class ChunkingService:
    SECTION_TITLE_MAX_CHARS = 512
    SECTION_TITLE_LOOKAHEAD_CHARS = 180

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
        matches = list(re.finditer(r"(?i)\bĐiều\s+\d+[a-zA-Z]?\b", text))
        if not matches:
            return [(None, text)]

        sections: list[tuple[str | None, str]] = []
        for index, match in enumerate(matches):
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            section_text = text[start:end].strip()
            sections.append((self._section_title_from_match(section_text, match.group(0)), section_text))
        return sections

    def _section_title_from_match(self, section_text: str, marker: str) -> str:
        candidate = section_text[: self.SECTION_TITLE_LOOKAHEAD_CHARS].strip()
        sentence_match = re.search(r"[.;:]", candidate)
        if sentence_match:
            candidate = candidate[: sentence_match.end()].strip()
        else:
            candidate = marker.strip()

        return candidate[: self.SECTION_TITLE_MAX_CHARS].rstrip()

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
