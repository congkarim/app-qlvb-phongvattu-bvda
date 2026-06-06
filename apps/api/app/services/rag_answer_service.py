from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from sqlalchemy.orm import Session

from app.services.search_rerank_service import normalize_search_text
from app.services.search_service import SearchService


class SearchBackend(Protocol):
    def semantic_search(
        self,
        *,
        query: str,
        limit: int,
        document_type: str | None = None,
        department_id: str | None = None,
        business_type: str | None = None,
        document_number: str | None = None,
        issued_date: date | None = None,
        doc_group: str | None = None,
        section_role: str | None = None,
        requires_review: bool | None = None,
    ) -> list[dict]:
        ...


@dataclass(frozen=True)
class RagAnswerConfig:
    fallback_answer: str = (
        "Không đủ căn cứ trong các đoạn đã truy xuất để trả lời chắc chắn. "
        "Hãy thử truy vấn cụ thể hơn hoặc kiểm tra trực tiếp các nguồn liên quan."
    )
    minimum_query_terms: int = 2
    quote_max_chars: int = 420


class RagAnswerService:
    def __init__(
        self,
        db: Session | None = None,
        *,
        search_backend: SearchBackend | None = None,
        config: RagAnswerConfig | None = None,
    ) -> None:
        self.search = search_backend or SearchService(db)
        self.config = config or RagAnswerConfig()

    def answer(
        self,
        *,
        query: str,
        limit: int,
        min_score: float,
        max_citations: int,
        document_type: str | None = None,
        department_id: str | None = None,
        business_type: str | None = None,
        document_number: str | None = None,
        issued_date: date | None = None,
        doc_group: str | None = None,
        section_role: str | None = None,
        requires_review: bool | None = None,
    ) -> dict:
        results = self.search.semantic_search(
            query=query,
            limit=limit,
            document_type=document_type,
            department_id=department_id,
            business_type=business_type,
            document_number=document_number,
            issued_date=issued_date,
            doc_group=doc_group,
            section_role=section_role,
            requires_review=requires_review,
        )
        evidence = [
            result
            for result in results
            if float(result.get("score") or 0.0) >= min_score
            and self._has_query_overlap(query, str(result.get("text") or ""))
        ][:max_citations]

        citations = [self._citation(query, result) for result in evidence]
        if not self._has_enough_evidence(query, evidence):
            return {
                "query": query,
                "answer": self.config.fallback_answer,
                "grounded": False,
                "confidence": 0.0,
                "fallback_reason": "insufficient_evidence",
                "citations": citations,
            }

        return {
            "query": query,
            "answer": self._compose_answer(citations),
            "grounded": True,
            "confidence": self._confidence(citations),
            "fallback_reason": None,
            "citations": citations,
        }

    def _has_enough_evidence(self, query: str, evidence: list[dict]) -> bool:
        if not evidence:
            return False
        query_terms = self._query_terms(query)
        if len(query_terms) < self.config.minimum_query_terms:
            return True
        combined = normalize_search_text(" ".join(str(item.get("text") or "") for item in evidence))
        matched = sum(1 for term in query_terms if term in combined)
        return matched >= min(len(query_terms), self.config.minimum_query_terms)

    def _has_query_overlap(self, query: str, text: str) -> bool:
        query_terms = self._query_terms(query)
        if not query_terms:
            return bool(text.strip())
        text_norm = normalize_search_text(text)
        matched = sum(1 for term in query_terms if term in text_norm)
        return matched >= min(len(query_terms), self.config.minimum_query_terms)

    def _compose_answer(self, citations: list[dict]) -> str:
        snippets = [citation["quote"].rstrip(".") for citation in citations if citation["quote"]]
        return "Dựa trên các đoạn đã truy xuất: " + ". ".join(snippets) + "."

    def _citation(self, query: str, result: dict) -> dict:
        return {
            "document_id": str(result.get("document_id") or ""),
            "chunk_id": str(result.get("chunk_id") or ""),
            "score": float(result.get("score") or 0.0),
            "quote": self._quote(query, str(result.get("text") or "")),
            "title": result.get("title"),
            "document_type": result.get("document_type"),
            "document_number": result.get("document_number"),
            "issued_date": result.get("issued_date"),
            "issuing_agency": result.get("issuing_agency"),
            "business_type": result.get("business_type"),
            "page_from": result.get("page_from"),
            "page_to": result.get("page_to"),
            "section_role": result.get("section_role"),
            "section_path": result.get("section_path") or [],
        }

    def _quote(self, query: str, text: str) -> str:
        sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
        if not sentences:
            return text[: self.config.quote_max_chars].strip()
        query_terms = self._query_terms(query)
        ranked = sorted(
            sentences,
            key=lambda sentence: self._sentence_overlap(sentence, query_terms),
            reverse=True,
        )
        quote = ranked[0]
        if len(quote) > self.config.quote_max_chars:
            quote = quote[: self.config.quote_max_chars].rsplit(" ", 1)[0].strip()
        return quote

    def _sentence_overlap(self, sentence: str, query_terms: set[str]) -> int:
        sentence_norm = normalize_search_text(sentence)
        return sum(1 for term in query_terms if term in sentence_norm)

    def _query_terms(self, query: str) -> set[str]:
        return {term for term in re.findall(r"\w+", normalize_search_text(query)) if len(term) >= 3}

    def _confidence(self, citations: list[dict]) -> float:
        if not citations:
            return 0.0
        top_scores = [float(citation["score"]) for citation in citations]
        normalized = min(1.0, sum(top_scores) / len(top_scores))
        coverage_bonus = min(0.15, 0.05 * len(citations))
        return round(min(1.0, normalized + coverage_bonus), 4)
