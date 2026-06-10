from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.stock_movement import (
    LowStockListResponse,
    StockBalanceRead,
    StockMovementCreateRequest,
    StockMovementListResponse,
    StockMovementRead,
)
from app.services.stock_movement_service import (
    StockMovementNotFoundError,
    StockMovementOperationError,
    StockMovementService,
)


router = APIRouter(prefix="/stock-movements", tags=["stock-movements"])
balances_router = APIRouter(prefix="/stock-balances", tags=["stock-balances"])


@router.get("", response_model=StockMovementListResponse)
def list_stock_movements(
    movement_type: str | None = Query(default=None, pattern="^(in|out)$"),
    catalog_item_id: str | None = Query(default=None),
    q: str | None = Query(default=None, max_length=200),
    reference_number: str | None = Query(default=None, max_length=128),
    movement_date_from: date | None = Query(default=None),
    movement_date_to: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> StockMovementListResponse:
    items, total = StockMovementService(db).list_movements(
        movement_type=movement_type,
        catalog_item_id=catalog_item_id,
        query=q,
        reference_number=reference_number,
        movement_date_from=movement_date_from,
        movement_date_to=movement_date_to,
        limit=limit,
        offset=offset,
    )
    return StockMovementListResponse(
        items=[StockMovementRead(**item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{movement_id}", response_model=StockMovementRead)
def get_stock_movement(
    movement_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> StockMovementRead:
    try:
        return StockMovementRead(**StockMovementService(db).get_movement(movement_id))
    except StockMovementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=StockMovementRead, status_code=status.HTTP_201_CREATED)
def create_stock_movement(
    payload: StockMovementCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StockMovementRead:
    try:
        return StockMovementRead(
            **StockMovementService(db).create_movement(
                values=payload.model_dump(),
                actor=current_user,
            )
        )
    except StockMovementOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.delete("/{movement_id}", response_model=StockMovementRead)
def delete_stock_movement(
    movement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> StockMovementRead:
    try:
        return StockMovementRead(
            **StockMovementService(db).delete_movement(movement_id=movement_id, actor=current_user)
        )
    except StockMovementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@balances_router.get("/low-stock", response_model=LowStockListResponse)
def list_low_stock_balances(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> LowStockListResponse:
    items, total = StockMovementService(db).list_low_stock(limit=limit)
    return LowStockListResponse(
        items=[StockBalanceRead(**item) for item in items],
        total=total,
    )


@balances_router.get("/{catalog_item_id}", response_model=StockBalanceRead)
def get_stock_balance(
    catalog_item_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> StockBalanceRead:
    try:
        return StockBalanceRead(**StockMovementService(db).get_balance(catalog_item_id))
    except StockMovementOperationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
