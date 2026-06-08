from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.procurement_line_item import (
    ProcurementLineItemCreateRequest,
    ProcurementLineItemListResponse,
    ProcurementLineItemRead,
    ProcurementLineItemUpdateRequest,
)
from app.services.procurement_line_item_service import (
    ProcurementLineItemAlreadyExistsError,
    ProcurementLineItemNotFoundError,
    ProcurementLineItemOperationError,
    ProcurementLineItemService,
)
from app.services.procurement_service import ProcurementNotFoundError


router = APIRouter(prefix="/procurement-line-items", tags=["procurement-line-items"])


@router.patch("/{line_item_id}", response_model=ProcurementLineItemRead)
def update_procurement_line_item(
    line_item_id: str,
    payload: ProcurementLineItemUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcurementLineItemRead:
    try:
        return ProcurementLineItemRead(
            **ProcurementLineItemService(db).update_line_item(
                line_item_id=line_item_id,
                values=payload.model_dump(exclude_unset=True),
                actor=current_user,
            )
        )
    except ProcurementLineItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProcurementLineItemAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ProcurementLineItemOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.delete("/{line_item_id}", response_model=ProcurementLineItemRead)
def delete_procurement_line_item(
    line_item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ProcurementLineItemRead:
    try:
        return ProcurementLineItemRead(
            **ProcurementLineItemService(db).delete_line_item(line_item_id=line_item_id, actor=current_user)
        )
    except ProcurementLineItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
