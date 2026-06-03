from datetime import datetime

from pydantic import BaseModel


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
    pages: list[DocumentPageRead] = []
    chunks: list[DocumentChunkRead] = []
    ocr_jobs: list[OCRJobRead] = []


class UploadResponse(BaseModel):
    document: DocumentRead
    ocr_job: OCRJobRead


class ReprocessDocumentRequest(BaseModel):
    reason: str | None = None


class ReprocessDocumentResponse(BaseModel):
    document: DocumentRead
    ocr_job: OCRJobRead
