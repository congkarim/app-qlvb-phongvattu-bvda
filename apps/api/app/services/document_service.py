import zipfile
from datetime import date, datetime, timezone
from mimetypes import guess_type
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.document_relation_repository import DocumentRelationRepository
from app.repositories.document_repository import DocumentRepository, OCRJobRepository
from app.schemas.document import DocumentListItemRead
from app.services.module_onboarding_service import batch_missing_module_metadata_flags
from app.services.chunk_payload import build_qdrant_payload
from app.services.document_classifier_service import DOCUMENT_TYPE_LABELS
from app.services.qdrant_service import QdrantService


class DocumentNotFoundError(ValueError):
    pass


class DocumentBusyError(RuntimeError):
    pass


class DocumentFileNotFoundError(ValueError):
    pass


class DocumentFileOperationError(ValueError):
    pass


class DocumentChunkNotFoundError(ValueError):
    pass


class DocumentSourceFileMissingError(FileNotFoundError):
    pass


class UploadTooLargeError(ValueError):
    pass


class UploadTooManyFilesError(ValueError):
    pass


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_logs = AuditLogRepository(db)
        self.documents = DocumentRepository(db)
        self.ocr_jobs = OCRJobRepository(db)
        self.qdrant = QdrantService()
        self.settings = get_settings()

    def upload(
        self,
        file: UploadFile,
        document_type: str = "document",
        *,
        title: str | None = None,
        document_number: str | None = None,
        issued_date: date | None = None,
        issuing_agency: str | None = None,
        business_type: str | None = None,
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
            document_number=self._normalize_title(document_number),
            issued_date=issued_date,
            issuing_agency=self._normalize_title(issuing_agency),
            business_type=self._normalize_title(business_type),
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
                "document_number": document.document_number,
                "issued_date": document.issued_date.isoformat() if document.issued_date else None,
                "issuing_agency": document.issuing_agency,
                "business_type": document.business_type,
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
        document_number: str | None = None,
        issued_date: date | None = None,
        issuing_agency: str | None = None,
        business_type: str | None = None,
        actor: User | None = None,
    ):
        document_title = self._normalize_title(title)
        if not document_title:
            raise ValueError("Document title is required for multi-file upload")
        if not files:
            raise ValueError("At least one source file is required")
        self._validate_file_count(len(files))

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
            document_number=self._normalize_title(document_number),
            issued_date=issued_date,
            issuing_agency=self._normalize_title(issuing_agency),
            business_type=self._normalize_title(business_type),
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
                "document_number": document.document_number,
                "issued_date": document.issued_date.isoformat() if document.issued_date else None,
                "issuing_agency": document.issuing_agency,
                "business_type": document.business_type,
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

    def upload_zip(
        self,
        *,
        title: str,
        zip_file: UploadFile,
        document_type: str = "document",
        document_number: str | None = None,
        issued_date: date | None = None,
        issuing_agency: str | None = None,
        business_type: str | None = None,
        actor: User | None = None,
    ):
        document_title = self._normalize_title(title)
        if not document_title:
            raise ValueError("Document title is required for zip upload")
        if not (zip_file.filename or "").lower().endswith(".zip"):
            raise ValueError("Only .zip files are supported")

        upload_dir = Path(self.settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        _, zip_path, _ = self._save_upload_file(
            zip_file,
            upload_dir,
            max_size_bytes=self.settings.upload_max_zip_size_bytes,
        )
        saved_files = self._extract_zip_source_files(zip_path, upload_dir)
        if not saved_files:
            raise ValueError("Zip file does not contain source files")

        document = self._create_document_with_saved_files(
            title=document_title,
            document_type=document_type,
            saved_files=saved_files,
            document_number=self._normalize_title(document_number),
            issued_date=issued_date,
            issuing_agency=self._normalize_title(issuing_agency),
            business_type=self._normalize_title(business_type),
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
            action="document.upload_zip",
            entity_type="document",
            entity_id=document.id,
            actor_user_id=actor.id if actor else None,
            metadata={
                "title": document.title,
                "zip_filename": zip_file.filename,
                "document_type": document.document_type,
                "document_number": document.document_number,
                "issued_date": document.issued_date.isoformat() if document.issued_date else None,
                "issuing_agency": document.issuing_agency,
                "business_type": document.business_type,
                "file_count": len(document_files),
                "files": self._document_file_metadata(document_files),
                "ocr_job_id": ocr_job.id,
            },
        )
        self.db.commit()
        self.db.refresh(document)
        for document_file in document_files:
            self.db.refresh(document_file)
        self.db.refresh(ocr_job)
        return document, document_files, ocr_job

    def list_documents(
        self,
        limit: int = 50,
        offset: int = 0,
        *,
        query: str | None = None,
        status: str | None = None,
        document_type: str | None = None,
        business_type: str | None = None,
        missing_module_metadata: bool | None = None,
        has_relations: bool | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ):
        normalized_query = self._normalize_title(query)
        normalized_status = self._normalize_title(status)
        normalized_document_type = self._normalize_title(document_type)
        normalized_business_type = self._normalize_title(business_type)
        items = self.documents.list_documents(
            limit=limit,
            offset=offset,
            query=normalized_query,
            status=normalized_status,
            document_type=normalized_document_type,
            business_type=normalized_business_type,
            missing_module_metadata=missing_module_metadata,
            has_relations=has_relations,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        total = self.documents.count_documents(
            query=normalized_query,
            status=normalized_status,
            document_type=normalized_document_type,
            business_type=normalized_business_type,
            missing_module_metadata=missing_module_metadata,
            has_relations=has_relations,
        )
        missing_flags = batch_missing_module_metadata_flags(self.db, items)
        relation_counts = DocumentRelationRepository(self.db).batch_count_active_for_documents(
            [item.id for item in items]
        )
        serialized_items = [
            DocumentListItemRead.model_validate(item).model_copy(
                update={
                    "missing_module_metadata": missing_flags.get(item.id, False),
                    "relation_count": relation_counts.get(item.id, 0),
                }
            )
            for item in items
        ]
        return {
            "items": serialized_items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_document(self, document_id: str):
        return self.documents.get_document(document_id)

    def list_review_queue_chunks(
        self,
        *,
        limit: int,
        offset: int,
        section_role: str | None = None,
        document_id: str | None = None,
        max_confidence: float | None = None,
    ) -> dict:
        normalized_section_role = self._normalize_title(section_role)
        normalized_document_id = self._normalize_title(document_id)
        chunks = self.documents.list_review_queue_chunks(
            limit=limit,
            offset=offset,
            section_role=normalized_section_role,
            document_id=normalized_document_id,
            max_confidence=max_confidence,
        )
        total = self.documents.count_review_queue_chunks(
            section_role=normalized_section_role,
            document_id=normalized_document_id,
            max_confidence=max_confidence,
        )
        return {
            "items": [self._review_queue_chunk_payload(chunk) for chunk in chunks],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_source_file_for_download(self, document_id: str, document_file_id: str):
        if not self._is_uuid(document_id) or not self._is_uuid(document_file_id):
            raise DocumentFileNotFoundError(f"Document source file not found: {document_file_id}")
        document_file = self.documents.get_active_file_for_document(
            document_id=document_id,
            document_file_id=document_file_id,
        )
        if document_file is None:
            raise DocumentFileNotFoundError(f"Document source file not found: {document_file_id}")

        file_path = Path(document_file.file_path)
        if not file_path.is_file():
            raise DocumentSourceFileMissingError(f"Document source file missing on disk: {document_file_id}")
        return document_file, file_path

    def update_metadata(
        self,
        document_id: str,
        *,
        title: str,
        document_type: str | None = None,
        classification_confidence: float | None = None,
        document_number: str | None = None,
        document_symbol: str | None = None,
        issued_date: date | None = None,
        issued_place: str | None = None,
        issuing_agency: str | None = None,
        excerpt: str | None = None,
        recipient: str | None = None,
        signer_name: str | None = None,
        signer_title: str | None = None,
        seals_present: bool | None = None,
        attachment_present: bool | None = None,
        page_count: int | None = None,
        business_type: str | None = None,
        actor: User | None = None,
    ):
        document = self.documents.get_document(document_id)
        if document is None:
            raise DocumentNotFoundError(f"Document not found: {document_id}")

        next_metadata = {
            "title": self._normalize_title(title),
            "document_type": self._normalize_document_type(document_type or document.document_type),
            "classification_confidence": classification_confidence,
            "document_number": self._normalize_title(document_number),
            "document_symbol": self._normalize_title(document_symbol),
            "issued_date": issued_date,
            "issued_place": self._normalize_title(issued_place),
            "issuing_agency": self._normalize_title(issuing_agency),
            "excerpt": self._normalize_long_text(excerpt),
            "recipient": self._normalize_long_text(recipient),
            "signer_name": self._normalize_title(signer_name),
            "signer_title": self._normalize_title(signer_title),
            "seals_present": seals_present,
            "attachment_present": attachment_present,
            "page_count": page_count,
            "metadata_source": "manual",
            "metadata_reviewed_at": datetime.now(timezone.utc),
            "business_type": self._normalize_title(business_type),
        }
        if not next_metadata["title"]:
            raise ValueError("Document title is required")

        previous_metadata = self._document_metadata(document)
        document = self.documents.update_metadata(document, **next_metadata)
        changed_fields = [
            key
            for key, previous_value in previous_metadata.items()
            if previous_value != self._serialize_metadata_value(next_metadata[key])
        ]
        self.audit_logs.create(
            action="document.metadata_updated",
            entity_type="document",
            entity_id=document.id,
            actor_user_id=actor.id if actor else None,
            metadata={
                "changed_fields": changed_fields,
                "previous": previous_metadata,
                "current": self._document_metadata(document),
            },
        )
        self.db.commit()
        self.db.refresh(document)
        return document

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

    def mark_chunk_reviewed(self, document_id: str, chunk_id: str, *, actor: User | None = None):
        chunk = self.documents.get_chunk_for_document(document_id=document_id, chunk_id=chunk_id)
        if chunk is None:
            raise DocumentChunkNotFoundError(f"Document chunk not found: {chunk_id}")

        was_requires_review = chunk.requires_review
        chunk = self.documents.mark_chunk_reviewed(chunk)
        if was_requires_review:
            self.audit_logs.create(
                action="document_chunk.reviewed",
                entity_type="document",
                entity_id=chunk.document_id,
                actor_user_id=actor.id if actor else None,
                metadata={
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "section_role": chunk.section_role,
                    "section_path": chunk.section_path or [],
                    "previous_requires_review": True,
                    "current_requires_review": False,
                },
            )

        point_id = chunk.qdrant_point_id or chunk.id
        self.qdrant.set_payload(
            point_id=point_id,
            payload=build_qdrant_payload(chunk.document, chunk),
        )
        self.db.commit()
        self.db.refresh(chunk)
        return chunk

    def add_source_files(
        self,
        document_id: str,
        files: list[UploadFile],
        *,
        actor: User | None = None,
    ):
        document = self._get_mutable_document(document_id)
        if not files:
            raise DocumentFileOperationError("At least one source file is required")
        self._validate_file_count(len(files))

        upload_dir = Path(self.settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        existing_files = self.documents.list_files_for_document(document.id)
        next_order = max((document_file.file_order for document_file in existing_files), default=-1) + 1

        document_files = []
        for offset, file in enumerate(files):
            stored_name, file_path, file_size = self._save_upload_file(file, upload_dir)
            document_files.append(
                self.documents.create_file(
                    document_id=document.id,
                    original_filename=file.filename or stored_name,
                    file_path=str(file_path),
                    content_type=file.content_type,
                    file_size=file_size,
                    file_order=next_order + offset,
                )
            )
        if not existing_files and document_files:
            self.documents.update_legacy_file_fields(document, document_files[0])

        ocr_job = self._create_source_file_reprocess_job(
            document=document,
            actor=actor,
            action="document.source_files_added",
            metadata={
                "file_count": len(document_files),
                "files": self._document_file_metadata(document_files),
            },
        )
        self.db.commit()
        self.db.refresh(document)
        for document_file in document_files:
            self.db.refresh(document_file)
        self.db.refresh(ocr_job)
        return document, self.documents.list_files_for_document(document.id), ocr_job

    def reorder_source_files(
        self,
        document_id: str,
        *,
        file_ids: list[str],
        actor: User | None = None,
    ):
        document = self._get_mutable_document(document_id)
        active_files = self.documents.list_files_for_document(document.id)
        active_ids = [document_file.id for document_file in active_files]
        if len(file_ids) != len(active_ids) or set(file_ids) != set(active_ids):
            raise DocumentFileOperationError("file_ids must include every active source file exactly once")

        by_id = {document_file.id: document_file for document_file in active_files}
        reordered_files = []
        for file_order, file_id in enumerate(file_ids):
            reordered_files.append(self.documents.update_file_order(by_id[file_id], file_order))

        self.documents.update_legacy_file_fields(document, reordered_files[0])
        ocr_job = self._create_source_file_reprocess_job(
            document=document,
            actor=actor,
            action="document.source_files_reordered",
            metadata={"file_ids": file_ids},
        )
        self.db.commit()
        self.db.refresh(document)
        for document_file in reordered_files:
            self.db.refresh(document_file)
        self.db.refresh(ocr_job)
        return document, self.documents.list_files_for_document(document.id), ocr_job

    def delete_source_file(
        self,
        document_id: str,
        document_file_id: str,
        *,
        actor: User | None = None,
    ):
        document = self._get_mutable_document(document_id)
        active_files = self.documents.list_files_for_document(document.id)
        if len(active_files) <= 1:
            raise DocumentFileOperationError("Cannot delete the last source file")

        document_file = self.documents.get_file_for_document(
            document_id=document.id,
            document_file_id=document_file_id,
        )
        if document_file is None:
            raise DocumentFileNotFoundError(f"Document source file not found: {document_file_id}")

        self.documents.soft_delete_file(document_file)
        remaining_files = self.documents.list_files_for_document(document.id)
        for file_order, remaining_file in enumerate(remaining_files):
            self.documents.update_file_order(remaining_file, file_order)
        self.documents.update_legacy_file_fields(document, remaining_files[0])

        ocr_job = self._create_source_file_reprocess_job(
            document=document,
            actor=actor,
            action="document.source_file_deleted",
            metadata={
                "deleted_file_id": document_file.id,
                "deleted_filename": document_file.original_filename,
                "remaining_file_count": len(remaining_files),
            },
        )
        self.db.commit()
        self.db.refresh(document)
        self.db.refresh(ocr_job)
        return document, self.documents.list_files_for_document(document.id), ocr_job

    def _save_upload_file(
        self,
        file: UploadFile,
        upload_dir: Path,
        *,
        max_size_bytes: int | None = None,
    ) -> tuple[str, Path, int]:
        safe_filename = Path(file.filename or "uploaded_file").name
        stored_name = f"{uuid4()}_{safe_filename}"
        file_path = upload_dir / stored_name
        limit = max_size_bytes if max_size_bytes is not None else self.settings.upload_max_file_size_bytes
        total = 0
        try:
            file.file.seek(0)
            with file_path.open("wb") as output:
                while True:
                    chunk = file.file.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > limit:
                        raise UploadTooLargeError(
                            f"File exceeds maximum upload size of {limit} bytes"
                        )
                    output.write(chunk)
        except Exception:
            if file_path.exists():
                file_path.unlink()
            raise
        return stored_name, file_path, total

    def _save_bytes_file(
        self,
        *,
        filename: str,
        content: bytes,
        upload_dir: Path,
        max_size_bytes: int | None = None,
    ) -> tuple[str, Path, int]:
        limit = max_size_bytes if max_size_bytes is not None else self.settings.upload_max_file_size_bytes
        if len(content) > limit:
            raise UploadTooLargeError(f"File exceeds maximum upload size of {limit} bytes")
        safe_filename = Path(filename or "uploaded_file").name
        stored_name = f"{uuid4()}_{safe_filename}"
        file_path = upload_dir / stored_name
        file_path.write_bytes(content)
        return stored_name, file_path, len(content)

    def _extract_zip_source_files(self, zip_path: Path, upload_dir: Path) -> list[dict[str, str | int | None]]:
        max_files = self.settings.upload_max_files_per_request
        max_file_size = self.settings.upload_max_file_size_bytes
        try:
            with zipfile.ZipFile(zip_path) as archive:
                source_files = []
                for member in archive.infolist():
                    if member.is_dir() or member.filename.startswith("__MACOSX/"):
                        continue
                    source_name = Path(member.filename).name
                    if not source_name:
                        continue
                    if len(source_files) >= max_files:
                        raise UploadTooManyFilesError(
                            f"Zip contains more than {max_files} source files"
                        )
                    if member.file_size > max_file_size:
                        raise UploadTooLargeError(
                            f"Zip member exceeds maximum upload size of {max_file_size} bytes"
                        )
                    content = archive.read(member)
                    if len(content) > max_file_size:
                        raise UploadTooLargeError(
                            f"Zip member exceeds maximum upload size of {max_file_size} bytes"
                        )
                    stored_name, file_path, file_size = self._save_bytes_file(
                        filename=source_name,
                        content=content,
                        upload_dir=upload_dir,
                        max_size_bytes=max_file_size,
                    )
                    content_type = guess_type(source_name)[0]
                    source_files.append(
                        {
                            "original_filename": source_name or stored_name,
                            "file_path": str(file_path),
                            "content_type": content_type,
                            "file_size": file_size,
                        }
                    )
                return source_files
        except zipfile.BadZipFile as exc:
            raise ValueError("Invalid zip file") from exc
        finally:
            if zip_path.exists():
                zip_path.unlink()

    def _validate_file_count(self, count: int) -> None:
        if count > self.settings.upload_max_files_per_request:
            raise UploadTooManyFilesError(
                f"Upload exceeds maximum file count of {self.settings.upload_max_files_per_request}"
            )

    def _create_document_with_saved_files(
        self,
        *,
        title: str,
        document_type: str,
        saved_files: list[dict[str, str | int | None]],
        document_number: str | None = None,
        issued_date: date | None = None,
        issuing_agency: str | None = None,
        business_type: str | None = None,
    ):
        first_file = saved_files[0]
        return self.documents.create_document(
            title=title,
            original_filename=str(first_file["original_filename"]),
            file_path=str(first_file["file_path"]),
            content_type=first_file["content_type"],
            document_type=document_type,
            document_number=document_number,
            issued_date=issued_date,
            issuing_agency=issuing_agency,
            business_type=business_type,
        )

    def _get_mutable_document(self, document_id: str):
        document = self.documents.get_document(document_id)
        if document is None:
            raise DocumentNotFoundError(f"Document not found: {document_id}")
        if self.ocr_jobs.has_active_job(document_id):
            raise DocumentBusyError(f"Document already has an active OCR job: {document_id}")
        return document

    def _create_source_file_reprocess_job(
        self,
        *,
        document,
        actor: User | None,
        action: str,
        metadata: dict,
    ):
        previous_status = document.status
        ocr_job = self.ocr_jobs.create_job(
            document.id,
            job_type="reprocess",
            reason="source files changed",
        )
        self.documents.update_status(document, "reprocess_pending")
        self.audit_logs.create(
            action=action,
            entity_type="document",
            entity_id=document.id,
            actor_user_id=actor.id if actor else None,
            metadata={
                **metadata,
                "ocr_job_id": ocr_job.id,
                "previous_status": previous_status,
            },
        )
        return ocr_job

    def _document_file_metadata(self, document_files) -> list[dict[str, str | int | None]]:
        return [
            {
                "id": document_file.id,
                "filename": document_file.original_filename,
                "file_order": document_file.file_order,
                "content_type": document_file.content_type,
                "file_size": document_file.file_size,
            }
            for document_file in document_files
        ]

    def _document_metadata(self, document) -> dict[str, object]:
        return {
            "title": document.title,
            "document_type": document.document_type,
            "classification_confidence": document.classification_confidence,
            "document_number": document.document_number,
            "document_symbol": document.document_symbol,
            "issued_date": document.issued_date.isoformat() if document.issued_date else None,
            "issued_place": document.issued_place,
            "issuing_agency": document.issuing_agency,
            "excerpt": document.excerpt,
            "recipient": document.recipient,
            "signer_name": document.signer_name,
            "signer_title": document.signer_title,
            "seals_present": document.seals_present,
            "attachment_present": document.attachment_present,
            "page_count": document.page_count,
            "metadata_source": document.metadata_source,
            "metadata_reviewed_at": document.metadata_reviewed_at.isoformat() if document.metadata_reviewed_at else None,
            "business_type": document.business_type,
        }

    def _review_queue_chunk_payload(self, chunk) -> dict:
        document = chunk.document
        return {
            "id": chunk.id,
            "document_id": chunk.document_id,
            "document_title": document.title,
            "document_number": document.document_number,
            "issued_date": document.issued_date,
            "business_type": document.business_type,
            "chunk_index": chunk.chunk_index,
            "text": chunk.text,
            "page_from": chunk.page_from,
            "page_to": chunk.page_to,
            "section_title": chunk.section_title,
            "doc_group": chunk.doc_group,
            "chunk_level": chunk.chunk_level,
            "section_role": chunk.section_role,
            "section_path": chunk.section_path,
            "chunk_confidence": chunk.chunk_confidence,
            "requires_review": chunk.requires_review,
            "created_at": chunk.created_at,
            "updated_at": chunk.updated_at,
        }

    def _serialize_metadata_value(self, value) -> str | None:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return value

    def _is_uuid(self, value: str) -> bool:
        try:
            UUID(value)
        except ValueError:
            return False
        return True

    def _normalize_title(self, title: str | None) -> str | None:
        if title is None:
            return None
        normalized = " ".join(title.strip().split())
        return normalized or None

    def _normalize_long_text(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = "\n".join(" ".join(line.strip().split()) for line in value.splitlines())
        normalized = "\n".join(line for line in normalized.splitlines() if line)
        return normalized or None

    def _normalize_document_type(self, value: str | None) -> str:
        normalized = self._normalize_title(value) or "UNKNOWN"
        if normalized not in DOCUMENT_TYPE_LABELS:
            return "UNKNOWN"
        return normalized

    def _title_from_filename(self, filename: str) -> str:
        stem = Path(filename).stem.strip()
        title = " ".join(stem.replace("_", " ").replace("-", " ").split())
        return title or filename
