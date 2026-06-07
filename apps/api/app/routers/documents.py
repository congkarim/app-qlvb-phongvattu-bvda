from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.document import (
    DocumentDetailRead,
    DocumentChunkRead,
    DocumentListResponse,
    DocumentMetadataUpdateRequest,
    DocumentRead,
    MultiFileUploadResponse,
    ReorderDocumentFilesRequest,
    ReprocessDocumentRequest,
    ReprocessDocumentResponse,
    ReviewQueueResponse,
    SourceFileMutationResponse,
    UploadResponse,
)
from app.schemas.onboarding import OnboardingSuggestionResponse
from app.schemas.document_relation import (
    DocumentRelationCreateRequest,
    DocumentRelationOutgoingRead,
    DocumentRelationsResponse,
    RelationSuggestionsResponse,
)
from app.services.module_onboarding_service import ModuleOnboardingService
from app.repositories.document_repository import DocumentRepository
from app.services.document_relation_service import (
    DocumentRelationAlreadyExistsError,
    DocumentRelationNotFoundError,
    DocumentRelationOperationError,
    DocumentRelationService,
)
from app.services.document_relation_suggestion_service import (
    DocumentRelationSuggestionNotFoundError,
    DocumentRelationSuggestionService,
)
from app.services.document_service import (
    DocumentBusyError,
    DocumentChunkNotFoundError,
    DocumentFileNotFoundError,
    DocumentFileOperationError,
    DocumentNotFoundError,
    DocumentService,
    DocumentSourceFileMissingError,
    UploadTooLargeError,
    UploadTooManyFilesError,
)


router = APIRouter(prefix="/documents", tags=["documents"], dependencies=[Depends(get_current_user)])


def _raise_upload_error(exc: Exception) -> None:
    if isinstance(exc, UploadTooLargeError):
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(exc)) from exc
    if isinstance(exc, UploadTooManyFilesError):
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    raise exc


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
    try:
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
    except (UploadTooLargeError, UploadTooManyFilesError, ValueError) as exc:
        _raise_upload_error(exc)
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

    try:
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
    except (UploadTooLargeError, UploadTooManyFilesError, ValueError) as exc:
        _raise_upload_error(exc)
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
    except (UploadTooLargeError, UploadTooManyFilesError, ValueError) as exc:
        _raise_upload_error(exc)
    return MultiFileUploadResponse(document=document, files=document_files, ocr_job=ocr_job)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, max_length=200),
    document_type: str | None = Query(default=None, max_length=64),
    business_type: str | None = Query(default=None, max_length=64),
    missing_module_metadata: bool | None = Query(default=None),
    has_relations: bool | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status", max_length=64),
    sort_by: str = Query(default="created_at", pattern="^(created_at|updated_at|issued_date|title|status|document_type|business_type)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    return DocumentService(db).list_documents(
        limit=limit,
        offset=offset,
        query=q,
        status=status_filter,
        document_type=document_type,
        business_type=business_type,
        missing_module_metadata=missing_module_metadata,
        has_relations=has_relations,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.post("/{document_id}/files", response_model=SourceFileMutationResponse, status_code=status.HTTP_202_ACCEPTED)
def add_document_source_files(
    document_id: str,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
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
    except (UploadTooLargeError, UploadTooManyFilesError) as exc:
        _raise_upload_error(exc)
    return SourceFileMutationResponse(document=document, files=document_files, ocr_job=ocr_job)


@router.patch("/{document_id}/files/order", response_model=SourceFileMutationResponse, status_code=status.HTTP_202_ACCEPTED)
def reorder_document_source_files(
    document_id: str,
    payload: ReorderDocumentFilesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
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
    current_user: User = Depends(require_admin),
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


@router.get("/{document_id}/files/{document_file_id}/download", response_class=FileResponse)
def download_document_source_file(
    document_id: str,
    document_file_id: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    try:
        document_file, file_path = DocumentService(db).get_source_file_for_download(
            document_id=document_id,
            document_file_id=document_file_id,
        )
    except DocumentFileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source file not found")
    except DocumentSourceFileMissingError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source file missing")

    return FileResponse(
        path=file_path,
        media_type=document_file.content_type or "application/octet-stream",
        filename=document_file.original_filename,
        content_disposition_type="inline",
    )


@router.get("/chunks/review-queue", response_model=ReviewQueueResponse)
def list_review_queue_chunks(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    section_role: str | None = Query(default=None, max_length=64),
    document_id: str | None = Query(default=None, max_length=64),
    max_confidence: float | None = Query(default=None, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ReviewQueueResponse:
    return DocumentService(db).list_review_queue_chunks(
        limit=limit,
        offset=offset,
        section_role=section_role,
        document_id=document_id,
        max_confidence=max_confidence,
    )


@router.get("/{document_id}/onboarding-suggestions", response_model=OnboardingSuggestionResponse)
def get_document_onboarding_suggestions(
    document_id: str,
    db: Session = Depends(get_db),
) -> OnboardingSuggestionResponse:
    suggestion = ModuleOnboardingService(db).get_suggestions(document_id)
    if suggestion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return OnboardingSuggestionResponse(**suggestion)


@router.get("/{document_id}/relation-suggestions", response_model=RelationSuggestionsResponse)
def list_document_relation_suggestions(
    document_id: str,
    db: Session = Depends(get_db),
) -> RelationSuggestionsResponse:
    document = DocumentRepository(db).get_document(document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.status != "searchable":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document is not searchable",
        )
    try:
        return RelationSuggestionsResponse(
            **DocumentRelationSuggestionService(db).suggest_relations(document_id)
        )
    except DocumentRelationSuggestionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{document_id}/relations", response_model=DocumentRelationsResponse)
def list_document_relations(
    document_id: str,
    db: Session = Depends(get_db),
) -> DocumentRelationsResponse:
    try:
        return DocumentRelationsResponse(**DocumentRelationService(db).list_relations(document_id))
    except DocumentRelationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{document_id}/relations",
    response_model=DocumentRelationOutgoingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_document_relation(
    document_id: str,
    payload: DocumentRelationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentRelationOutgoingRead:
    try:
        return DocumentRelationOutgoingRead(
            **DocumentRelationService(db).create_relation(
                document_id=document_id,
                values=payload.model_dump(),
                actor=current_user,
            )
        )
    except DocumentRelationAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except DocumentRelationOperationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except DocumentRelationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


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
            document_type=payload.document_type,
            classification_confidence=payload.classification_confidence,
            document_number=payload.document_number,
            document_symbol=payload.document_symbol,
            issued_date=payload.issued_date,
            issued_place=payload.issued_place,
            issuing_agency=payload.issuing_agency,
            excerpt=payload.excerpt,
            recipient=payload.recipient,
            signer_name=payload.signer_name,
            signer_title=payload.signer_title,
            seals_present=payload.seals_present,
            attachment_present=payload.attachment_present,
            page_count=payload.page_count,
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
    current_user: User = Depends(require_admin),
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


@router.patch("/{document_id}/chunks/{chunk_id}/reviewed", response_model=DocumentChunkRead)
def mark_document_chunk_reviewed(
    document_id: str,
    chunk_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> DocumentChunkRead:
    try:
        return DocumentService(db).mark_chunk_reviewed(
            document_id=document_id,
            chunk_id=chunk_id,
            actor=current_user,
        )
    except DocumentChunkNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")
