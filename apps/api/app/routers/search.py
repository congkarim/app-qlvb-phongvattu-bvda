from fastapi import APIRouter

from app.schemas.search import SemanticSearchRequest, SemanticSearchResponse
from app.services.search_service import SearchService


router = APIRouter(prefix="/search", tags=["search"])


@router.post("/semantic", response_model=SemanticSearchResponse)
def semantic_search(payload: SemanticSearchRequest) -> SemanticSearchResponse:
    results = SearchService().semantic_search(
        query=payload.query,
        limit=payload.limit,
        document_type=payload.document_type,
        department_id=payload.department_id,
    )
    return SemanticSearchResponse(query=payload.query, results=results)
