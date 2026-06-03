import re
from datetime import datetime, timezone

from sqlalchemy import or_, select
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

    def list_pages_for_document(self, document_id: str) -> list[DocumentPage]:
        stmt = (
            select(DocumentPage)
            .where(DocumentPage.document_id == document_id, DocumentPage.deleted_at.is_(None))
            .order_by(DocumentPage.page_number.asc())
        )
        return list(self.db.scalars(stmt))

    def replace_pages_for_document(
        self,
        *,
        document_id: str,
        pages: list[dict[str, str | int | float]],
    ) -> list[DocumentPage]:
        existing_by_number = {page.page_number: page for page in self.list_pages_for_document(document_id)}
        retained_numbers: set[int] = set()
        replaced: list[DocumentPage] = []

        for page_payload in pages:
            page_number = int(page_payload["page_number"])
            retained_numbers.add(page_number)
            page = existing_by_number.get(page_number)
            if page is None:
                page = DocumentPage(document_id=document_id, page_number=page_number)
            page.text = str(page_payload["text"])
            page.confidence = float(page_payload["confidence"])
            page.status = "ocr_completed"
            page.deleted_at = None
            self.db.add(page)
            replaced.append(page)

        deleted_at = datetime.now(timezone.utc)
        for page in existing_by_number.values():
            if page.page_number not in retained_numbers:
                page.deleted_at = deleted_at
                self.db.add(page)

        self.db.flush()
        return replaced

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

    def list_chunks_for_document(self, document_id: str) -> list[DocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id, DocumentChunk.deleted_at.is_(None))
            .options(selectinload(DocumentChunk.document))
            .order_by(DocumentChunk.chunk_index.asc())
        )
        return list(self.db.scalars(stmt))

    def replace_chunks_for_document(
        self,
        *,
        document_id: str,
        chunks: list[dict[str, str | int | None]],
    ) -> tuple[list[DocumentChunk], list[DocumentChunk]]:
        existing_by_index = {chunk.chunk_index: chunk for chunk in self.list_chunks_for_document(document_id)}
        retained_indexes: set[int] = set()
        replaced: list[DocumentChunk] = []

        for chunk_index, chunk_payload in enumerate(chunks):
            retained_indexes.add(chunk_index)
            chunk = existing_by_index.get(chunk_index)
            if chunk is None:
                chunk = DocumentChunk(document_id=document_id, chunk_index=chunk_index)
            chunk.text = str(chunk_payload["text"])
            chunk.content_hash = str(chunk_payload["content_hash"])
            chunk.page_from = int(chunk_payload["page_from"]) if chunk_payload["page_from"] is not None else None
            chunk.page_to = int(chunk_payload["page_to"]) if chunk_payload["page_to"] is not None else None
            chunk.section_title = str(chunk_payload["section_title"]) if chunk_payload["section_title"] else None
            chunk.deleted_at = None
            self.db.add(chunk)
            replaced.append(chunk)

        deleted_at = datetime.now(timezone.utc)
        deleted: list[DocumentChunk] = []
        for chunk in existing_by_index.values():
            if chunk.chunk_index not in retained_indexes:
                chunk.deleted_at = deleted_at
                self.db.add(chunk)
                deleted.append(chunk)

        self.db.flush()
        return replaced, deleted

    def list_chunks_for_indexing(self, *, limit: int = 100, offset: int = 0) -> list[DocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .join(Document)
            .where(
                DocumentChunk.deleted_at.is_(None),
                Document.deleted_at.is_(None),
            )
            .options(selectinload(DocumentChunk.document))
            .order_by(DocumentChunk.created_at.asc(), DocumentChunk.chunk_index.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(stmt))

    def search_chunks_by_keyword(
        self,
        *,
        query: str,
        limit: int,
        document_type: str | None = None,
        department_id: str | None = None,
    ) -> list[DocumentChunk]:
        terms = list(dict.fromkeys(term for term in re.findall(r"\w+", query.lower()) if len(term) >= 3))
        if not terms:
            return []

        conditions = [DocumentChunk.text.ilike(f"%{term}%") for term in terms]
        conditions.append(Document.title.ilike(f"%{query}%"))
        stmt = (
            select(DocumentChunk)
            .join(Document)
            .where(
                DocumentChunk.deleted_at.is_(None),
                Document.deleted_at.is_(None),
                or_(*conditions),
            )
            .options(selectinload(DocumentChunk.document))
            .order_by(DocumentChunk.created_at.desc(), DocumentChunk.chunk_index.asc())
            .limit(limit)
        )
        if document_type is not None:
            stmt = stmt.where(Document.document_type == document_type)
        if department_id is not None:
            stmt = stmt.where(Document.department_id == department_id)
        return list(self.db.scalars(stmt))

    def update_chunk_qdrant_point_id(self, chunk: DocumentChunk, point_id: str) -> DocumentChunk:
        chunk.qdrant_point_id = point_id
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
