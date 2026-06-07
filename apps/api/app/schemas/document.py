from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.audit import AuditLogRead


class OCRJobRead(BaseModel):
    id: str
    document_id: str
    job_type: str = "ocr"
    status: str
    attempts: int
    max_attempts: int = 3
    reason: str | None = None
    failed_reason: str | None = None
    error_message: str | None = None
    next_run_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentRead(BaseModel):
    id: str
    title: str
    original_filename: str
    content_type: str | None = None
    document_type: str
    classification_confidence: float | None = None
    document_number: str | None = None
    document_symbol: str | None = None
    issued_date: date | None = None
    issued_place: str | None = None
    issuing_agency: str | None = None
    excerpt: str | None = None
    recipient: str | None = None
    signer_name: str | None = None
    signer_title: str | None = None
    seals_present: bool | None = None
    attachment_present: bool | None = None
    page_count: int | None = None
    metadata_source: str | None = None
    metadata_reviewed_at: datetime | None = None
    business_type: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListItemRead(DocumentRead):
    missing_module_metadata: bool = False


class DocumentPageRead(BaseModel):
    id: str
    page_number: int
    text: str
    confidence: float
    status: str

    model_config = {"from_attributes": True}


class DocumentFileRead(BaseModel):
    id: str
    document_id: str
    original_filename: str
    content_type: str | None = None
    file_size: int
    file_order: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentChunkRead(BaseModel):
    id: str
    chunk_index: int
    text: str
    page_from: int | None = None
    page_to: int | None = None
    section_title: str | None = None
    doc_group: str | None = None
    chunk_level: str | None = None
    section_role: str | None = None
    section_path: list[str] | None = None
    chunk_confidence: float | None = None
    requires_review: bool = False
    qdrant_point_id: str | None = None

    model_config = {"from_attributes": True}


class ReviewQueueChunkRead(BaseModel):
    id: str
    document_id: str
    document_title: str
    document_number: str | None = None
    issued_date: date | None = None
    business_type: str | None = None
    chunk_index: int
    text: str
    page_from: int | None = None
    page_to: int | None = None
    section_title: str | None = None
    doc_group: str | None = None
    chunk_level: str | None = None
    section_role: str | None = None
    section_path: list[str] | None = None
    chunk_confidence: float | None = None
    requires_review: bool = True
    created_at: datetime
    updated_at: datetime


class ReviewQueueResponse(BaseModel):
    items: list[ReviewQueueChunkRead]
    total: int
    limit: int
    offset: int


class DocumentListResponse(BaseModel):
    items: list[DocumentListItemRead]
    total: int
    limit: int
    offset: int


class DocumentDetailRead(DocumentRead):
    files: list[DocumentFileRead] = []
    pages: list[DocumentPageRead] = []
    chunks: list[DocumentChunkRead] = []
    ocr_jobs: list[OCRJobRead] = []
    audit_logs: list[AuditLogRead] = []


class DocumentMetadataUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    document_type: str = Field(default="UNKNOWN", max_length=64)
    classification_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    document_number: str | None = Field(default=None, max_length=128)
    document_symbol: str | None = Field(default=None, max_length=128)
    issued_date: date | None = None
    issued_place: str | None = Field(default=None, max_length=255)
    issuing_agency: str | None = Field(default=None, max_length=255)
    excerpt: str | None = None
    recipient: str | None = None
    signer_name: str | None = Field(default=None, max_length=255)
    signer_title: str | None = Field(default=None, max_length=255)
    seals_present: bool | None = None
    attachment_present: bool | None = None
    page_count: int | None = Field(default=None, ge=1)
    business_type: str | None = Field(default=None, max_length=64)


class UploadResponse(BaseModel):
    document: DocumentRead
    ocr_job: OCRJobRead


class MultiFileUploadResponse(BaseModel):
    document: DocumentRead
    files: list[DocumentFileRead]
    ocr_job: OCRJobRead


class SourceFileMutationResponse(BaseModel):
    document: DocumentRead
    files: list[DocumentFileRead]
    ocr_job: OCRJobRead


class ReorderDocumentFilesRequest(BaseModel):
    file_ids: list[str] = Field(min_length=1)


class ReprocessDocumentRequest(BaseModel):
    reason: str | None = None


class ReprocessDocumentResponse(BaseModel):
    document: DocumentRead
    ocr_job: OCRJobRead
