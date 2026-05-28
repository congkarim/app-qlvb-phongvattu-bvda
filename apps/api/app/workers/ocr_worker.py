import time
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.document import OCRJob
from app.repositories.document_repository import DocumentRepository, OCRJobRepository
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService


class OCRWorker:
    def __init__(self, db: Session):
        self.db = db
        self.documents = DocumentRepository(db)
        self.ocr_jobs = OCRJobRepository(db)
        self.chunking = ChunkingService()
        self.embeddings = EmbeddingService()
        self.qdrant = QdrantService()

    def run_once(self) -> bool:
        job = self.ocr_jobs.get_next_pending_job()
        if not job:
            return False

        self.process_job(job)
        return True

    def process_job(self, job: OCRJob) -> None:
        job.status = "ocr_running"
        job.attempts += 1
        job.started_at = datetime.now(timezone.utc)
        self.db.add(job)
        self.db.commit()

        try:
            document = self.documents.get_document(job.document_id)
            if not document:
                raise ValueError(f"Document not found: {job.document_id}")

            self.documents.update_status(document, "ocr_running")
            simulated_text = self._simulate_ocr_text(Path(document.file_path), document.original_filename)
            page = self.documents.create_page(
                document_id=document.id,
                page_number=1,
                text=simulated_text,
                confidence=0.99,
            )

            self.documents.update_status(document, "chunking")
            chunks = self.chunking.create_chunks(simulated_text)
            for chunk_index, chunk_payload in enumerate(chunks):
                chunk = self.documents.create_chunk(
                    document_id=document.id,
                    chunk_index=chunk_index,
                    text=str(chunk_payload["text"]),
                    content_hash=str(chunk_payload["content_hash"]),
                    page_from=page.page_number,
                    page_to=page.page_number,
                    section_title=chunk_payload["section_title"],
                )
                point_id = chunk.id
                vector = self.embeddings.embed(chunk.text)
                self.qdrant.upsert_chunk(
                    point_id=point_id,
                    vector=vector,
                    payload={
                        "document_id": document.id,
                        "chunk_id": chunk.id,
                        "text": chunk.text,
                        "title": document.title,
                        "document_type": document.document_type,
                        "department_id": document.department_id,
                        "page_from": chunk.page_from,
                        "page_to": chunk.page_to,
                    },
                )
                chunk.qdrant_point_id = point_id
                self.db.add(chunk)

            self.documents.update_status(document, "searchable")
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            self.db.add(job)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            job.status = "failed"
            job.error_message = str(exc)
            self.db.add(job)
            self.db.commit()
            raise

    def _simulate_ocr_text(self, file_path: Path, filename: str) -> str:
        extracted = ""
        if file_path.exists() and file_path.suffix.lower() in {".txt", ".md"}:
            extracted = file_path.read_text(encoding="utf-8", errors="ignore")

        if extracted.strip():
            return extracted

        return (
            f"Văn bản OCR mô phỏng từ file {filename}. "
            "Điều 1. Phạm vi áp dụng của tài liệu được ghi nhận để kiểm tra semantic search. "
            "Khoản 1 quy định quy trình tiếp nhận, xử lý, lưu trữ và tra cứu văn bản trong hệ thống nội bộ. "
            "Điều 2. Trách nhiệm thực hiện thuộc về các phòng ban liên quan theo metadata của hồ sơ."
        )


def run_forever(db_factory, poll_seconds: int = 5) -> None:
    while True:
        db = db_factory()
        try:
            processed = OCRWorker(db).run_once()
        finally:
            db.close()
        if not processed:
            time.sleep(poll_seconds)
