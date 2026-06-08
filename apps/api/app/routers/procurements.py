from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.procurement import (
    ProcurementCreateRequest,
    ProcurementListResponse,
    ProcurementRead,
    ProcurementUpdateRequest,
)
from app.schemas.procurement_line_item import (
    ProcurementLineItemCreateRequest,
    ProcurementLineItemListResponse,
    ProcurementLineItemRead,
)
from app.services.materials_catalog_service import MaterialsCatalogNotFoundError
from app.services.procurement_line_item_service import (
    ProcurementLineItemAlreadyExistsError,
    ProcurementLineItemOperationError,
    ProcurementLineItemService,
)
from app.services.procurement_service import (
    ProcurementAlreadyExistsError,
    ProcurementNotFoundError,
    ProcurementOperationError,
    ProcurementService,
)


router = APIRouter(prefix="/procurements", tags=["procurements"])


@router.get("", response_model=ProcurementListResponse, dependencies=[Depends(get_current_user)])
def list_procurements(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, max_length=200),
    document_id: str | None = Query(default=None),
    procurement_kind: str | None = Query(default=None, pattern="^(proposal|plan|acceptance)$"),
    reference_number: str | None = Query(default=None, max_length=128),
    requesting_unit: str | None = Query(default=None, max_length=255),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        pattern="^(draft|submitted|approved|rejected|completed|archived)$",
    ),
    requested_date_from: date | None = Query(default=None),
    requested_date_to: date | None = Query(default=None),
    sort_by: str = Query(
        default="created_at",
        pattern="^(created_at|updated_at|reference_number|procurement_kind|requesting_unit|status|requested_date|estimated_value)$",
    ),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> ProcurementListResponse:
    try:
        items, total = ProcurementService(db).list_procurements(
            limit=limit,
            offset=offset,
            query=q,
            document_id=document_id,
            procurement_kind=procurement_kind,
            reference_number=reference_number,
            requesting_unit=requesting_unit,
            status=status_filter,
            requested_date_from=requested_date_from,
            requested_date_to=requested_date_to,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
    except ProcurementOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return ProcurementListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/by-document/{document_id}", response_model=ProcurementRead)
def get_procurement_by_document(
    document_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ProcurementRead:
    try:
        return ProcurementRead(**ProcurementService(db).get_procurement_by_document_id(document_id))
    except ProcurementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{procurement_id}/line-items", response_model=ProcurementLineItemListResponse)
def list_procurement_line_items(
    procurement_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ProcurementLineItemListResponse:
    try:
        return ProcurementLineItemListResponse(
            **ProcurementLineItemService(db).list_line_items(procurement_id)
        )
    except ProcurementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{procurement_id}/line-items", response_model=ProcurementLineItemRead, status_code=status.HTTP_201_CREATED)
def create_procurement_line_item(
    procurement_id: str,
    payload: ProcurementLineItemCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcurementLineItemRead:
    try:
        return ProcurementLineItemRead(
            **ProcurementLineItemService(db).create_line_item(
                procurement_id=procurement_id,
                values=payload.model_dump(),
                actor=current_user,
            )
        )
    except ProcurementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProcurementLineItemAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ProcurementLineItemOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except MaterialsCatalogNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{procurement_id}", response_model=ProcurementRead)
def get_procurement(
    procurement_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ProcurementRead:
    try:
        return ProcurementRead(**ProcurementService(db).get_procurement(procurement_id))
    except ProcurementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("", response_model=ProcurementRead, status_code=status.HTTP_201_CREATED)
def create_procurement(
    payload: ProcurementCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcurementRead:
    try:
        return ProcurementRead(**ProcurementService(db).create_procurement(values=payload.model_dump(), actor=current_user))
    except ProcurementAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ProcurementOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.patch("/{procurement_id}", response_model=ProcurementRead)
def update_procurement(
    procurement_id: str,
    payload: ProcurementUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcurementRead:
    try:
        return ProcurementRead(
            **ProcurementService(db).update_procurement(
                procurement_id=procurement_id,
                values=payload.model_dump(exclude_unset=True),
                actor=current_user,
            )
        )
    except ProcurementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ProcurementOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.delete("/{procurement_id}", response_model=ProcurementRead)
def delete_procurement(
    procurement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ProcurementRead:
    try:
        return ProcurementRead(**ProcurementService(db).delete_procurement(procurement_id=procurement_id, actor=current_user))
    except ProcurementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
