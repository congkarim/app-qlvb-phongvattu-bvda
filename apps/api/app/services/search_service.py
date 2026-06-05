import re
import unicodedata
from datetime import date

from sqlalchemy.orm import Session

from app.repositories.document_repository import DocumentRepository
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService


class SearchService:
    def __init__(self, db: Session | None = None) -> None:
        self.db = db
        self.embeddings = EmbeddingService()
        self.qdrant = QdrantService()

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
        vector = self.embeddings.embed(query)
        search_limit = min(max(limit * 8, limit + 20), 100)
        filters = {
            "document_type": document_type,
            "department_id": department_id,
            "business_type": business_type,
            "document_number": document_number,
            "issued_date": issued_date.isoformat() if issued_date else None,
            "doc_group": doc_group,
            "section_role": section_role,
            "requires_review": requires_review,
        }
        hits = self.qdrant.search(
            vector=vector,
            limit=search_limit,
            filters=filters,
        )
        allowed_chunk_ids = self._matching_chunk_ids(
            hits=hits,
            document_type=document_type,
            department_id=department_id,
            business_type=business_type,
            document_number=document_number,
            issued_date=issued_date,
            doc_group=doc_group,
            section_role=section_role,
            requires_review=requires_review,
        )
        candidates = []
        for hit in hits:
            payload = hit.payload or {}
            chunk_id = str(payload.get("chunk_id") or "")
            if allowed_chunk_ids is not None and chunk_id not in allowed_chunk_ids:
                continue
            text = payload.get("text", "")
            candidate = {
                "document_id": payload.get("document_id", ""),
                "chunk_id": chunk_id,
                "score": hit.score,
                "text": text,
                "title": payload.get("title"),
                "document_type": payload.get("document_type"),
                "document_number": payload.get("document_number"),
                "issued_date": payload.get("issued_date"),
                "business_type": payload.get("business_type"),
                "page_from": payload.get("page_from"),
                "page_to": payload.get("page_to"),
                "doc_group": payload.get("doc_group"),
                "section_role": payload.get("section_role"),
                "section_path": payload.get("section_path") or [],
                "requires_review": bool(payload.get("requires_review", False)),
                "_vector_score": float(hit.score),
                "_keyword_score": self._keyword_score(query, text, str(payload.get("title") or "")),
                "_dedup_key": self._dedup_key(payload),
            }
            candidate["_rerank_score"] = self._rerank_score(
                query,
                text,
                vector_score=candidate["_vector_score"],
                keyword_score=candidate["_keyword_score"],
            )
            candidates.append(candidate)

        candidates_by_chunk_id = {str(candidate["chunk_id"]): candidate for candidate in candidates}
        for candidate in self._keyword_candidates(
            query=query,
            limit=search_limit,
            document_type=document_type,
            department_id=department_id,
            business_type=business_type,
            document_number=document_number,
            issued_date=issued_date,
            doc_group=doc_group,
            section_role=section_role,
            requires_review=requires_review,
        ):
            existing = candidates_by_chunk_id.get(str(candidate["chunk_id"]))
            if existing:
                existing["_keyword_score"] = max(existing["_keyword_score"], candidate["_keyword_score"])
                existing["_rerank_score"] = self._rerank_score(
                    query,
                    str(existing.get("text") or ""),
                    vector_score=existing["_vector_score"],
                    keyword_score=existing["_keyword_score"],
                )
                continue
            candidates.append(candidate)
            candidates_by_chunk_id[str(candidate["chunk_id"])] = candidate

        ranked = sorted(candidates, key=lambda item: item["_rerank_score"], reverse=True)
        results = []
        seen_keys: set[str] = set()
        seen_documents: set[str] = set()
        seen_titles: set[str] = set()
        for item in ranked:
            dedup_key = str(item.pop("_dedup_key"))
            rank_score = float(item.pop("_rerank_score", item.get("score") or 0.0))
            item.pop("_vector_score", None)
            item.pop("_keyword_score", None)
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
                    "score": round(rank_score, 6),
                    "text": item["text"],
                    "title": item["title"],
                    "document_type": item["document_type"],
                    "document_number": item["document_number"],
                    "issued_date": item["issued_date"],
                    "business_type": item["business_type"],
                    "page_from": item["page_from"],
                    "page_to": item["page_to"],
                    "doc_group": item["doc_group"],
                    "section_role": item["section_role"],
                    "section_path": item["section_path"],
                    "requires_review": item["requires_review"],
                }
            )
            if len(results) >= limit:
                break
        return results

    def _keyword_candidates(
        self,
        *,
        query: str,
        limit: int,
        document_type: str | None,
        department_id: str | None,
        business_type: str | None,
        document_number: str | None,
        issued_date: date | None,
        doc_group: str | None,
        section_role: str | None,
        requires_review: bool | None,
    ) -> list[dict]:
        if self.db is None:
            return []

        chunks = DocumentRepository(self.db).search_chunks_by_keyword(
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
        candidates = []
        for chunk in chunks:
            document = chunk.document
            keyword_score = self._keyword_score(query, chunk.text, document.title)
            candidate = {
                "document_id": document.id,
                "chunk_id": chunk.id,
                "score": keyword_score,
                "text": chunk.text,
                "title": document.title,
                "document_type": document.document_type,
                "document_number": document.document_number,
                "issued_date": document.issued_date,
                "business_type": document.business_type,
                "page_from": chunk.page_from,
                "page_to": chunk.page_to,
                "doc_group": chunk.doc_group,
                "section_role": chunk.section_role,
                "section_path": chunk.section_path or [],
                "requires_review": chunk.requires_review,
                "_vector_score": 0.0,
                "_keyword_score": keyword_score,
                "_dedup_key": chunk.content_hash or self._dedup_key(
                    {
                        "title": document.title,
                        "page_from": chunk.page_from,
                        "page_to": chunk.page_to,
                        "text": chunk.text,
                    }
                ),
            }
            candidate["_rerank_score"] = self._rerank_score(
                query,
                chunk.text,
                vector_score=0.0,
                keyword_score=keyword_score,
            )
            candidates.append(candidate)
        return candidates

    def _matching_chunk_ids(
        self,
        *,
        hits: list,
        document_type: str | None,
        department_id: str | None,
        business_type: str | None,
        document_number: str | None,
        issued_date: date | None,
        doc_group: str | None,
        section_role: str | None,
        requires_review: bool | None,
    ) -> set[str] | None:
        if self.db is None:
            return None
        chunk_ids = [str((hit.payload or {}).get("chunk_id") or "") for hit in hits]
        chunk_ids = [chunk_id for chunk_id in chunk_ids if chunk_id]
        return DocumentRepository(self.db).list_matching_chunk_ids(
            chunk_ids=chunk_ids,
            document_type=document_type,
            department_id=department_id,
            business_type=business_type,
            document_number=document_number,
            issued_date=issued_date,
            doc_group=doc_group,
            section_role=section_role,
            requires_review=requires_review,
        )

    def _rerank_score(self, query: str, text: str, *, vector_score: float, keyword_score: float) -> float:
        query_norm = self._normalize(query)
        text_norm = self._normalize(text)
        score = float(vector_score) + keyword_score

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

    def _keyword_score(self, query: str, text: str, title: str = "") -> float:
        query_norm = self._normalize(query)
        text_norm = self._normalize(text)
        title_norm = self._normalize(title)
        query_terms = {term for term in re.findall(r"\w+", query_norm) if len(term) >= 3}
        if not query_terms:
            return 0.0

        matched_terms = sum(1 for term in query_terms if term in text_norm or term in title_norm)
        coverage = matched_terms / len(query_terms)
        score = 0.45 * coverage
        if query_norm and query_norm in text_norm:
            score += 0.75

        phrases = self._query_phrases(query_norm)
        for phrase in phrases:
            if phrase in text_norm:
                score += 0.2
        return score

    def _query_phrases(self, query_norm: str) -> list[str]:
        phrase_candidates = [
            "pham vi dieu chinh",
            "nguoi lien he",
            "so hieu",
            "kinh gui",
            "che do phu cap",
            "ho tro hang thang",
            "nhan vien y te thon",
            "co do thon ban",
        ]
        return [phrase for phrase in phrase_candidates if phrase in query_norm]

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
