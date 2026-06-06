from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.dispatch import DispatchCreateRequest, DispatchListResponse, DispatchRead, DispatchUpdateRequest
from app.services.dispatch_service import (
    DispatchAlreadyExistsError,
    DispatchNotFoundError,
    DispatchOperationError,
    DispatchService,
)


router = APIRouter(prefix="/dispatches", tags=["dispatches"])


@router.get("", response_model=DispatchListResponse, dependencies=[Depends(get_current_user)])
def list_dispatches(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, max_length=200),
    document_id: str | None = Query(default=None),
    dispatch_type: str | None = Query(default=None, pattern="^(incoming|outgoing)$"),
    document_number: str | None = Query(default=None, max_length=128),
    issuing_agency: str | None = Query(default=None, max_length=255),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        pattern="^(draft|registered|processing|completed|archived)$",
    ),
    issued_date_from: date | None = Query(default=None),
    issued_date_to: date | None = Query(default=None),
    sort_by: str = Query(
        default="created_at",
        pattern="^(created_at|updated_at|document_number|dispatch_type|issuing_agency|status|issued_date)$",
    ),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> DispatchListResponse:
    try:
        items, total = DispatchService(db).list_dispatches(
            limit=limit,
            offset=offset,
            query=q,
            document_id=document_id,
            dispatch_type=dispatch_type,
            document_number=document_number,
            issuing_agency=issuing_agency,
            status=status_filter,
            issued_date_from=issued_date_from,
            issued_date_to=issued_date_to,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
    except DispatchOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return DispatchListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/by-document/{document_id}", response_model=DispatchRead)
def get_dispatch_by_document(
    document_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> DispatchRead:
    try:
        return DispatchRead(**DispatchService(db).get_dispatch_by_document_id(document_id))
    except DispatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{dispatch_id}", response_model=DispatchRead)
def get_dispatch(
    dispatch_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> DispatchRead:
    try:
        return DispatchRead(**DispatchService(db).get_dispatch(dispatch_id))
    except DispatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("", response_model=DispatchRead, status_code=status.HTTP_201_CREATED)
def create_dispatch(
    payload: DispatchCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DispatchRead:
    try:
        return DispatchRead(**DispatchService(db).create_dispatch(values=payload.model_dump(), actor=current_user))
    except DispatchAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except DispatchOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.patch("/{dispatch_id}", response_model=DispatchRead)
def update_dispatch(
    dispatch_id: str,
    payload: DispatchUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DispatchRead:
    try:
        return DispatchRead(
            **DispatchService(db).update_dispatch(
                dispatch_id=dispatch_id,
                values=payload.model_dump(exclude_unset=True),
                actor=current_user,
            )
        )
    except DispatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except DispatchOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.delete("/{dispatch_id}", response_model=DispatchRead)
def delete_dispatch(
    dispatch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> DispatchRead:
    try:
        return DispatchRead(**DispatchService(db).delete_dispatch(dispatch_id=dispatch_id, actor=current_user))
    except DispatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
