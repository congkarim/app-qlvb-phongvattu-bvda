from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.document import (
    DocumentDetailRead,
    DocumentMetadataUpdateRequest,
    DocumentRead,
    MultiFileUploadResponse,
    ReorderDocumentFilesRequest,
    ReprocessDocumentRequest,
    ReprocessDocumentResponse,
    SourceFileMutationResponse,
    UploadResponse,
)
from app.services.document_service import (
    DocumentBusyError,
    DocumentFileNotFoundError,
    DocumentFileOperationError,
    DocumentNotFoundError,
    DocumentService,
)


router = APIRouter(prefix="/documents", tags=["documents"], dependencies=[Depends(get_current_user)])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    document_number: str | None = Form(default=None),
    issued_date: date | None = Form(default=None),
    issuing_agency: str | None = Form(default=None),
    business_type: str | None = Form(default=None),
    document_type: str = Query(default="document"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadResponse:
    document, ocr_job = DocumentService(db).upload(
        file=file,
        title=title,
        document_type=document_type,
        document_number=document_number,
        issued_date=issued_date,
        issuing_agency=issuing_agency,
        business_type=business_type,
        actor=current_user,
    )
    return UploadResponse(document=document, ocr_job=ocr_job)


@router.post("/upload/multi-file", response_model=MultiFileUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_multi_file_document(
    files: list[UploadFile] = File(...),
    title: str = Form(...),
    document_type: str = Form(default="document"),
    document_number: str | None = Form(default=None),
    issued_date: date | None = Form(default=None),
    issuing_agency: str | None = Form(default=None),
    business_type: str | None = Form(default=None),
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
        document_number=document_number,
        issued_date=issued_date,
        issuing_agency=issuing_agency,
        business_type=business_type,
        actor=current_user,
    )
    return MultiFileUploadResponse(document=document, files=document_files, ocr_job=ocr_job)


@router.post("/upload/zip", response_model=MultiFileUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_zip_document(
    zip_file: UploadFile = File(...),
    title: str = Form(...),
    document_type: str = Form(default="document"),
    document_number: str | None = Form(default=None),
    issued_date: date | None = Form(default=None),
    issuing_agency: str | None = Form(default=None),
    business_type: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MultiFileUploadResponse:
    if not title.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Document title is required")
    try:
        document, document_files, ocr_job = DocumentService(db).upload_zip(
            title=title,
            zip_file=zip_file,
            document_type=document_type,
            document_number=document_number,
            issued_date=issued_date,
            issuing_agency=issuing_agency,
            business_type=business_type,
            actor=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return MultiFileUploadResponse(document=document, files=document_files, ocr_job=ocr_job)


@router.get("", response_model=list[DocumentRead])
def list_documents(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, max_length=200),
    document_type: str | None = Query(default=None, max_length=64),
    business_type: str | None = Query(default=None, max_length=64),
    status_filter: str | None = Query(default=None, alias="status", max_length=64),
    sort_by: str = Query(default="created_at", pattern="^(created_at|updated_at|issued_date|title|status|document_type|business_type)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> list[DocumentRead]:
    return DocumentService(db).list_documents(
        limit=limit,
        offset=offset,
        query=q,
        status=status_filter,
        document_type=document_type,
        business_type=business_type,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.post("/{document_id}/files", response_model=SourceFileMutationResponse, status_code=status.HTTP_202_ACCEPTED)
def add_document_source_files(
    document_id: str,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SourceFileMutationResponse:
    try:
        document, document_files, ocr_job = DocumentService(db).add_source_files(
            document_id,
            files,
            actor=current_user,
        )
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    except DocumentBusyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except DocumentFileOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return SourceFileMutationResponse(document=document, files=document_files, ocr_job=ocr_job)


@router.patch("/{document_id}/files/order", response_model=SourceFileMutationResponse, status_code=status.HTTP_202_ACCEPTED)
def reorder_document_source_files(
    document_id: str,
    payload: ReorderDocumentFilesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SourceFileMutationResponse:
    try:
        document, document_files, ocr_job = DocumentService(db).reorder_source_files(
            document_id,
            file_ids=payload.file_ids,
            actor=current_user,
        )
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    except DocumentBusyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except DocumentFileOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return SourceFileMutationResponse(document=document, files=document_files, ocr_job=ocr_job)


@router.delete("/{document_id}/files/{document_file_id}", response_model=SourceFileMutationResponse, status_code=status.HTTP_202_ACCEPTED)
def delete_document_source_file(
    document_id: str,
    document_file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SourceFileMutationResponse:
    try:
        document, document_files, ocr_job = DocumentService(db).delete_source_file(
            document_id,
            document_file_id,
            actor=current_user,
        )
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    except DocumentFileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source file not found")
    except DocumentBusyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except DocumentFileOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return SourceFileMutationResponse(document=document, files=document_files, ocr_job=ocr_job)


@router.get("/{document_id}", response_model=DocumentDetailRead)
def get_document(document_id: str, db: Session = Depends(get_db)) -> DocumentDetailRead:
    document = DocumentService(db).get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.patch("/{document_id}/metadata", response_model=DocumentRead)
def update_document_metadata(
    document_id: str,
    payload: DocumentMetadataUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentRead:
    try:
        return DocumentService(db).update_metadata(
            document_id,
            title=payload.title,
            document_number=payload.document_number,
            issued_date=payload.issued_date,
            issuing_agency=payload.issuing_agency,
            business_type=payload.business_type,
            actor=current_user,
        )
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


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
