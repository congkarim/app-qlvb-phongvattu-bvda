from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


ContractStatus = Literal["draft", "active", "expired", "terminated", "completed"]


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
    contract_number: str | None = Field(default=None, max_length=128)
    supplier_name: str | None = Field(default=None, max_length=255)
    contract_status: ContractStatus | None = None


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
    contract_id: str | None = None
    contract_number: str | None = None
    supplier_name: str | None = None
    contract_status: str | None = None


class SemanticSearchResponse(BaseModel):
    query: str
    results: list[SemanticSearchResult]


class RagAnswerRequest(SemanticSearchRequest):
    limit: int = Field(default=6, ge=1, le=12)
    min_score: float = Field(default=0.35, ge=0.0)
    max_citations: int = Field(default=4, ge=1, le=8)


class RagCitation(BaseModel):
    document_id: str
    chunk_id: str
    score: float
    quote: str
    title: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    issued_date: date | None = None
    issuing_agency: str | None = None
    business_type: str | None = None
    page_from: int | None = None
    page_to: int | None = None
    section_role: str | None = None
    section_path: list[str] = Field(default_factory=list)


class RagAnswerResponse(BaseModel):
    query: str
    answer: str
    grounded: bool
    confidence: float
    fallback_reason: str | None = None
    citations: list[RagCitation] = Field(default_factory=list)
