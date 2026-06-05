from app.core.config import get_settings
from app.models.document import Document, DocumentChunk
from app.services.ocr_chunking.normalizer import normalize_for_detection


def build_qdrant_payload(document: Document, chunk: DocumentChunk) -> dict:
    settings = get_settings()
    section_path = chunk.section_path if isinstance(chunk.section_path, list) else []
    contains_appendix = chunk.section_role == "appendix" or (
        bool(section_path) and normalize_for_detection(str(section_path[0])).startswith("phu luc")
    )
    return {
        "document_id": document.id,
        "chunk_id": chunk.id,
        "text": chunk.text,
        "title": document.title,
        "document_type": document.document_type,
        "document_number": document.document_number,
        "issued_date": document.issued_date.isoformat() if document.issued_date else None,
        "issuing_agency": document.issuing_agency,
        "excerpt": document.excerpt,
        "recipient": document.recipient,
        "signer_name": document.signer_name,
        "business_type": document.business_type,
        "department_id": document.department_id,
        "page_from": chunk.page_from,
        "page_to": chunk.page_to,
        "content_hash": chunk.content_hash,
        "chunking_backend": settings.chunking_backend,
        "doc_group": chunk.doc_group,
        "chunk_level": chunk.chunk_level,
        "section_role": chunk.section_role,
        "section_title": chunk.section_title,
        "section_path": section_path,
        "chunk_confidence": chunk.chunk_confidence,
        "contains_appendix": contains_appendix,
        "requires_review": chunk.requires_review,
    }
