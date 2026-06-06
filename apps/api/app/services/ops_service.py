from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories.document_repository import DocumentRepository, OCRJobRepository
from app.schemas.ops import (
    StaleJobRecoveryRead,
    StaleOCRJobListRead,
    StaleOCRJobRead,
    StatusDetailRead,
    SystemStatusRead,
    WorkerQueueStatusRead,
)
from app.services.ocr_job_recovery_service import OCRJobRecoveryService
from app.services.qdrant_service import QdrantCollectionConfigError, QdrantService


class OpsService:
    def __init__(self, db: Session):
        self.db = db
        self.documents = DocumentRepository(db)
        self.ocr_jobs = OCRJobRepository(db)
        self.settings = get_settings()

    def get_worker_queue_status(self) -> WorkerQueueStatusRead:
        now = datetime.now(timezone.utc)
        lease_timeout_seconds = max(1, int(self.settings.ocr_job_lease_timeout_seconds))
        stale_before = now - timedelta(seconds=lease_timeout_seconds)
        pending_ready = self.ocr_jobs.count_pending_jobs_ready()
        pending_delayed = self.ocr_jobs.count_pending_jobs_delayed()
        running = self.ocr_jobs.count_jobs_by_status("ocr_running")
        stale_running = self.ocr_jobs.count_stale_running_jobs(stale_before=stale_before)
        failed = self.ocr_jobs.count_jobs_by_status("failed")
        completed = self.ocr_jobs.count_jobs_by_status("completed")
        active = pending_ready + pending_delayed + running
        return WorkerQueueStatusRead(
            status="ok",
            pending_ready=pending_ready,
            pending_delayed=pending_delayed,
            running=running,
            stale_running=stale_running,
            failed=failed,
            completed=completed,
            active=active,
            lease_timeout_seconds=lease_timeout_seconds,
            stale_recovery_enabled=self.settings.ocr_job_stale_recovery_enabled,
        )

    def list_stale_jobs(self, *, limit: int = 50, offset: int = 0) -> StaleOCRJobListRead:
        now = datetime.now(timezone.utc)
        lease_timeout_seconds = max(1, int(self.settings.ocr_job_lease_timeout_seconds))
        stale_before = now - timedelta(seconds=lease_timeout_seconds)
        total = self.ocr_jobs.count_stale_running_jobs(stale_before=stale_before)
        jobs = self.ocr_jobs.list_stale_running_jobs(
            stale_before=stale_before,
            limit=limit,
            offset=offset,
        )
        items: list[StaleOCRJobRead] = []
        for job in jobs:
            document = self.documents.get_document(job.document_id)
            started_at = job.started_at or now
            stale_for_seconds = max(0, int((now - started_at).total_seconds()) - lease_timeout_seconds)
            items.append(
                StaleOCRJobRead(
                    job_id=job.id,
                    document_id=job.document_id,
                    document_title=document.title if document is not None else None,
                    document_status=document.status if document is not None else None,
                    job_type=job.job_type,
                    status=job.status,
                    attempts=job.attempts,
                    max_attempts=job.max_attempts,
                    started_at=started_at,
                    lease_timeout_seconds=lease_timeout_seconds,
                    stale_for_seconds=stale_for_seconds,
                    failed_reason=job.failed_reason,
                    error_message=job.error_message,
                )
            )
        return StaleOCRJobListRead(
            status="ok",
            total=total,
            limit=limit,
            offset=offset,
            lease_timeout_seconds=lease_timeout_seconds,
            stale_recovery_enabled=self.settings.ocr_job_stale_recovery_enabled,
            items=items,
        )

    def recover_all_stale_jobs(self, *, actor_user_id: str) -> StaleJobRecoveryRead:
        if not self.settings.ocr_job_stale_recovery_enabled:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Stale OCR job recovery is disabled",
            )

        recovered_job_ids = OCRJobRecoveryService(self.db).recover_stale_jobs(actor_user_id=actor_user_id)
        self.db.commit()
        return StaleJobRecoveryRead(
            status="ok",
            recovered_count=len(recovered_job_ids),
            recovered_job_ids=recovered_job_ids,
        )

    def recover_stale_job_by_id(self, *, job_id: str, actor_user_id: str) -> StaleJobRecoveryRead:
        if not self.settings.ocr_job_stale_recovery_enabled:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Stale OCR job recovery is disabled",
            )

        recovered_job_id = OCRJobRecoveryService(self.db).recover_stale_job_by_id(
            job_id,
            actor_user_id=actor_user_id,
        )
        if recovered_job_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stale OCR job not found")

        self.db.commit()
        return StaleJobRecoveryRead(
            status="ok",
            recovered_count=1,
            recovered_job_ids=[recovered_job_id],
        )

    def get_system_status(self) -> SystemStatusRead:
        worker_queue = self.get_worker_queue_status()
        components = [
            self._get_ocr_status(),
            self._get_embedding_status(),
            self._get_qdrant_status(),
        ]
        status_value = "ok" if all(component.status == "ok" for component in components) else "degraded"
        return SystemStatusRead(
            status=status_value,
            ocr=components[0],
            embedding=components[1],
            qdrant=components[2],
            worker_queue=worker_queue,
        )

    def _get_ocr_status(self) -> StatusDetailRead:
        supported_engines = {"paddleocr", "paddle_vietocr"}
        status_value = "ok" if self.settings.ocr_engine in supported_engines else "degraded"
        error = None if status_value == "ok" else f"Unsupported OCR engine: {self.settings.ocr_engine}"
        return StatusDetailRead(
            status=status_value,
            name=self.settings.ocr_engine,
            details={
                "engine": self.settings.ocr_engine,
                "lang": self.settings.ocr_lang,
                "device": self.settings.ocr_device,
                "use_gpu": self.settings.ocr_use_gpu,
                "preprocess_mode": self.settings.ocr_preprocess_mode,
                "model_dir": str(self.settings.ocr_model_dir),
                "model_dir_exists": self.settings.ocr_model_dir.exists(),
                "vietocr_model_dir": str(self.settings.vietocr_model_dir),
                "vietocr_model_dir_exists": self.settings.vietocr_model_dir.exists(),
                "fallback_engine": self.settings.ocr_fallback_engine,
            },
            error=error,
        )

    def _get_embedding_status(self) -> StatusDetailRead:
        supported_backends = {"fake", "sentence_transformers"}
        status_value = "ok" if self.settings.embedding_backend in supported_backends else "degraded"
        error = None if status_value == "ok" else f"Unsupported embedding backend: {self.settings.embedding_backend}"
        model_path = self.settings.embedding_model_path
        return StatusDetailRead(
            status=status_value,
            name=self.settings.embedding_backend,
            details={
                "backend": self.settings.embedding_backend,
                "model_name": self.settings.embedding_model_name,
                "model_path": str(model_path) if model_path else None,
                "model_path_exists": model_path.exists() if model_path else None,
                "device": self.settings.embedding_device,
                "dimensions": self.settings.embedding_dimensions,
                "batch_size": self.settings.embedding_batch_size,
                "local_files_only": self.settings.embedding_local_files_only,
                "allow_fake_embeddings": self.settings.allow_fake_embeddings,
            },
            error=error,
        )

    def _get_qdrant_status(self) -> StatusDetailRead:
        qdrant = QdrantService()
        details: dict[str, str | int | bool | float | None] = {
            "url": self.settings.qdrant_url,
            "collection": self.settings.qdrant_collection,
            "expected_dimensions": self.settings.embedding_dimensions,
            "collection_exists": False,
        }
        try:
            collections = qdrant.client.get_collections().collections
            collection_exists = any(collection.name == self.settings.qdrant_collection for collection in collections)
            details["collection_exists"] = collection_exists
            if collection_exists:
                qdrant._validate_collection_dimensions()
                collection = qdrant.client.get_collection(self.settings.qdrant_collection)
                details["points_count"] = collection.points_count
                details["vectors_count"] = collection.vectors_count
                details["status"] = str(collection.status)
            return StatusDetailRead(
                status="ok" if collection_exists else "degraded",
                name=self.settings.qdrant_collection,
                details=details,
                error=None if collection_exists else "Qdrant collection has not been created yet",
            )
        except QdrantCollectionConfigError as exc:
            return StatusDetailRead(
                status="degraded",
                name=self.settings.qdrant_collection,
                details=details,
                error=str(exc),
            )
        except Exception as exc:
            return StatusDetailRead(
                status="degraded",
                name=self.settings.qdrant_collection,
                details=details,
                error=f"Qdrant unavailable: {exc}",
            )
