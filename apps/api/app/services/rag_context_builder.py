from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


SnippetFn = Callable[[str, str], str]


@dataclass(frozen=True)
class ContextBlock:
    index: int
    chunk_id: str
    text: str


class RagContextBuilder:
    SNIPPET_MAX_CHARS = 600

    def __init__(self, *, max_context_chars: int = 8000) -> None:
        self.max_context_chars = max_context_chars

    def build(self, query: str, evidence: list[dict], *, snippet_fn: SnippetFn) -> tuple[str, list[dict]]:
        ordered = self._select_evidence(evidence)
        blocks: list[ContextBlock] = []
        for index, item in enumerate(ordered, start=1):
            blocks.append(
                ContextBlock(
                    index=index,
                    chunk_id=str(item.get("chunk_id") or ""),
                    text=self._format_block(index, item, query, snippet_fn),
                )
            )

        while blocks and sum(len(block.text) for block in blocks) > self.max_context_chars:
            blocks.pop()

        trimmed_evidence = ordered[: len(blocks)]
        context_text = "\n\n".join(block.text for block in blocks)
        return context_text, trimmed_evidence

    def _select_evidence(self, evidence: list[dict]) -> list[dict]:
        preferred = [item for item in evidence if not item.get("requires_review")]
        return preferred or list(evidence)

    def _format_block(self, index: int, item: dict, query: str, snippet_fn: SnippetFn) -> str:
        title = str(item.get("title") or "Không rõ tên văn bản")
        document_number = str(item.get("document_number") or "—")
        page_from = item.get("page_from")
        page_to = item.get("page_to")
        if page_from is not None and page_to is not None:
            page_label = f"Trang {page_from}-{page_to}"
        elif page_from is not None:
            page_label = f"Trang {page_from}"
        else:
            page_label = "Trang —"

        section_path = item.get("section_path") or []
        section_label = " > ".join(str(part) for part in section_path) if section_path else "—"
        chunk_id = str(item.get("chunk_id") or "")
        header = (
            f"[{index}] chunk_id={chunk_id} | {title} | Số: {document_number} | "
            f"{page_label} | {section_label}"
        )
        snippet = snippet_fn(query, str(item.get("text") or ""))
        if len(snippet) > self.SNIPPET_MAX_CHARS:
            snippet = snippet[: self.SNIPPET_MAX_CHARS].rsplit(" ", 1)[0].strip()
        return f"{header}\n{snippet}"
