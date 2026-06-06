from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.contract import ContractCreateRequest, ContractListResponse, ContractRead, ContractUpdateRequest
from app.services.contract_service import (
    ContractAlreadyExistsError,
    ContractNotFoundError,
    ContractOperationError,
    ContractService,
)


router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.get("", response_model=ContractListResponse, dependencies=[Depends(get_current_user)])
def list_contracts(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, max_length=200),
    document_id: str | None = Query(default=None),
    contract_number: str | None = Query(default=None, max_length=128),
    supplier_name: str | None = Query(default=None, max_length=255),
    status_filter: str | None = Query(default=None, alias="status", pattern="^(draft|active|expired|terminated|completed)$"),
    sign_date_from: date | None = Query(default=None),
    sign_date_to: date | None = Query(default=None),
    effective_to_from: date | None = Query(default=None),
    effective_to_to: date | None = Query(default=None),
    sort_by: str = Query(default="created_at", pattern="^(created_at|updated_at|contract_number|supplier_name|status|sign_date|effective_to)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> ContractListResponse:
    try:
        items, total = ContractService(db).list_contracts(
            limit=limit,
            offset=offset,
            query=q,
            document_id=document_id,
            contract_number=contract_number,
            supplier_name=supplier_name,
            status=status_filter,
            sign_date_from=sign_date_from,
            sign_date_to=sign_date_to,
            effective_to_from=effective_to_from,
            effective_to_to=effective_to_to,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
    except ContractOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return ContractListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/by-document/{document_id}", response_model=ContractRead)
def get_contract_by_document(
    document_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ContractRead:
    try:
        return ContractRead(**ContractService(db).get_contract_by_document_id(document_id))
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{contract_id}", response_model=ContractRead)
def get_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ContractRead:
    try:
        return ContractRead(**ContractService(db).get_contract(contract_id))
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("", response_model=ContractRead, status_code=status.HTTP_201_CREATED)
def create_contract(
    payload: ContractCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContractRead:
    try:
        return ContractRead(**ContractService(db).create_contract(values=payload.model_dump(), actor=current_user))
    except ContractAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ContractOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.patch("/{contract_id}", response_model=ContractRead)
def update_contract(
    contract_id: str,
    payload: ContractUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContractRead:
    try:
        return ContractRead(**ContractService(db).update_contract(contract_id=contract_id, values=payload.model_dump(), actor=current_user))
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ContractOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.delete("/{contract_id}", response_model=ContractRead)
def delete_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ContractRead:
    try:
        return ContractRead(**ContractService(db).delete_contract(contract_id=contract_id, actor=current_user))
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
