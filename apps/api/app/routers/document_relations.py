from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.document_relation import DocumentRelationDeleteRead
from app.services.document_relation_service import (
    DocumentRelationForbiddenError,
    DocumentRelationNotFoundError,
    DocumentRelationService,
)


router = APIRouter(prefix="/document-relations", tags=["document-relations"])


@router.delete("/{relation_id}", response_model=DocumentRelationDeleteRead)
def delete_document_relation(
    relation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentRelationDeleteRead:
    try:
        return DocumentRelationDeleteRead(
            **DocumentRelationService(db).delete_relation(relation_id=relation_id, actor=current_user)
        )
    except DocumentRelationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DocumentRelationForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
