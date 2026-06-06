from datetime import datetime

from pydantic import BaseModel


class WorkerQueueStatusRead(BaseModel):
    status: str
    pending_ready: int
    pending_delayed: int
    running: int
    stale_running: int
    failed: int
    completed: int
    active: int
    lease_timeout_seconds: int
    stale_recovery_enabled: bool


class StaleOCRJobRead(BaseModel):
    job_id: str
    document_id: str
    document_title: str | None
    document_status: str | None
    job_type: str
    status: str
    attempts: int
    max_attempts: int
    started_at: datetime
    lease_timeout_seconds: int
    stale_for_seconds: int
    failed_reason: str | None = None
    error_message: str | None = None


class StaleOCRJobListRead(BaseModel):
    status: str
    total: int
    limit: int
    offset: int
    lease_timeout_seconds: int
    stale_recovery_enabled: bool
    items: list[StaleOCRJobRead]


class StaleJobRecoveryRead(BaseModel):
    status: str
    recovered_count: int
    recovered_job_ids: list[str]


class StatusDetailRead(BaseModel):
    status: str
    name: str
    details: dict[str, str | int | bool | float | None]
    error: str | None = None


class SystemStatusRead(BaseModel):
    status: str
    ocr: StatusDetailRead
    embedding: StatusDetailRead
    qdrant: StatusDetailRead
    worker_queue: WorkerQueueStatusRead
