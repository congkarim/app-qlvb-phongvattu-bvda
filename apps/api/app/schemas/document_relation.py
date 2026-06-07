from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

RelationType = Literal["references", "appendix_of", "implements", "related"]


class RelatedDocumentSummary(BaseModel):
    id: str
    title: str
    document_number: str | None = None
    document_type: str
    status: str


class DocumentRelationOutgoingRead(BaseModel):
    id: str
    relation_type: str
    notes: str | None = None
    target_document: RelatedDocumentSummary
    created_at: datetime


class DocumentRelationIncomingRead(BaseModel):
    id: str
    relation_type: str
    notes: str | None = None
    source_document: RelatedDocumentSummary
    created_at: datetime


class DocumentRelationsResponse(BaseModel):
    document_id: str
    outgoing: list[DocumentRelationOutgoingRead] = Field(default_factory=list)
    incoming: list[DocumentRelationIncomingRead] = Field(default_factory=list)


class DocumentRelationCreateRequest(BaseModel):
    target_document_id: str
    relation_type: RelationType
    notes: str | None = Field(default=None, max_length=2000)


class DocumentRelationDeleteRead(BaseModel):
    id: str
    source_document_id: str
    target_document_id: str
    relation_type: str
    notes: str | None = None
    created_at: datetime
