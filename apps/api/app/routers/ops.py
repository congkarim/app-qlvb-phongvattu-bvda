from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.schemas.ops import (
    StaleJobRecoveryRead,
    StaleOCRJobListRead,
    SystemStatusRead,
    WorkerQueueStatusRead,
)
from app.services.ops_service import OpsService


router = APIRouter(prefix="/ops", tags=["ops"], dependencies=[Depends(require_admin)])


@router.get("/worker-queue", response_model=WorkerQueueStatusRead)
def get_worker_queue_status(db: Session = Depends(get_db)) -> WorkerQueueStatusRead:
    return OpsService(db).get_worker_queue_status()


@router.get("/worker-queue/stale-jobs", response_model=StaleOCRJobListRead)
def list_stale_worker_jobs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> StaleOCRJobListRead:
    return OpsService(db).list_stale_jobs(limit=limit, offset=offset)


@router.post("/worker-queue/recover-stale", response_model=StaleJobRecoveryRead)
def recover_stale_worker_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> StaleJobRecoveryRead:
    return OpsService(db).recover_all_stale_jobs(actor_user_id=current_user.id)


@router.post("/worker-queue/stale-jobs/{job_id}/recover", response_model=StaleJobRecoveryRead)
def recover_stale_worker_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> StaleJobRecoveryRead:
    return OpsService(db).recover_stale_job_by_id(job_id=job_id, actor_user_id=current_user.id)


@router.get("/system-status", response_model=SystemStatusRead)
def get_system_status(db: Session = Depends(get_db)) -> SystemStatusRead:
    return OpsService(db).get_system_status()
