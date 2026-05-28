from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=50)
    document_type: str | None = None
    department_id: str | None = None


class SemanticSearchResult(BaseModel):
    document_id: str
    chunk_id: str
    score: float
    text: str
    title: str | None = None
    page_from: int | None = None
    page_to: int | None = None


class SemanticSearchResponse(BaseModel):
    query: str
    results: list[SemanticSearchResult]
