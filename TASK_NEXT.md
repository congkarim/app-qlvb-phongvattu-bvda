# Task Vừa Hoàn Thành: Tự Động Lưu Metadata Sau OCR

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-04

## Phạm Vi Đã Thực Hiện

Đã triển khai tự động phân loại văn bản hành chính và lưu metadata sau OCR theo skill
`.agents/skills/vn-admin-doc-ocr-classifier/`. Người dùng có thể xem metadata đã tự trích xuất trong
trang chi tiết, đối chiếu với OCR text/source file và sửa thủ công nếu trường nào sai.

Quy tắc đã chốt và đã kiểm tra:
- Nếu tài liệu đã được người dùng sửa metadata thủ công, reprocess không ghi đè metadata đó.
- Reprocess vẫn OCR lại pages/chunks/search index và ghi audit log kết quả auto extraction mới.
- Auto extraction chỉ ghi vào document khi metadata chưa được review/sửa thủ công.

## Kết Quả Chính

Backend/database:
- Thêm migration `0007_document_ocr_metadata`.
- Mở rộng bảng `documents` với:
  - `classification_confidence`
  - `document_symbol`
  - `issued_place`
  - `excerpt`
  - `recipient`
  - `signer_name`
  - `signer_title`
  - `seals_present`
  - `attachment_present`
  - `page_count`
  - `metadata_source`
  - `metadata_reviewed_at`
- `document_type` dùng nhãn hành chính chuẩn như `CV`, `QĐ`, `TB`, `UNKNOWN`.
- `business_type` vẫn giữ cho phân loại nghiệp vụ nội bộ.
- Thêm `DocumentClassifierService` rule-based/local, không dùng cloud service.
- OCR worker chạy luồng mới:
  - OCR/extract pages
  - lưu pages
  - auto classify/extract metadata
  - lưu metadata nếu chưa review thủ công
  - chunk
  - embedding
  - upsert Qdrant
- Qdrant payload được bổ sung metadata phục vụ search/filter.
- Thêm audit action `document.metadata_auto_extracted`.
- `PATCH /documents/{document_id}/metadata` nhận đủ field metadata mới và set `metadata_source=manual`,
  `metadata_reviewed_at=<now>`.

Frontend:
- Mở rộng `DocumentItem`, `DocumentDetail`, `DocumentMetadataUpdateInput`.
- Mở rộng `document.service.ts` để gửi đủ metadata field khi lưu thủ công.
- Trang `/documents/[id]` hiển thị và cho sửa:
  - loại văn bản hành chính
  - confidence
  - số văn bản, ký hiệu, ngày ban hành, địa danh, đơn vị ban hành
  - trích yếu, nơi nhận
  - người ký, chức vụ người ký
  - dấu, phụ lục/tệp kèm, số trang
  - nguồn metadata và thời điểm review
- Filter loại văn bản ở `/documents` dùng một nhóm nhãn hành chính phổ biến.

## Đã Kiểm Tra

```bash
docker compose config --quiet
docker compose run --rm --no-deps api python -m py_compile app/models/document.py app/schemas/document.py app/repositories/document_repository.py app/services/document_classifier_service.py app/services/document_service.py app/workers/ocr_worker.py app/routers/documents.py app/scripts/check_document_classifier.py alembic/versions/0007_document_ocr_metadata.py
docker compose run --rm --no-deps api python -m app.scripts.check_document_classifier
docker compose run --rm api alembic upgrade head
docker compose run --rm --no-deps web npm run build
docker compose up -d api worker web
```

Kết quả:
- Backend compile pass.
- Classifier checks pass cho `CV`, `QĐ`, `TB`, `BB`, `GM`, `UNKNOWN`, parse ngày ban hành và dòng `V/v`.
- Alembic nâng DB local từ `0006_document_business_metadata` lên `0007_document_ocr_metadata`.
- Frontend build pass qua Docker; vẫn có warning chunk PrimeVue lớn như trước, không fail.
- Smoke upload/reprocess text công văn:
  - document chuyển `searchable`.
  - auto metadata lưu `document_type=CV`, `document_number=789/CV-BV`, `document_symbol=CV-BV`,
    `issued_date=2026-06-04`, `issued_place=Hà Nội`, `metadata_source=auto`.
  - audit log có `document.metadata_auto_extracted` với `applied=true`.
- Smoke sửa metadata thủ công rồi reprocess:
  - metadata thủ công giữ nguyên sau reprocess.
  - audit log auto extraction mới có `applied=false` và reason `metadata already reviewed manually`.

## Task Tiếp Theo Đề Xuất

1. Preview file nâng cao:
   - Preview inline PDF/image/text cạnh metadata/OCR text trong trang detail.
   - Fallback download cho DOCX/XLSX hoặc định dạng browser không preview được.

2. RBAC nhẹ:
   - Role `admin` và `user`.
   - Chỉ admin được reprocess, xóa source file, đổi thứ tự source file.
   - User thường chỉ upload/search/xem/sửa metadata theo quyền được cấp.
