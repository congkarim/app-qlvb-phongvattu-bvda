from sqlalchemy.orm import Session

from app.repositories.document_repository import OCRJobRepository
from app.schemas.ops import WorkerQueueStatusRead


class OpsService:
    def __init__(self, db: Session):
        self.ocr_jobs = OCRJobRepository(db)

    def get_worker_queue_status(self) -> WorkerQueueStatusRead:
        pending_ready = self.ocr_jobs.count_pending_jobs_ready()
        pending_delayed = self.ocr_jobs.count_pending_jobs_delayed()
        running = self.ocr_jobs.count_jobs_by_status("ocr_running")
        failed = self.ocr_jobs.count_jobs_by_status("failed")
        completed = self.ocr_jobs.count_jobs_by_status("completed")
        active = pending_ready + pending_delayed + running
        return WorkerQueueStatusRead(
            status="ok",
            pending_ready=pending_ready,
            pending_delayed=pending_delayed,
            running=running,
            failed=failed,
            completed=completed,
            active=active,
        )
