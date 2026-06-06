from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.search import RagAnswerRequest, RagAnswerResponse, SemanticSearchRequest, SemanticSearchResponse
from app.services.rag_answer_service import RagAnswerService
from app.services.search_service import SearchService


router = APIRouter(prefix="/search", tags=["search"], dependencies=[Depends(get_current_user)])


@router.post("/semantic", response_model=SemanticSearchResponse)
def semantic_search(payload: SemanticSearchRequest, db: Session = Depends(get_db)) -> SemanticSearchResponse:
    results = SearchService(db).semantic_search(
        query=payload.query,
        limit=payload.limit,
        document_type=payload.document_type,
        department_id=payload.department_id,
        business_type=payload.business_type,
        document_number=payload.document_number,
        issued_date=payload.issued_date,
        doc_group=payload.doc_group,
        section_role=payload.section_role,
        requires_review=payload.requires_review,
        contract_number=payload.contract_number,
        supplier_name=payload.supplier_name,
        contract_status=payload.contract_status,
    )
    return SemanticSearchResponse(query=payload.query, results=results)


@router.post("/answer", response_model=RagAnswerResponse)
def rag_answer(payload: RagAnswerRequest, db: Session = Depends(get_db)) -> RagAnswerResponse:
    answer = RagAnswerService(db).answer(
        query=payload.query,
        limit=payload.limit,
        min_score=payload.min_score,
        max_citations=payload.max_citations,
        document_type=payload.document_type,
        department_id=payload.department_id,
        business_type=payload.business_type,
        document_number=payload.document_number,
        issued_date=payload.issued_date,
        doc_group=payload.doc_group,
        section_role=payload.section_role,
        requires_review=payload.requires_review,
        contract_number=payload.contract_number,
        supplier_name=payload.supplier_name,
        contract_status=payload.contract_status,
    )
    return RagAnswerResponse(**answer)
