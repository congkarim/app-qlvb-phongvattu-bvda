from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.search import SemanticSearchRequest, SemanticSearchResponse
from app.services.search_service import SearchService


router = APIRouter(prefix="/search", tags=["search"], dependencies=[Depends(get_current_user)])


@router.post("/semantic", response_model=SemanticSearchResponse)
def semantic_search(payload: SemanticSearchRequest, db: Session = Depends(get_db)) -> SemanticSearchResponse:
    results = SearchService(db).semantic_search(
        query=payload.query,
        limit=payload.limit,
        document_type=payload.document_type,
        department_id=payload.department_id,
    )
    return SemanticSearchResponse(query=payload.query, results=results)
