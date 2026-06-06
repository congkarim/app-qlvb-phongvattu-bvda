from pydantic import BaseModel


class WorkerQueueStatusRead(BaseModel):
    status: str
    pending_ready: int
    pending_delayed: int
    running: int
    failed: int
    completed: int
    active: int


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
