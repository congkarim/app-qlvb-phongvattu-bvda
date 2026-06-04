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

    def upload(
        self,
        file: UploadFile,
        document_type: str = "document",
        *,
        title: str | None = None,
        actor: User | None = None,
    ):
        upload_dir = Path(self.settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_name, file_path, file_size = self._save_upload_file(file, upload_dir)
        original_filename = file.filename or stored_name

        document_title = self._normalize_title(title) or self._title_from_filename(original_filename)

        document = self.documents.create_document(
            title=document_title,
            original_filename=original_filename,
            file_path=str(file_path),
            content_type=file.content_type,
            document_type=document_type,
        )
        document_file = self.documents.create_file(
            document_id=document.id,
            original_filename=original_filename,
            file_path=str(file_path),
            content_type=file.content_type,
            file_size=file_size,
            file_order=0,
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
                "document_file_ids": [document_file.id],
                "file_count": 1,
                "ocr_job_id": ocr_job.id,
            },
        )
        self.db.commit()
        self.db.refresh(document)
        self.db.refresh(ocr_job)
        return document, ocr_job

    def upload_multi_file(
        self,
        *,
        title: str,
        files: list[UploadFile],
        document_type: str = "document",
        actor: User | None = None,
    ):
        document_title = self._normalize_title(title)
        if not document_title:
            raise ValueError("Document title is required for multi-file upload")
        if not files:
            raise ValueError("At least one source file is required")

        upload_dir = Path(self.settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        saved_files = []
        for file in files:
            stored_name, file_path, file_size = self._save_upload_file(file, upload_dir)
            saved_files.append(
                {
                    "original_filename": file.filename or stored_name,
                    "file_path": str(file_path),
                    "content_type": file.content_type,
                    "file_size": file_size,
                }
            )

        first_file = saved_files[0]
        document = self.documents.create_document(
            title=document_title,
            original_filename=str(first_file["original_filename"]),
            file_path=str(first_file["file_path"]),
            content_type=first_file["content_type"],
            document_type=document_type,
        )

        document_files = [
            self.documents.create_file(
                document_id=document.id,
                original_filename=str(saved_file["original_filename"]),
                file_path=str(saved_file["file_path"]),
                content_type=saved_file["content_type"],
                file_size=int(saved_file["file_size"]),
                file_order=file_order,
            )
            for file_order, saved_file in enumerate(saved_files)
        ]
        ocr_job = self.ocr_jobs.create_job(document.id)
        self.documents.update_status(document, "ocr_pending")
        self.audit_logs.create(
            action="document.upload",
            entity_type="document",
            entity_id=document.id,
            actor_user_id=actor.id if actor else None,
            metadata={
                "title": document.title,
                "document_type": document.document_type,
                "file_count": len(document_files),
                "files": [
                    {
                        "id": document_file.id,
                        "filename": document_file.original_filename,
                        "file_order": document_file.file_order,
                        "content_type": document_file.content_type,
                        "file_size": document_file.file_size,
                    }
                    for document_file in document_files
                ],
                "ocr_job_id": ocr_job.id,
            },
        )
        self.db.commit()
        self.db.refresh(document)
        for document_file in document_files:
            self.db.refresh(document_file)
        self.db.refresh(ocr_job)
        return document, document_files, ocr_job

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

    def _save_upload_file(self, file: UploadFile, upload_dir: Path) -> tuple[str, Path, int]:
        safe_filename = Path(file.filename or "uploaded_file").name
        stored_name = f"{uuid4()}_{safe_filename}"
        file_path = upload_dir / stored_name

        with file_path.open("wb") as output:
            shutil.copyfileobj(file.file, output)

        return stored_name, file_path, file_path.stat().st_size

    def _normalize_title(self, title: str | None) -> str | None:
        if title is None:
            return None
        normalized = " ".join(title.strip().split())
        return normalized or None

    def _title_from_filename(self, filename: str) -> str:
        stem = Path(filename).stem.strip()
        title = " ".join(stem.replace("_", " ").replace("-", " ").split())
        return title or filename
