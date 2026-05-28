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
        hits = self.qdrant.search(
            vector=vector,
            limit=limit,
            filters={"document_type": document_type, "department_id": department_id, "deleted_at": None},
        )
        results = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(
                {
                    "document_id": payload.get("document_id", ""),
                    "chunk_id": payload.get("chunk_id", ""),
                    "score": hit.score,
                    "text": payload.get("text", ""),
                    "title": payload.get("title"),
                    "page_from": payload.get("page_from"),
                    "page_to": payload.get("page_to"),
                }
            )
        return results
