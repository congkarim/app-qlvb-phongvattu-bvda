from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Legal Document AI API"
    app_env: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://legal:legal@postgres:5432/legal_doc_ai"
    redis_url: str = "redis://redis:6379/0"
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "document_chunks"
    upload_dir: Path = Path("/data/uploads")
    upload_max_file_size_bytes: int = 52_428_800
    upload_max_files_per_request: int = 20
    upload_max_zip_size_bytes: int = 209_715_200
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
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
    chunking_backend: str = "ocr_chunking"
    ocr_engine: str = "paddle_vietocr"
    ocr_lang: str = "vi"
    ocr_use_gpu: bool = False
    ocr_device: str = "cpu"
    ocr_model_dir: Path = Path("/models/ocr")
    ocr_preprocess_mode: str = "auto"
    ocr_min_confidence: float = 0.0
    ocr_restore_vietnamese_terms: bool = True
    ocr_fallback_engine: str | None = None
    vietocr_model_dir: Path = Path("/models/ocr/vietocr")
    vietocr_device: str = "cpu"
    vietocr_config: str = "vgg_transformer"
    vietocr_weight_path: Path | None = None
    vietocr_max_batch_size: int = 1
    vietocr_beamsearch: bool = False
    ocr_job_lease_timeout_seconds: int = 3600
    ocr_job_stale_recovery_enabled: bool = True
    rag_generation_backend: str = "extractive"
    ollama_base_url: str = "http://ollama:11434"
    rag_llm_model: str = "qwen2.5:3b-instruct"
    rag_llm_timeout_seconds: int = 120
    rag_llm_max_context_chars: int = 8000
    rag_llm_max_output_tokens: int = 512
    rag_llm_temperature: float = 0.1

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() in {"prod", "production"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    @property
    def cors_origin_regex(self) -> str | None:
        if self.is_production:
            return None
        # Docker dev: browser may use LAN IP or 0.0.0.0 instead of localhost.
        return (
            r"https?://"
            r"(localhost|127\.0\.0\.1|0\.0\.0\.0|"
            r"192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+)"
            r"(:\d+)?"
        )

    @model_validator(mode="after")
    def validate_rag_generation_backend(self) -> "Settings":
        backend = self.rag_generation_backend.strip().lower()
        if backend not in {"extractive", "ollama"}:
            raise ValueError(
                "RAG_GENERATION_BACKEND must be 'extractive' or 'ollama', "
                f"got {self.rag_generation_backend!r}"
            )
        self.rag_generation_backend = backend
        if self.rag_llm_timeout_seconds < 1:
            raise ValueError("RAG_LLM_TIMEOUT_SECONDS must be >= 1")
        if self.rag_llm_max_context_chars < 512:
            raise ValueError("RAG_LLM_MAX_CONTEXT_CHARS must be >= 512")
        if self.rag_llm_max_output_tokens < 32:
            raise ValueError("RAG_LLM_MAX_OUTPUT_TOKENS must be >= 32")
        if not 0.0 <= self.rag_llm_temperature <= 2.0:
            raise ValueError("RAG_LLM_TEMPERATURE must be between 0.0 and 2.0")
        return self

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if not self.is_production:
            return self

        default_jwt_secrets = {"change-me-in-production", "local-dev-secret"}
        if self.jwt_secret_key in default_jwt_secrets or len(self.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must be changed to a strong value when APP_ENV=production")

        if self.admin_password == "admin123" or len(self.admin_password) < 12:
            raise ValueError("ADMIN_PASSWORD must be changed to a strong value when APP_ENV=production")

        if not self.cors_origins_list or "*" in self.cors_origins_list:
            raise ValueError("CORS_ALLOWED_ORIGINS must list explicit origins when APP_ENV=production")

        if "legal:legal@" in self.database_url:
            raise ValueError("DATABASE_URL must not use the default legal:legal credential when APP_ENV=production")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
