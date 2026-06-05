from pydantic import BaseModel


class WorkerQueueStatusRead(BaseModel):
    status: str
    pending_ready: int
    pending_delayed: int
    running: int
    failed: int
    completed: int
    active: int
