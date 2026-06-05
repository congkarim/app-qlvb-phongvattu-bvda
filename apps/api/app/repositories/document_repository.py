import re
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import asc, desc, func, nullsfirst, or_, select
from sqlalchemy.orm import Session, selectinload, with_loader_criteria

from app.models.document import Document, DocumentChunk, DocumentFile, DocumentPage, OCRJob
from app.repositories.audit_log_repository import AuditLogRepository


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
        document_number: str | None = None,
        issued_date=None,
        issuing_agency: str | None = None,
        business_type: str | None = None,
    ) -> Document:
        document = Document(
            title=title,
            original_filename=original_filename,
            file_path=file_path,
            content_type=content_type,
            document_type=document_type,
            document_number=document_number,
            issued_date=issued_date,
            issuing_agency=issuing_agency,
            business_type=business_type,
        )
        self.db.add(document)
        self.db.flush()
        return document

    def _document_list_conditions(
        self,
        *,
        query: str | None = None,
        status: str | None = None,
        document_type: str | None = None,
        business_type: str | None = None,
    ):
        conditions = [Document.deleted_at.is_(None)]
        if query:
            pattern = f"%{query}%"
            conditions.append(
                or_(
                    Document.title.ilike(pattern),
                    Document.original_filename.ilike(pattern),
                    Document.document_number.ilike(pattern),
                    Document.document_symbol.ilike(pattern),
                    Document.issuing_agency.ilike(pattern),
                    Document.excerpt.ilike(pattern),
                    Document.recipient.ilike(pattern),
                    Document.signer_name.ilike(pattern),
                )
            )
        if status:
            conditions.append(Document.status == status)
        if document_type:
            conditions.append(Document.document_type == document_type)
        if business_type:
            conditions.append(Document.business_type == business_type)
        return conditions

    def list_documents(
        self,
        limit: int = 50,
        offset: int = 0,
        *,
        query: str | None = None,
        status: str | None = None,
        document_type: str | None = None,
        business_type: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> list[Document]:
        stmt = select(Document).where(
            *self._document_list_conditions(
                query=query,
                status=status,
                document_type=document_type,
                business_type=business_type,
            )
        )

        sortable_columns = {
            "created_at": Document.created_at,
            "updated_at": Document.updated_at,
            "issued_date": Document.issued_date,
            "title": Document.title,
            "status": Document.status,
            "document_type": Document.document_type,
            "business_type": Document.business_type,
        }
        sort_column = sortable_columns.get(sort_by, Document.created_at)
        direction = asc if sort_dir == "asc" else desc
        if sort_by == "created_at":
            stmt = stmt.order_by(direction(sort_column), direction(Document.id))
        else:
            stmt = stmt.order_by(direction(sort_column), Document.created_at.desc(), Document.id.desc())
        stmt = stmt.limit(limit).offset(offset)
        return list(self.db.scalars(stmt))

    def count_documents(
        self,
        *,
        query: str | None = None,
        status: str | None = None,
        document_type: str | None = None,
        business_type: str | None = None,
    ) -> int:
        stmt = select(func.count(Document.id)).where(
            *self._document_list_conditions(
                query=query,
                status=status,
                document_type=document_type,
                business_type=business_type,
            )
        )
        return int(self.db.scalar(stmt) or 0)

    def get_document(self, document_id: str) -> Document | None:
        stmt = (
            select(Document)
            .where(Document.id == document_id, Document.deleted_at.is_(None))
            .options(
                selectinload(Document.pages),
                selectinload(Document.files),
                selectinload(Document.chunks),
                selectinload(Document.ocr_jobs),
                with_loader_criteria(DocumentFile, DocumentFile.deleted_at.is_(None)),
                with_loader_criteria(DocumentPage, DocumentPage.deleted_at.is_(None)),
                with_loader_criteria(DocumentChunk, DocumentChunk.deleted_at.is_(None)),
                with_loader_criteria(OCRJob, OCRJob.deleted_at.is_(None)),
            )
        )
        document = self.db.scalar(stmt)
        if document is not None:
            document.audit_logs = AuditLogRepository(self.db).list_for_entity(
                entity_type="document",
                entity_id=document.id,
            )
        return document

    def update_status(self, document: Document, status: str) -> Document:
        document.status = status
        self.db.add(document)
        self.db.flush()
        return document

    def update_metadata(
        self,
        document: Document,
        *,
        title: str,
        document_type: str,
        classification_confidence: float | None,
        document_number: str | None,
        document_symbol: str | None,
        issued_date,
        issued_place: str | None,
        issuing_agency: str | None,
        excerpt: str | None,
        recipient: str | None,
        signer_name: str | None,
        signer_title: str | None,
        seals_present: bool | None,
        attachment_present: bool | None,
        page_count: int | None,
        metadata_source: str | None,
        metadata_reviewed_at,
        business_type: str | None,
    ) -> Document:
        document.title = title
        document.document_type = document_type
        document.classification_confidence = classification_confidence
        document.document_number = document_number
        document.document_symbol = document_symbol
        document.issued_date = issued_date
        document.issued_place = issued_place
        document.issuing_agency = issuing_agency
        document.excerpt = excerpt
        document.recipient = recipient
        document.signer_name = signer_name
        document.signer_title = signer_title
        document.seals_present = seals_present
        document.attachment_present = attachment_present
        document.page_count = page_count
        document.metadata_source = metadata_source
        document.metadata_reviewed_at = metadata_reviewed_at
        document.business_type = business_type
        self.db.add(document)
        self.db.flush()
        return document

    def create_file(
        self,
        *,
        document_id: str,
        original_filename: str,
        file_path: str,
        content_type: str | None,
        file_size: int,
        file_order: int,
        status: str = "pending",
    ) -> DocumentFile:
        document_file = DocumentFile(
            document_id=document_id,
            original_filename=original_filename,
            file_path=file_path,
            content_type=content_type,
            file_size=file_size,
            file_order=file_order,
            status=status,
        )
        self.db.add(document_file)
        self.db.flush()
        return document_file

    def list_files_for_document(self, document_id: str) -> list[DocumentFile]:
        stmt = (
            select(DocumentFile)
            .where(DocumentFile.document_id == document_id, DocumentFile.deleted_at.is_(None))
            .order_by(DocumentFile.file_order.asc(), DocumentFile.created_at.asc())
        )
        return list(self.db.scalars(stmt))

    def get_file_for_document(self, *, document_id: str, document_file_id: str) -> DocumentFile | None:
        stmt = select(DocumentFile).where(
            DocumentFile.id == document_file_id,
            DocumentFile.document_id == document_id,
            DocumentFile.deleted_at.is_(None),
        )
        return self.db.scalar(stmt)

    def get_active_file_for_document(self, *, document_id: str, document_file_id: str) -> DocumentFile | None:
        stmt = (
            select(DocumentFile)
            .join(Document, Document.id == DocumentFile.document_id)
            .where(
                Document.id == document_id,
                Document.deleted_at.is_(None),
                DocumentFile.id == document_file_id,
                DocumentFile.deleted_at.is_(None),
            )
        )
        return self.db.scalar(stmt)

    def update_file_status(self, document_file: DocumentFile, status: str) -> DocumentFile:
        document_file.status = status
        self.db.add(document_file)
        self.db.flush()
        return document_file

    def update_file_order(self, document_file: DocumentFile, file_order: int) -> DocumentFile:
        document_file.file_order = file_order
        self.db.add(document_file)
        self.db.flush()
        return document_file

    def soft_delete_file(self, document_file: DocumentFile) -> DocumentFile:
        document_file.deleted_at = datetime.now(timezone.utc)
        self.db.add(document_file)
        self.db.flush()
        return document_file

    def update_legacy_file_fields(self, document: Document, document_file: DocumentFile) -> Document:
        document.original_filename = document_file.original_filename
        document.file_path = document_file.file_path
        document.content_type = document_file.content_type
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
        doc_group: str | None = None,
        chunk_level: str | None = None,
        section_role: str | None = None,
        section_path: list[str] | None = None,
        chunk_confidence: float | None = None,
        requires_review: bool = False,
        chunk_metadata: dict[str, Any] | None = None,
        qdrant_point_id: str | None = None,
    ) -> DocumentChunk:
        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=chunk_index,
            text=text,
            page_from=page_from,
            page_to=page_to,
            section_title=section_title,
            doc_group=doc_group,
            chunk_level=chunk_level,
            section_role=section_role,
            section_path=section_path,
            chunk_confidence=chunk_confidence,
            requires_review=requires_review,
            content_hash=content_hash,
            qdrant_point_id=qdrant_point_id,
        )
        if chunk_metadata is not None:
            self._apply_chunk_metadata(chunk, {"chunk_metadata": chunk_metadata})
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

    def get_chunk_for_document(self, *, document_id: str, chunk_id: str) -> DocumentChunk | None:
        stmt = (
            select(DocumentChunk)
            .join(Document)
            .where(
                Document.id == document_id,
                Document.deleted_at.is_(None),
                DocumentChunk.id == chunk_id,
                DocumentChunk.document_id == document_id,
                DocumentChunk.deleted_at.is_(None),
            )
            .options(selectinload(DocumentChunk.document))
        )
        return self.db.scalar(stmt)

    def mark_chunk_reviewed(self, chunk: DocumentChunk) -> DocumentChunk:
        chunk.requires_review = False
        self.db.add(chunk)
        self.db.flush()
        return chunk

    def list_review_queue_chunks(
        self,
        *,
        limit: int,
        offset: int,
        section_role: str | None = None,
        document_id: str | None = None,
        max_confidence: float | None = None,
    ) -> list[DocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .join(Document)
            .options(selectinload(DocumentChunk.document))
            .order_by(
                nullsfirst(DocumentChunk.chunk_confidence.asc()),
                DocumentChunk.updated_at.desc(),
                DocumentChunk.id.asc(),
            )
            .limit(limit)
            .offset(offset)
        )
        stmt = self._apply_review_queue_filters(
            stmt,
            section_role=section_role,
            document_id=document_id,
            max_confidence=max_confidence,
        )
        return list(self.db.scalars(stmt))

    def count_review_queue_chunks(
        self,
        *,
        section_role: str | None = None,
        document_id: str | None = None,
        max_confidence: float | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(DocumentChunk).join(Document)
        stmt = self._apply_review_queue_filters(
            stmt,
            section_role=section_role,
            document_id=document_id,
            max_confidence=max_confidence,
        )
        return int(self.db.scalar(stmt) or 0)

    def _apply_review_queue_filters(
        self,
        stmt,
        *,
        section_role: str | None,
        document_id: str | None,
        max_confidence: float | None,
    ):
        stmt = stmt.where(
            DocumentChunk.deleted_at.is_(None),
            DocumentChunk.requires_review.is_(True),
            Document.deleted_at.is_(None),
        )
        if section_role is not None:
            stmt = stmt.where(DocumentChunk.section_role == section_role)
        if document_id is not None:
            stmt = stmt.where(DocumentChunk.document_id == document_id)
        if max_confidence is not None:
            stmt = stmt.where(
                or_(
                    DocumentChunk.chunk_confidence <= max_confidence,
                    DocumentChunk.chunk_confidence.is_(None),
                )
            )
        return stmt

    def list_documents_for_chunk_metadata_backfill(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        missing_only: bool = True,
    ) -> list[Document]:
        stmt = (
            select(Document)
            .join(DocumentChunk, DocumentChunk.document_id == Document.id)
            .where(
                Document.deleted_at.is_(None),
                DocumentChunk.deleted_at.is_(None),
            )
            .options(
                selectinload(Document.pages),
                selectinload(Document.chunks),
                with_loader_criteria(DocumentPage, DocumentPage.deleted_at.is_(None)),
                with_loader_criteria(DocumentChunk, DocumentChunk.deleted_at.is_(None)),
            )
            .order_by(Document.created_at.asc())
            .distinct()
            .limit(limit)
            .offset(offset)
        )
        if missing_only:
            stmt = stmt.where(
                or_(
                    DocumentChunk.doc_group.is_(None),
                    DocumentChunk.chunk_level.is_(None),
                    DocumentChunk.section_role.is_(None),
                    DocumentChunk.chunk_confidence.is_(None),
                )
            )
        return list(self.db.scalars(stmt))

    def update_chunk_metadata_for_document(
        self,
        *,
        document_id: str,
        chunk_payloads: list[dict[str, Any]],
    ) -> tuple[int, int]:
        payload_by_index = {index: payload for index, payload in enumerate(chunk_payloads)}
        updated = 0
        skipped = 0

        for chunk in self.list_chunks_for_document(document_id):
            chunk_payload = payload_by_index.get(chunk.chunk_index)
            if chunk_payload is None:
                self._apply_fallback_chunk_metadata(chunk)
                self.db.add(chunk)
                skipped += 1
                continue
            self._apply_chunk_metadata(chunk, chunk_payload)
            if not chunk.section_title:
                chunk.section_title = _clean_optional_string(chunk_payload.get("section_title"), 512)
            self.db.add(chunk)
            updated += 1

        self.db.flush()
        return updated, skipped

    def replace_chunks_for_document(
        self,
        *,
        document_id: str,
        chunks: list[dict[str, Any]],
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
            self._apply_chunk_metadata(chunk, chunk_payload)
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
        business_type: str | None = None,
        document_number: str | None = None,
        issued_date: date | None = None,
        doc_group: str | None = None,
        section_role: str | None = None,
        requires_review: bool | None = None,
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
        stmt = self._apply_chunk_search_filters(
            stmt,
            document_type=document_type,
            department_id=department_id,
            business_type=business_type,
            document_number=document_number,
            issued_date=issued_date,
            doc_group=doc_group,
            section_role=section_role,
            requires_review=requires_review,
        )
        return list(self.db.scalars(stmt))

    def list_matching_chunk_ids(
        self,
        *,
        chunk_ids: list[str],
        document_type: str | None = None,
        department_id: str | None = None,
        business_type: str | None = None,
        document_number: str | None = None,
        issued_date: date | None = None,
        doc_group: str | None = None,
        section_role: str | None = None,
        requires_review: bool | None = None,
    ) -> set[str]:
        if not chunk_ids:
            return set()
        stmt = (
            select(DocumentChunk.id)
            .join(Document)
            .where(
                DocumentChunk.id.in_(chunk_ids),
                DocumentChunk.deleted_at.is_(None),
                Document.deleted_at.is_(None),
            )
        )
        stmt = self._apply_chunk_search_filters(
            stmt,
            document_type=document_type,
            department_id=department_id,
            business_type=business_type,
            document_number=document_number,
            issued_date=issued_date,
            doc_group=doc_group,
            section_role=section_role,
            requires_review=requires_review,
        )
        return set(self.db.scalars(stmt))

    def _apply_chunk_search_filters(
        self,
        stmt,
        *,
        document_type: str | None,
        department_id: str | None,
        business_type: str | None,
        document_number: str | None,
        issued_date: date | None,
        doc_group: str | None,
        section_role: str | None,
        requires_review: bool | None,
    ):
        if document_type is not None:
            stmt = stmt.where(Document.document_type == document_type)
        if department_id is not None:
            stmt = stmt.where(Document.department_id == department_id)
        if business_type is not None:
            stmt = stmt.where(Document.business_type == business_type)
        if document_number is not None:
            stmt = stmt.where(Document.document_number == document_number)
        if issued_date is not None:
            stmt = stmt.where(Document.issued_date == issued_date)
        if doc_group is not None:
            stmt = stmt.where(DocumentChunk.doc_group == doc_group)
        if section_role is not None:
            stmt = stmt.where(DocumentChunk.section_role == section_role)
        if requires_review is not None:
            stmt = stmt.where(DocumentChunk.requires_review == requires_review)
        return stmt

    def update_chunk_qdrant_point_id(self, chunk: DocumentChunk, point_id: str) -> DocumentChunk:
        chunk.qdrant_point_id = point_id
        self.db.add(chunk)
        self.db.flush()
        return chunk

    def _apply_chunk_metadata(self, chunk: DocumentChunk, chunk_payload: dict[str, Any]) -> None:
        metadata = chunk_payload.get("chunk_metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        section_path = metadata.get("section_path")
        chunk.doc_group = _clean_optional_string(metadata.get("doc_group"), 8)
        chunk.chunk_level = _clean_optional_string(metadata.get("chunk_level"), 32)
        chunk.section_role = _clean_optional_string(metadata.get("section_role"), 64)
        chunk.section_path = [str(item) for item in section_path] if isinstance(section_path, list) else None
        chunk.chunk_confidence = _optional_float(metadata.get("confidence"))
        chunk.requires_review = bool(metadata.get("requires_review", False))

    def _apply_fallback_chunk_metadata(self, chunk: DocumentChunk) -> None:
        chunk.doc_group = chunk.doc_group or "E"
        chunk.chunk_level = chunk.chunk_level or "paragraph"
        chunk.section_role = chunk.section_role or "unknown"
        chunk.section_path = chunk.section_path or ([chunk.section_title] if chunk.section_title else [])
        chunk.chunk_confidence = chunk.chunk_confidence if chunk.chunk_confidence is not None else 0.0
        chunk.requires_review = True


def _clean_optional_string(value: Any, max_length: int) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text[:max_length] if text else None


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class OCRJobRepository:
    def __init__(self, db: Session):
        self.db = db

    ACTIVE_STATUSES = {"pending", "ocr_running"}

    def create_job(
        self,
        document_id: str,
        *,
        job_type: str = "ocr",
        reason: str | None = None,
        max_attempts: int = 3,
    ) -> OCRJob:
        job = OCRJob(
            document_id=document_id,
            job_type=job_type,
            reason=reason,
            status="pending",
            max_attempts=max_attempts,
        )
        self.db.add(job)
        self.db.flush()
        return job

    def get_next_pending_job(self) -> OCRJob | None:
        now = datetime.now(timezone.utc)
        stmt = (
            select(OCRJob)
            .where(
                OCRJob.status == "pending",
                OCRJob.deleted_at.is_(None),
                or_(OCRJob.next_run_at.is_(None), OCRJob.next_run_at <= now),
            )
            .order_by(OCRJob.created_at.asc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def claim_next_pending_job(self) -> OCRJob | None:
        now = datetime.now(timezone.utc)
        stmt = (
            select(OCRJob)
            .where(
                OCRJob.status == "pending",
                OCRJob.deleted_at.is_(None),
                or_(OCRJob.next_run_at.is_(None), OCRJob.next_run_at <= now),
            )
            .order_by(OCRJob.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        job = self.db.scalar(stmt)
        if job is None:
            return None

        job.status = "ocr_running"
        job.attempts += 1
        job.started_at = now
        job.next_run_at = None
        job.failed_reason = None
        job.error_message = None
        self.db.add(job)
        self.db.flush()
        return job

    def get_job(self, job_id: str) -> OCRJob | None:
        return self.db.get(OCRJob, job_id)

    def has_active_job(self, document_id: str) -> bool:
        stmt = (
            select(OCRJob.id)
            .where(
                OCRJob.document_id == document_id,
                OCRJob.deleted_at.is_(None),
                OCRJob.status.in_(self.ACTIVE_STATUSES),
            )
            .limit(1)
        )
        return self.db.scalar(stmt) is not None

    def count_jobs_by_status(self, status: str) -> int:
        stmt = select(func.count()).select_from(OCRJob).where(OCRJob.status == status, OCRJob.deleted_at.is_(None))
        return int(self.db.scalar(stmt) or 0)

    def count_pending_jobs_ready(self) -> int:
        now = datetime.now(timezone.utc)
        stmt = (
            select(func.count())
            .select_from(OCRJob)
            .where(
                OCRJob.status == "pending",
                OCRJob.deleted_at.is_(None),
                or_(OCRJob.next_run_at.is_(None), OCRJob.next_run_at <= now),
            )
        )
        return int(self.db.scalar(stmt) or 0)

    def count_pending_jobs_delayed(self) -> int:
        now = datetime.now(timezone.utc)
        stmt = (
            select(func.count())
            .select_from(OCRJob)
            .where(
                OCRJob.status == "pending",
                OCRJob.deleted_at.is_(None),
                OCRJob.next_run_at.is_not(None),
                OCRJob.next_run_at > now,
            )
        )
        return int(self.db.scalar(stmt) or 0)
