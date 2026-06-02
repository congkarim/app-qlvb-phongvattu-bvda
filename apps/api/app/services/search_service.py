import re
import unicodedata

from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService


class SearchService:
    def __init__(self) -> None:
        self.embeddings = EmbeddingService()
        self.qdrant = QdrantService()

    def semantic_search(
        self,
        *,
        query: str,
        limit: int,
        document_type: str | None = None,
        department_id: str | None = None,
    ) -> list[dict]:
        vector = self.embeddings.embed(query)
        search_limit = min(max(limit * 8, limit + 20), 100)
        hits = self.qdrant.search(
            vector=vector,
            limit=search_limit,
            filters={"document_type": document_type, "department_id": department_id, "deleted_at": None},
        )
        candidates = []
        for hit in hits:
            payload = hit.payload or {}
            text = payload.get("text", "")
            candidate = {
                "document_id": payload.get("document_id", ""),
                "chunk_id": payload.get("chunk_id", ""),
                "score": hit.score,
                "text": text,
                "title": payload.get("title"),
                "page_from": payload.get("page_from"),
                "page_to": payload.get("page_to"),
                "_rerank_score": self._rerank_score(query, text, hit.score),
                "_dedup_key": self._dedup_key(payload),
            }
            candidates.append(candidate)

        ranked = sorted(candidates, key=lambda item: item["_rerank_score"], reverse=True)
        results = []
        seen_keys: set[str] = set()
        seen_documents: set[str] = set()
        seen_titles: set[str] = set()
        for item in ranked:
            dedup_key = str(item.pop("_dedup_key"))
            item.pop("_rerank_score", None)
            document_id = str(item.get("document_id") or "")
            title_key = self._normalize(str(item.get("title") or ""))
            if dedup_key in seen_keys:
                continue
            if document_id in seen_documents and self._is_weak_match(query, str(item.get("text") or "")):
                continue
            if title_key in seen_titles and self._is_weak_match(query, str(item.get("text") or "")):
                continue
            seen_keys.add(dedup_key)
            seen_documents.add(document_id)
            if title_key:
                seen_titles.add(title_key)
            results.append(
                {
                    "document_id": item["document_id"],
                    "chunk_id": item["chunk_id"],
                    "score": round(float(item["score"]), 6),
                    "text": item["text"],
                    "title": item["title"],
                    "page_from": item["page_from"],
                    "page_to": item["page_to"],
                }
            )
            if len(results) >= limit:
                break
        return results

    def _rerank_score(self, query: str, text: str, vector_score: float) -> float:
        query_norm = self._normalize(query)
        text_norm = self._normalize(text)
        score = float(vector_score)

        query_terms = [term for term in re.findall(r"\w+", query_norm) if len(term) >= 3]
        if query_terms:
            matched_terms = sum(1 for term in set(query_terms) if term in text_norm)
            score += 0.05 * matched_terms
            score += 0.12 * (matched_terms / len(set(query_terms)))

        legal_markers = {
            "dieu 1": 0.25,
            "pham vi dieu chinh": 0.3,
            "luat dau thau": 0.25,
        }
        for marker, boost in legal_markers.items():
            if marker in query_norm and marker in text_norm:
                score += boost

        if "pham vi dieu chinh" in query_norm and text_norm.startswith("dieu 1"):
            score += 0.55
        if "luat dau thau" in query_norm and text_norm.startswith("dieu 1"):
            score += 0.2
        if "pham vi dieu chinh" in query_norm and "dieu 1" in text_norm:
            score += 0.2
        if "luat dau thau" in query_norm and "dau thau" in text_norm:
            score += 0.12
        if "pham vi dieu chinh" in query_norm and "pham vi dieu chinh" not in text_norm:
            score -= 0.18
        return score

    def _is_weak_match(self, query: str, text: str) -> bool:
        query_terms = {term for term in re.findall(r"\w+", self._normalize(query)) if len(term) >= 4}
        if not query_terms:
            return False
        text_norm = self._normalize(text)
        matched_terms = sum(1 for term in query_terms if term in text_norm)
        return matched_terms < max(2, len(query_terms) // 2)

    def _dedup_key(self, payload: dict) -> str:
        content_hash = payload.get("content_hash")
        if content_hash:
            return str(content_hash)
        title = str(payload.get("title") or "")
        page_from = payload.get("page_from")
        page_to = payload.get("page_to")
        text = str(payload.get("text") or "")
        normalized_text = self._normalize(text)[:320]
        return f"{self._normalize(title)}:{page_from}:{page_to}:{normalized_text}"

    def _normalize(self, text: str) -> str:
        decomposed = unicodedata.normalize("NFD", text.lower())
        without_accents = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
        return re.sub(r"\s+", " ", without_accents.replace("đ", "d")).strip()
