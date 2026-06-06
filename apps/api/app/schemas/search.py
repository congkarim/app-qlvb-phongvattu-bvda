from datetime import date

from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=50)
    document_type: str | None = None
    department_id: str | None = None
    business_type: str | None = None
    document_number: str | None = None
    issued_date: date | None = None
    doc_group: str | None = Field(default=None, max_length=8)
    section_role: str | None = Field(default=None, max_length=64)
    requires_review: bool | None = None


class SemanticSearchResult(BaseModel):
    document_id: str
    chunk_id: str
    score: float
    text: str
    title: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    issued_date: date | None = None
    issuing_agency: str | None = None
    business_type: str | None = None
    page_from: int | None = None
    page_to: int | None = None
    doc_group: str | None = None
    section_role: str | None = None
    section_path: list[str] = Field(default_factory=list)
    requires_review: bool = False


class SemanticSearchResponse(BaseModel):
    query: str
    results: list[SemanticSearchResult]
