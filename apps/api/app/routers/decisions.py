from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.decision import DecisionCreateRequest, DecisionListResponse, DecisionRead, DecisionUpdateRequest
from app.services.decision_service import (
    DecisionAlreadyExistsError,
    DecisionNotFoundError,
    DecisionOperationError,
    DecisionService,
)


router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.get("", response_model=DecisionListResponse, dependencies=[Depends(get_current_user)])
def list_decisions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, max_length=200),
    document_id: str | None = Query(default=None),
    decision_kind: str | None = Query(default=None, pattern="^(decision|notification)$"),
    document_number: str | None = Query(default=None, max_length=128),
    issuing_agency: str | None = Query(default=None, max_length=255),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        pattern="^(draft|registered|effective|expired|revoked|archived)$",
    ),
    issued_date_from: date | None = Query(default=None),
    issued_date_to: date | None = Query(default=None),
    effective_from: date | None = Query(default=None),
    effective_to: date | None = Query(default=None),
    sort_by: str = Query(
        default="created_at",
        pattern="^(created_at|updated_at|document_number|decision_kind|issuing_agency|status|issued_date|effective_from|effective_to)$",
    ),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> DecisionListResponse:
    try:
        items, total = DecisionService(db).list_decisions(
            limit=limit,
            offset=offset,
            query=q,
            document_id=document_id,
            decision_kind=decision_kind,
            document_number=document_number,
            issuing_agency=issuing_agency,
            status=status_filter,
            issued_date_from=issued_date_from,
            issued_date_to=issued_date_to,
            effective_from=effective_from,
            effective_to=effective_to,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
    except DecisionOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return DecisionListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/by-document/{document_id}", response_model=DecisionRead)
def get_decision_by_document(
    document_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> DecisionRead:
    try:
        return DecisionRead(**DecisionService(db).get_decision_by_document_id(document_id))
    except DecisionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{decision_id}", response_model=DecisionRead)
def get_decision(
    decision_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> DecisionRead:
    try:
        return DecisionRead(**DecisionService(db).get_decision(decision_id))
    except DecisionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("", response_model=DecisionRead, status_code=status.HTTP_201_CREATED)
def create_decision(
    payload: DecisionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DecisionRead:
    try:
        return DecisionRead(**DecisionService(db).create_decision(values=payload.model_dump(), actor=current_user))
    except DecisionAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except DecisionOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.patch("/{decision_id}", response_model=DecisionRead)
def update_decision(
    decision_id: str,
    payload: DecisionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DecisionRead:
    try:
        return DecisionRead(
            **DecisionService(db).update_decision(
                decision_id=decision_id,
                values=payload.model_dump(exclude_unset=True),
                actor=current_user,
            )
        )
    except DecisionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except DecisionOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.delete("/{decision_id}", response_model=DecisionRead)
def delete_decision(
    decision_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> DecisionRead:
    try:
        return DecisionRead(**DecisionService(db).delete_decision(decision_id=decision_id, actor=current_user))
    except DecisionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
