from qdrant_client import QdrantClient
from typing import Any

from qdrant_client.http.models import Distance, FieldCondition, Filter, MatchValue, PointIdsList, PointStruct, VectorParams

from app.core.config import get_settings


class QdrantCollectionConfigError(RuntimeError):
    pass


class QdrantService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = QdrantClient(url=self.settings.qdrant_url)

    def ensure_collection(self) -> None:
        collections = self.client.get_collections().collections
        if any(collection.name == self.settings.qdrant_collection for collection in collections):
            self._validate_collection_dimensions()
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

    def delete_points(self, point_ids: list[str]) -> None:
        if not point_ids:
            return
        self.ensure_collection()
        self.client.delete(
            collection_name=self.settings.qdrant_collection,
            points_selector=PointIdsList(points=point_ids),
        )

    def search(self, *, vector: list[float], limit: int, filters: dict[str, Any | None]) -> list:
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

    def _validate_collection_dimensions(self) -> None:
        collection = self.client.get_collection(self.settings.qdrant_collection)
        vectors_config = collection.config.params.vectors
        actual_size = getattr(vectors_config, "size", None)
        if isinstance(vectors_config, dict):
            actual_size = next(
                (getattr(vector_config, "size", None) for vector_config in vectors_config.values()),
                None,
            )
        if actual_size != self.settings.embedding_dimensions:
            raise QdrantCollectionConfigError(
                "Qdrant collection vector size mismatch: "
                f"collection={self.settings.qdrant_collection}, "
                f"actual={actual_size}, expected={self.settings.embedding_dimensions}. "
                "Use a versioned QDRANT_COLLECTION for each embedding model/dimension."
            )
