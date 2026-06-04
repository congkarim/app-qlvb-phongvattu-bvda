from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.document import (
    DocumentDetailRead,
    DocumentRead,
    MultiFileUploadResponse,
    ReprocessDocumentRequest,
    ReprocessDocumentResponse,
    UploadResponse,
)
from app.services.document_service import DocumentBusyError, DocumentNotFoundError, DocumentService


router = APIRouter(prefix="/documents", tags=["documents"], dependencies=[Depends(get_current_user)])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    document_type: str = Query(default="document"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadResponse:
    document, ocr_job = DocumentService(db).upload(
        file=file,
        title=title,
        document_type=document_type,
        actor=current_user,
    )
    return UploadResponse(document=document, ocr_job=ocr_job)


@router.post("/upload/multi-file", response_model=MultiFileUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_multi_file_document(
    files: list[UploadFile] = File(...),
    title: str = Form(...),
    document_type: str = Form(default="document"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MultiFileUploadResponse:
    if not title.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Document title is required")
    if not files:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="At least one source file is required")

    document, document_files, ocr_job = DocumentService(db).upload_multi_file(
        title=title,
        files=files,
        document_type=document_type,
        actor=current_user,
    )
    return MultiFileUploadResponse(document=document, files=document_files, ocr_job=ocr_job)


@router.get("", response_model=list[DocumentRead])
def list_documents(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[DocumentRead]:
    return DocumentService(db).list_documents(limit=limit, offset=offset)


@router.get("/{document_id}", response_model=DocumentDetailRead)
def get_document(document_id: str, db: Session = Depends(get_db)) -> DocumentDetailRead:
    document = DocumentService(db).get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.post("/{document_id}/reprocess", response_model=ReprocessDocumentResponse, status_code=status.HTTP_202_ACCEPTED)
def reprocess_document(
    document_id: str,
    payload: ReprocessDocumentRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReprocessDocumentResponse:
    try:
        document, ocr_job = DocumentService(db).request_reprocess(
            document_id,
            reason=payload.reason if payload else None,
            actor=current_user,
        )
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    except DocumentBusyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return ReprocessDocumentResponse(document=document, ocr_job=ocr_job)
