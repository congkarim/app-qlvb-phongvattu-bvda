from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin


class Document(UUIDTimestampMixin, Base):
    __tablename__ = "documents"

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_type: Mapped[str] = mapped_column(String(64), nullable=False, default="document")
    classification_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    document_symbol: Mapped[str | None] = mapped_column(String(128), nullable=True)
    issued_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    issued_place: Mapped[str | None] = mapped_column(String(255), nullable=True)
    issuing_agency: Mapped[str | None] = mapped_column(String(255), nullable=True)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    recipient: Mapped[str | None] = mapped_column(Text, nullable=True)
    signer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signer_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seals_present: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    attachment_present: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    metadata_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    business_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="uploaded", index=True)
    department_id: Mapped[str | None] = mapped_column(ForeignKey("departments.id"), nullable=True)

    department: Mapped["Department | None"] = relationship(back_populates="documents")
    files: Mapped[list["DocumentFile"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    pages: Mapped[list["DocumentPage"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    ocr_jobs: Mapped[list["OCRJob"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentFile(UUIDTimestampMixin, Base):
    __tablename__ = "document_files"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    file_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending")

    document: Mapped[Document] = relationship(back_populates="files")

    __table_args__ = (
        Index("ix_document_files_document_order", "document_id", "file_order"),
    )


class DocumentPage(UUIDTimestampMixin, Base):
    __tablename__ = "document_pages"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending")

    document: Mapped[Document] = relationship(back_populates="pages")

    __table_args__ = (Index("ix_document_pages_document_page", "document_id", "page_number", unique=True),)


class DocumentChunk(UUIDTimestampMixin, Base):
    __tablename__ = "document_chunks"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page_from: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    qdrant_point_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    document: Mapped[Document] = relationship(back_populates="chunks")

    __table_args__ = (
        Index("ix_document_chunks_document_index", "document_id", "chunk_index", unique=True),
        Index("ix_document_chunks_hash", "content_hash"),
    )


class OCRJob(UUIDTimestampMixin, Base):
    __tablename__ = "ocr_jobs"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    job_type: Mapped[str] = mapped_column(String(64), nullable=False, default="ocr")
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    document: Mapped[Document] = relationship(back_populates="ocr_jobs")

    __table_args__ = (Index("ix_ocr_jobs_status_created", "status", "created_at"),)
