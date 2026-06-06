from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.health import HealthLivenessRead, HealthReadinessRead
from app.services.health_service import HealthService


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthLivenessRead)
def health_check() -> HealthLivenessRead:
    return HealthService().get_liveness()


@router.get("/health/live", response_model=HealthLivenessRead)
def health_live() -> HealthLivenessRead:
    return HealthService().get_liveness()


@router.get("/health/ready", response_model=HealthReadinessRead)
def health_ready(response: Response, db: Session = Depends(get_db)) -> HealthReadinessRead:
    readiness = HealthService().get_readiness(db)
    if readiness.status != "ok":
        response.status_code = 503
    return readiness
