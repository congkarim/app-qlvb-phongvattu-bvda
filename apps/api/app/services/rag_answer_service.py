from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.services.local_llm_service import GenerateResult, LocalLLMError, LocalLLMService
from app.services.rag_citation_validator import CitationValidator
from app.services.rag_context_builder import RagContextBuilder
from app.services.search_rerank_service import normalize_search_text
from app.services.search_service import SearchService


logger = logging.getLogger(__name__)

GENERATIVE_SYSTEM_PROMPT = (
    "Bạn là trợ lý tra cứu văn bản hành chính tiếng Việt. Chỉ trả lời dựa trên các đoạn [1]..[n] được cung cấp.\n"
    "- Không bịa số văn bản, điều khoản hoặc nội dung không có trong context.\n"
    "- Mỗi ý quan trọng phải kèm tham chiếu [số] tương ứng đoạn nguồn.\n"
    '- Nếu context không đủ trả lời, trả lời ngắn: "Không đủ căn cứ trong các đoạn đã cung cấp." '
    "và không thêm thông tin ngoài context.\n"
    "- Trả lời súc tích, tiếng Việt chuẩn hành chính."
)


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
        issuing_agency: str | None = None,
        issued_date: date | None = None,
        doc_group: str | None = None,
        section_role: str | None = None,
        requires_review: bool | None = None,
        contract_number: str | None = None,
        supplier_name: str | None = None,
        contract_status: str | None = None,
        dispatch_type: str | None = None,
        dispatch_status: str | None = None,
        decision_kind: str | None = None,
        decision_status: str | None = None,
        effective_from: date | None = None,
        effective_to: date | None = None,
        procurement_kind: str | None = None,
        procurement_status: str | None = None,
        reference_number: str | None = None,
        requesting_unit: str | None = None,
        procurement_item_name: str | None = None,
        procurement_item_code: str | None = None,
    ) -> list[dict]:
        ...


class LLMBackend(Protocol):
    def is_generative_enabled(self) -> bool: ...

    def is_available(self) -> bool: ...

    def generate(self, *, system: str, user: str) -> GenerateResult: ...


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
        llm_backend: LLMBackend | None = None,
        config: RagAnswerConfig | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.search = search_backend or SearchService(db)
        self._llm_backend = llm_backend
        self.config = config or RagAnswerConfig()
        self.settings = settings or get_settings()

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
        issuing_agency: str | None = None,
        issued_date: date | None = None,
        doc_group: str | None = None,
        section_role: str | None = None,
        requires_review: bool | None = None,
        contract_number: str | None = None,
        supplier_name: str | None = None,
        contract_status: str | None = None,
        dispatch_type: str | None = None,
        dispatch_status: str | None = None,
        decision_kind: str | None = None,
        decision_status: str | None = None,
        effective_from: date | None = None,
        effective_to: date | None = None,
        procurement_kind: str | None = None,
        procurement_status: str | None = None,
        reference_number: str | None = None,
        requesting_unit: str | None = None,
        procurement_item_name: str | None = None,
        procurement_item_code: str | None = None,
    ) -> dict:
        results = self.search.semantic_search(
            query=query,
            limit=limit,
            document_type=document_type,
            department_id=department_id,
            business_type=business_type,
            document_number=document_number,
            issuing_agency=issuing_agency,
            issued_date=issued_date,
            doc_group=doc_group,
            section_role=section_role,
            requires_review=requires_review,
            contract_number=contract_number,
            supplier_name=supplier_name,
            contract_status=contract_status,
            dispatch_type=dispatch_type,
            dispatch_status=dispatch_status,
            decision_kind=decision_kind,
            decision_status=decision_status,
            effective_from=effective_from,
            effective_to=effective_to,
            procurement_kind=procurement_kind,
            procurement_status=procurement_status,
            reference_number=reference_number,
            requesting_unit=requesting_unit,
            procurement_item_name=procurement_item_name,
            procurement_item_code=procurement_item_code,
        )
        evidence = [
            result
            for result in results
            if float(result.get("score") or 0.0) >= min_score
            and self._has_query_overlap(query, str(result.get("text") or ""))
        ][:max_citations]

        if not self._has_enough_evidence(query, evidence):
            return self._insufficient_evidence_response(query)

        generative = self._try_generative_answer(query, evidence)
        if generative is not None:
            return generative

        return self._extractive_response(query, evidence)

    def _try_generative_answer(self, query: str, evidence: list[dict]) -> dict | None:
        llm = self._llm()
        if not llm.is_generative_enabled():
            return None

        if not llm.is_available():
            return self._extractive_response(query, evidence, fallback_reason="llm_unavailable")

        context_builder = RagContextBuilder(max_context_chars=self.settings.rag_llm_max_context_chars)
        context_text, ordered_evidence = context_builder.build(
            query,
            evidence,
            snippet_fn=self._quote,
        )
        user_prompt = (
            f"Câu hỏi: {query}\n\n"
            f"Các đoạn tham chiếu:\n{context_text}\n\n"
            "Trả lời câu hỏi và trích [n] cho mỗi ý dựa trên đoạn tương ứng."
        )

        try:
            generated = llm.generate(system=GENERATIVE_SYSTEM_PROMPT, user=user_prompt)
        except LocalLLMError as exc:
            logger.warning("Generative RAG failed, falling back to extractive: %s", exc)
            return self._extractive_response(query, evidence, fallback_reason="llm_unavailable")

        validator = CitationValidator()
        if validator.is_insufficient_claim(generated.text):
            return self._insufficient_evidence_response(query)

        validation = validator.validate(generated.text, len(ordered_evidence))
        if not validation.valid:
            logger.warning("Generative RAG citation validation failed")
            return self._extractive_response(query, evidence, fallback_reason="validation_failed")

        citations = self._citations_for_markers(query, ordered_evidence, validation.marker_indices)
        return {
            "query": query,
            "answer": generated.text,
            "grounded": True,
            "confidence": self._confidence(citations),
            "fallback_reason": None,
            "citations": citations,
            "generation_mode": "generative",
            "model_name": generated.model_name,
            "latency_ms": generated.latency_ms,
        }

    def _extractive_response(
        self,
        query: str,
        evidence: list[dict],
        *,
        fallback_reason: str | None = None,
    ) -> dict:
        citations = [self._citation(query, result) for result in evidence]
        return {
            "query": query,
            "answer": self._compose_answer(citations),
            "grounded": True,
            "confidence": self._confidence(citations),
            "fallback_reason": fallback_reason,
            "citations": citations,
            "generation_mode": "extractive",
            "model_name": None,
            "latency_ms": None,
        }

    def _insufficient_evidence_response(self, query: str) -> dict:
        return {
            "query": query,
            "answer": self.config.fallback_answer,
            "grounded": False,
            "confidence": 0.0,
            "fallback_reason": "insufficient_evidence",
            "citations": [],
            "generation_mode": "extractive",
            "model_name": None,
            "latency_ms": None,
        }

    def _citations_for_markers(
        self,
        query: str,
        evidence: list[dict],
        marker_indices: tuple[int, ...],
    ) -> list[dict]:
        citations: list[dict] = []
        for index in marker_indices:
            citations.append(self._citation(query, evidence[index - 1]))
        return citations

    def _llm(self) -> LLMBackend:
        if self._llm_backend is None:
            self._llm_backend = LocalLLMService(self.settings)
        return self._llm_backend

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
        top_citations = citations[:2]
        snippets = [citation["quote"].rstrip(".") for citation in top_citations if citation["quote"]]
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
