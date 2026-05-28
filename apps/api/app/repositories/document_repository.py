from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.document import Document, DocumentChunk, DocumentPage, OCRJob


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_document(
        self,
        *,
        title: str,
        original_filename: str,
        file_path: str,
        content_type: str | None,
        document_type: str = "document",
    ) -> Document:
        document = Document(
            title=title,
            original_filename=original_filename,
            file_path=file_path,
            content_type=content_type,
            document_type=document_type,
        )
        self.db.add(document)
        self.db.flush()
        return document

    def list_documents(self, limit: int = 50, offset: int = 0) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.deleted_at.is_(None))
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(stmt))

    def get_document(self, document_id: str) -> Document | None:
        stmt = (
            select(Document)
            .where(Document.id == document_id, Document.deleted_at.is_(None))
            .options(
                selectinload(Document.pages),
                selectinload(Document.chunks),
                selectinload(Document.ocr_jobs),
            )
        )
        return self.db.scalar(stmt)

    def update_status(self, document: Document, status: str) -> Document:
        document.status = status
        self.db.add(document)
        self.db.flush()
        return document

    def create_page(self, *, document_id: str, page_number: int, text: str, confidence: float) -> DocumentPage:
        page = DocumentPage(
            document_id=document_id,
            page_number=page_number,
            text=text,
            confidence=confidence,
            status="ocr_completed",
        )
        self.db.add(page)
        self.db.flush()
        return page

    def create_chunk(
        self,
        *,
        document_id: str,
        chunk_index: int,
        text: str,
        content_hash: str,
        page_from: int | None = None,
        page_to: int | None = None,
        section_title: str | None = None,
        qdrant_point_id: str | None = None,
    ) -> DocumentChunk:
        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=chunk_index,
            text=text,
            page_from=page_from,
            page_to=page_to,
            section_title=section_title,
            content_hash=content_hash,
            qdrant_point_id=qdrant_point_id,
        )
        self.db.add(chunk)
        self.db.flush()
        return chunk


class OCRJobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_job(self, document_id: str) -> OCRJob:
        job = OCRJob(document_id=document_id, status="pending")
        self.db.add(job)
        self.db.flush()
        return job

    def get_next_pending_job(self) -> OCRJob | None:
        stmt = (
            select(OCRJob)
            .where(OCRJob.status == "pending", OCRJob.deleted_at.is_(None))
            .order_by(OCRJob.created_at.asc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def get_job(self, job_id: str) -> OCRJob | None:
        return self.db.get(OCRJob, job_id)
