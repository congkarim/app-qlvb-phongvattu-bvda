from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.schemas.audit import AuditLogRead
from app.schemas.user import UserCreateRequest, UserListResponse, UserRead, UserResetPasswordRequest, UserUpdateRequest
from app.services.user_service import (
    UserAlreadyExistsError,
    UserNotFoundError,
    UserOperationError,
    UserService,
)


router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_admin)])


@router.get("", response_model=UserListResponse)
def list_users(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, max_length=200),
    role: str | None = Query(default=None, pattern="^(admin|user)$"),
    is_active: bool | None = Query(default=None),
    sort_by: str = Query(default="created_at", pattern="^(created_at|updated_at|email|full_name|role|is_active)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> UserListResponse:
    items, total = UserService(db).list_users(
        limit=limit,
        offset=offset,
        query=q,
        role=role,
        is_active=is_active,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return UserListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{user_id}/audit-logs", response_model=list[AuditLogRead])
def list_user_audit_logs(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[AuditLogRead]:
    try:
        return UserService(db).list_user_audit_logs(user_id=user_id, limit=limit)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserRead:
    try:
        return UserService(db).create_user(
            email=str(payload.email),
            full_name=payload.full_name,
            password=payload.password,
            role=payload.role,
            is_active=payload.is_active,
            actor=current_user,
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except UserOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserRead:
    try:
        return UserService(db).update_user(
            user_id=user_id,
            full_name=payload.full_name,
            role=payload.role,
            is_active=payload.is_active,
            actor=current_user,
        )
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except UserOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post("/{user_id}/activate", response_model=UserRead)
def activate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserRead:
    try:
        return UserService(db).set_user_active(user_id=user_id, is_active=True, actor=current_user)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/{user_id}/deactivate", response_model=UserRead)
def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserRead:
    try:
        return UserService(db).set_user_active(user_id=user_id, is_active=False, actor=current_user)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except UserOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post("/{user_id}/reset-password", response_model=UserRead)
def reset_user_password(
    user_id: str,
    payload: UserResetPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserRead:
    try:
        return UserService(db).reset_password(user_id=user_id, password=payload.password, actor=current_user)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except UserOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.delete("/{user_id}", response_model=UserRead)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserRead:
    try:
        return UserService(db).soft_delete_user(user_id=user_id, actor=current_user)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except UserOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
