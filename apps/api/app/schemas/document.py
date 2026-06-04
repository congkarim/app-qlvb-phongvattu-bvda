from datetime import date, datetime

from pydantic import BaseModel, Field


class AuditActorRead(BaseModel):
    id: str
    email: str
    full_name: str

    model_config = {"from_attributes": True}


class AuditLogRead(BaseModel):
    id: str
    actor_user_id: str | None = None
    actor: AuditActorRead | None = None
    action: str
    entity_type: str
    entity_id: str
    metadata: dict = Field(default_factory=dict, validation_alias="metadata_")
    created_at: datetime

    model_config = {"from_attributes": True}


class OCRJobRead(BaseModel):
    id: str
    document_id: str
    job_type: str = "ocr"
    status: str
    attempts: int
    reason: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentRead(BaseModel):
    id: str
    title: str
    original_filename: str
    content_type: str | None = None
    document_type: str
    document_number: str | None = None
    issued_date: date | None = None
    issuing_agency: str | None = None
    business_type: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


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
    qdrant_point_id: str | None = None

    model_config = {"from_attributes": True}


class DocumentDetailRead(DocumentRead):
    files: list[DocumentFileRead] = []
    pages: list[DocumentPageRead] = []
    chunks: list[DocumentChunkRead] = []
    ocr_jobs: list[OCRJobRead] = []
    audit_logs: list[AuditLogRead] = []


class DocumentMetadataUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    document_number: str | None = Field(default=None, max_length=128)
    issued_date: date | None = None
    issuing_agency: str | None = Field(default=None, max_length=255)
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
