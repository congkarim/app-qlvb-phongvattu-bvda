from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_admin
from app.schemas.ops import WorkerQueueStatusRead
from app.services.ops_service import OpsService


router = APIRouter(prefix="/ops", tags=["ops"], dependencies=[Depends(require_admin)])


@router.get("/worker-queue", response_model=WorkerQueueStatusRead)
def get_worker_queue_status(db: Session = Depends(get_db)) -> WorkerQueueStatusRead:
    return OpsService(db).get_worker_queue_status()
