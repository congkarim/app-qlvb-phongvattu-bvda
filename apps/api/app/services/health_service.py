import os
from pathlib import Path

import redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.health import HealthComponentRead, HealthLivenessRead, HealthReadinessRead
from app.services.qdrant_service import QdrantService


class HealthService:
    def get_liveness(self) -> HealthLivenessRead:
        return HealthLivenessRead(status="ok")

    def get_readiness(self, db: Session) -> HealthReadinessRead:
        settings = get_settings()
        components = {
            "postgres": self._check_postgres(db),
            "redis": self._check_redis(settings.redis_url),
            "qdrant": self._check_qdrant(),
            "uploads": self._check_uploads(settings.upload_dir),
        }
        status = "ok" if all(component.status == "ok" for component in components.values()) else "degraded"
        return HealthReadinessRead(status=status, components=components)

    def _check_postgres(self, db: Session) -> HealthComponentRead:
        try:
            db.execute(text("SELECT 1"))
            return HealthComponentRead(status="ok")
        except Exception as exc:
            return HealthComponentRead(status="down", error=f"PostgreSQL unavailable: {exc}")

    def _check_redis(self, redis_url: str) -> HealthComponentRead:
        try:
            client = redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
            client.ping()
            return HealthComponentRead(status="ok")
        except Exception as exc:
            return HealthComponentRead(status="down", error=f"Redis unavailable: {exc}")

    def _check_qdrant(self) -> HealthComponentRead:
        try:
            QdrantService().client.get_collections()
            return HealthComponentRead(status="ok")
        except Exception as exc:
            return HealthComponentRead(status="down", error=f"Qdrant unavailable: {exc}")

    def _check_uploads(self, upload_dir: Path) -> HealthComponentRead:
        try:
            upload_dir.mkdir(parents=True, exist_ok=True)
            if not upload_dir.is_dir():
                return HealthComponentRead(status="down", error="Upload directory is not a directory")
            if not os.access(upload_dir, os.W_OK):
                return HealthComponentRead(status="down", error="Upload directory is not writable")
            return HealthComponentRead(status="ok")
        except Exception as exc:
            return HealthComponentRead(status="down", error=f"Upload directory unavailable: {exc}")
