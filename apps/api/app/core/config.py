from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Legal Document AI API"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://legal:legal@postgres:5432/legal_doc_ai"
    redis_url: str = "redis://redis:6379/0"
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "document_chunks"
    upload_dir: Path = Path("/data/uploads")
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    admin_email: str = "admin@example.com"
    admin_password: str = "admin123"
    admin_full_name: str = "System Admin"
    embedding_backend: str = "fake"
    embedding_model_name: str = "bkai-foundation-models/vietnamese-bi-encoder"
    embedding_model_path: Path | None = None
    embedding_device: str = "cpu"
    embedding_dimensions: int = 384
    embedding_batch_size: int = 16
    embedding_local_files_only: bool = True
    allow_fake_embeddings: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
