from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.catalog import (
    CatalogItemCreateRequest,
    CatalogItemRead,
    CatalogItemUpdateRequest,
    DepartmentCreateRequest,
    DepartmentRead,
    DepartmentUpdateRequest,
)
from app.services.catalog_service import (
    CatalogAlreadyExistsError,
    CatalogNotFoundError,
    CatalogOperationError,
    CatalogService,
)


router = APIRouter(prefix="/catalogs", tags=["catalogs"])
admin_router = APIRouter(prefix="/admin/catalogs", tags=["admin-catalogs"], dependencies=[Depends(require_admin)])


@router.get("/departments", response_model=list[DepartmentRead])
def list_departments(
    include_inactive: bool = Query(default=False),
    q: str | None = Query(default=None, max_length=200),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[DepartmentRead]:
    return CatalogService(db).list_departments(include_inactive=include_inactive, query=q)


@router.get("/business-types", response_model=list[CatalogItemRead])
def list_business_types(
    include_inactive: bool = Query(default=False),
    q: str | None = Query(default=None, max_length=200),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[CatalogItemRead]:
    return CatalogService(db).list_items(catalog_type="business_type", include_inactive=include_inactive, query=q)


@router.get("/document-types", response_model=list[CatalogItemRead])
def list_document_types(
    include_inactive: bool = Query(default=False),
    q: str | None = Query(default=None, max_length=200),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[CatalogItemRead]:
    return CatalogService(db).list_items(catalog_type="document_type", include_inactive=include_inactive, query=q)


@admin_router.post("/departments", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> DepartmentRead:
    try:
        return CatalogService(db).create_department(values=payload.model_dump(), actor=current_user)
    except CatalogAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except CatalogOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@admin_router.patch("/departments/{department_id}", response_model=DepartmentRead)
def update_department(
    department_id: str,
    payload: DepartmentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> DepartmentRead:
    try:
        return CatalogService(db).update_department(department_id=department_id, values=payload.model_dump(), actor=current_user)
    except CatalogAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except CatalogNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except CatalogOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@admin_router.delete("/departments/{department_id}", response_model=DepartmentRead)
def delete_department(
    department_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> DepartmentRead:
    try:
        return CatalogService(db).delete_department(department_id=department_id, actor=current_user)
    except CatalogNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except CatalogOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@admin_router.get("/items", response_model=list[CatalogItemRead])
def list_admin_items(
    catalog_type: str | None = Query(default=None, pattern="^(business_type|document_type)$"),
    include_inactive: bool = Query(default=True),
    q: str | None = Query(default=None, max_length=200),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> list[CatalogItemRead]:
    try:
        return CatalogService(db).list_items(catalog_type=catalog_type, include_inactive=include_inactive, query=q)
    except CatalogOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@admin_router.post("/items", response_model=CatalogItemRead, status_code=status.HTTP_201_CREATED)
def create_item(
    payload: CatalogItemCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> CatalogItemRead:
    try:
        return CatalogService(db).create_item(values=payload.model_dump(), actor=current_user)
    except CatalogAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except CatalogOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@admin_router.patch("/items/{item_id}", response_model=CatalogItemRead)
def update_item(
    item_id: str,
    payload: CatalogItemUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> CatalogItemRead:
    try:
        return CatalogService(db).update_item(item_id=item_id, values=payload.model_dump(), actor=current_user)
    except CatalogAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except CatalogNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except CatalogOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@admin_router.delete("/items/{item_id}", response_model=CatalogItemRead)
def delete_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> CatalogItemRead:
    try:
        return CatalogService(db).delete_item(item_id=item_id, actor=current_user)
    except CatalogNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
