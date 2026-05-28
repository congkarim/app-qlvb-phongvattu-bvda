from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

from app.core.config import get_settings


class QdrantService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = QdrantClient(url=self.settings.qdrant_url)

    def ensure_collection(self) -> None:
        collections = self.client.get_collections().collections
        if any(collection.name == self.settings.qdrant_collection for collection in collections):
            return
        self.client.create_collection(
            collection_name=self.settings.qdrant_collection,
            vectors_config=VectorParams(size=self.settings.embedding_dimensions, distance=Distance.COSINE),
        )

    def upsert_chunk(self, *, point_id: str, vector: list[float], payload: dict) -> None:
        self.ensure_collection()
        self.client.upsert(
            collection_name=self.settings.qdrant_collection,
            points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        )

    def search(self, *, vector: list[float], limit: int, filters: dict[str, str | None]) -> list:
        self.ensure_collection()
        conditions = [
            FieldCondition(key=key, match=MatchValue(value=value))
            for key, value in filters.items()
            if value is not None
        ]
        query_filter = Filter(must=conditions) if conditions else None
        return self.client.search(
            collection_name=self.settings.qdrant_collection,
            query_vector=vector,
            query_filter=query_filter,
            limit=limit,
        )
