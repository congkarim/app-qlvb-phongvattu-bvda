import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.document_repository import DocumentRepository, OCRJobRepository


class DocumentNotFoundError(ValueError):
    pass


class DocumentBusyError(RuntimeError):
    pass


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_logs = AuditLogRepository(db)
        self.documents = DocumentRepository(db)
        self.ocr_jobs = OCRJobRepository(db)
        self.settings = get_settings()

    def upload(self, file: UploadFile, document_type: str = "document", *, actor: User | None = None):
        upload_dir = Path(self.settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid4()}_{file.filename}"
        file_path = upload_dir / stored_name

        with file_path.open("wb") as output:
            shutil.copyfileobj(file.file, output)

        document = self.documents.create_document(
            title=file.filename or stored_name,
            original_filename=file.filename or stored_name,
            file_path=str(file_path),
            content_type=file.content_type,
            document_type=document_type,
        )
        ocr_job = self.ocr_jobs.create_job(document.id)
        self.documents.update_status(document, "ocr_pending")
        self.audit_logs.create(
            action="document.upload",
            entity_type="document",
            entity_id=document.id,
            actor_user_id=actor.id if actor else None,
            metadata={
                "filename": document.original_filename,
                "content_type": document.content_type,
                "document_type": document.document_type,
                "ocr_job_id": ocr_job.id,
            },
        )
        self.db.commit()
        self.db.refresh(document)
        self.db.refresh(ocr_job)
        return document, ocr_job

    def list_documents(self, limit: int = 50, offset: int = 0):
        return self.documents.list_documents(limit=limit, offset=offset)

    def get_document(self, document_id: str):
        return self.documents.get_document(document_id)

    def request_reprocess(self, document_id: str, *, reason: str | None = None, actor: User | None = None):
        document = self.documents.get_document(document_id)
        if document is None:
            raise DocumentNotFoundError(f"Document not found: {document_id}")
        if self.ocr_jobs.has_active_job(document_id):
            raise DocumentBusyError(f"Document already has an active OCR job: {document_id}")

        previous_status = document.status
        ocr_job = self.ocr_jobs.create_job(document.id, job_type="reprocess", reason=reason)
        self.documents.update_status(document, "reprocess_pending")
        self.audit_logs.create(
            action="document.reprocess_requested",
            entity_type="document",
            entity_id=document.id,
            actor_user_id=actor.id if actor else None,
            metadata={
                "reason": reason,
                "ocr_job_id": ocr_job.id,
                "previous_status": previous_status,
            },
        )
        self.db.commit()
        self.db.refresh(document)
        self.db.refresh(ocr_job)
        return document, ocr_job
