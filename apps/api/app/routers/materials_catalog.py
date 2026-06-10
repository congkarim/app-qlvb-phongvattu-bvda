from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.materials_catalog import (
    MaterialsCatalogAutocompleteRead,
    MaterialsCatalogCreateRequest,
    MaterialsCatalogListResponse,
    MaterialsCatalogRead,
    MaterialsCatalogUpdateRequest,
)
from app.services.materials_catalog_service import (
    MaterialsCatalogAlreadyExistsError,
    MaterialsCatalogNotFoundError,
    MaterialsCatalogOperationError,
    MaterialsCatalogService,
)


router = APIRouter(prefix="/materials-catalog", tags=["materials-catalog"])


@router.get("", response_model=list[MaterialsCatalogAutocompleteRead])
def list_active_materials_catalog(
    q: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[MaterialsCatalogAutocompleteRead]:
    return MaterialsCatalogService(db).list_active(query=q, limit=limit)


@router.get("/all", response_model=MaterialsCatalogListResponse)
def list_all_materials_catalog(
    q: str | None = Query(default=None, max_length=200),
    is_active: bool | None = Query(default=None),
    category: str | None = Query(default=None, max_length=128),
    below_min: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> MaterialsCatalogListResponse:
    items, total = MaterialsCatalogService(db).list_all(
        query=q,
        is_active=is_active,
        category=category,
        below_min=below_min,
        limit=limit,
        offset=offset,
    )
    return MaterialsCatalogListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{catalog_id}", response_model=MaterialsCatalogRead)
def get_materials_catalog_item(
    catalog_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> MaterialsCatalogRead:
    try:
        return MaterialsCatalogRead(**MaterialsCatalogService(db).get_catalog_item(catalog_id))
    except MaterialsCatalogNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=MaterialsCatalogRead, status_code=status.HTTP_201_CREATED)
def create_materials_catalog_item(
    payload: MaterialsCatalogCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> MaterialsCatalogRead:
    try:
        return MaterialsCatalogRead(
            **MaterialsCatalogService(db).create_catalog_item(
                values=payload.model_dump(),
                actor=current_user,
            )
        )
    except MaterialsCatalogAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except MaterialsCatalogOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.patch("/{catalog_id}", response_model=MaterialsCatalogRead)
def update_materials_catalog_item(
    catalog_id: str,
    payload: MaterialsCatalogUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> MaterialsCatalogRead:
    try:
        return MaterialsCatalogRead(
            **MaterialsCatalogService(db).update_catalog_item(
                catalog_id=catalog_id,
                values=payload.model_dump(exclude_unset=True),
                actor=current_user,
            )
        )
    except MaterialsCatalogNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MaterialsCatalogAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except MaterialsCatalogOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.delete("/{catalog_id}", response_model=MaterialsCatalogRead)
def delete_materials_catalog_item(
    catalog_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> MaterialsCatalogRead:
    try:
        return MaterialsCatalogRead(
            **MaterialsCatalogService(db).delete_catalog_item(catalog_id=catalog_id, actor=current_user)
        )
    except MaterialsCatalogNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
