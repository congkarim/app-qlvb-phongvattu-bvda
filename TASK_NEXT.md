# Task Vừa Hoàn Thành: Xem/Download Source File Khi Sửa Metadata

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-04

## Phạm Vi Đã Thực Hiện

Đã hỗ trợ xem hoặc download tệp nguồn khi người dùng sửa metadata trong `/documents/[id]`, giúp đối chiếu số văn bản, ngày ban hành, đơn vị ban hành và loại nghiệp vụ trước khi lưu.

## Kết Quả Chính

Backend:
- Thêm API:
  - `GET /api/v1/documents/{document_id}/files/{document_file_id}/download`
- Chỉ trả source file còn active và thuộc đúng document.
- Không expose path thật trên server.
- Trả file bằng `FileResponse` với `content-disposition: inline`.
- File id sai hoặc file không tồn tại trả 404.

Frontend:
- `document.service.ts` có `downloadSourceFile` dùng auth header để fetch blob.
- `useDocuments.ts` có `openSourceFile` và `sourceFileViewLoading`.
- Trang `/documents/[id]` có nút `Xem` cạnh từng tệp nguồn.
- PDF/image/text mở tab mới; DOCX/XLSX hoặc định dạng browser không preview được fallback download.

## Đã Kiểm Tra

```bash
docker compose config --quiet
docker compose run --rm --no-deps api python -m py_compile app/repositories/document_repository.py app/services/document_service.py app/routers/documents.py
docker compose run --rm --no-deps web npm run build
curl -fsS -I http://localhost:3000/login
curl -fsS -I http://localhost:3000/documents/{document_id}
```

Kết quả:
- Backend compile pass.
- Frontend build pass qua Docker.
- Download source file hợp lệ trả 200 với `content-disposition: inline`.
- File id sai trả 404.
- `/login` trả 200.
- Detail route redirect `302 /login` khi chưa đăng nhập.

## Task Tiếp Theo Đề Xuất: Tự Động Lưu Metadata Sau OCR

Mục tiêu: sau khi OCR xong, hệ thống tự động phân loại văn bản hành chính và lưu metadata theo skill
`.agents/skills/vn-admin-doc-ocr-classifier/`. Người dùng sẽ xem OCR text, đối chiếu metadata đã trích xuất,
và sửa thủ công nếu có trường sai.

Quy tắc quan trọng:
- Nếu tài liệu đã được người dùng sửa metadata thủ công, reprocess không được ghi đè metadata đó.
- Reprocess chỉ được cập nhật lại OCR pages/chunks/search index và ghi nhận kết quả auto extraction mới trong audit log.
- Chỉ tự động ghi metadata sau OCR khi tài liệu chưa có dấu hiệu đã được review/sửa thủ công.

### Phạm Vi Backend/Database

1. Mở rộng schema `documents` để khớp classifier:
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

2. Giữ và chỉnh nghĩa các trường hiện có:
   - `document_type`: dùng nhãn hành chính chuẩn như `QĐ`, `CV`, `TB`, `UNKNOWN`.
   - `issuing_agency`: map từ `agency_name`.
   - `issued_date`: map từ `date`.
   - `business_type`: chỉ giữ cho phân loại nghiệp vụ nội bộ, không dùng thay `document_type`.

3. Tạo service classifier local/rule-based:
   - Input: OCR pages.
   - Output: JSON hợp lệ theo `extraction_schema.json`.
   - Không bịa trường không có bằng chứng; thiếu thì lưu `null`.
   - Nếu mơ hồ thì `document_type = "UNKNOWN"` và giảm confidence.

4. Gắn vào OCR worker:
   - Luồng mới: OCR pages -> lưu pages -> classify metadata -> lưu metadata nếu chưa review thủ công -> chunk -> embedding -> Qdrant.
   - Với job `reprocess`, kiểm tra `metadata_reviewed_at`/`metadata_source` trước khi update metadata.

5. Cập nhật API:
   - Mở rộng `DocumentRead`, `DocumentDetailRead`, `DocumentMetadataUpdateRequest`.
   - `PATCH /documents/{document_id}/metadata` nhận đủ trường mới.
   - Khi người dùng lưu thủ công, set `metadata_source = "manual"` hoặc `"mixed"` và set `metadata_reviewed_at`.

6. Audit log:
   - Thêm action `document.metadata_auto_extracted`.
   - Giữ action `document.metadata_updated` cho sửa thủ công.
   - Log rõ `ocr_job_id`, `document_type`, `confidence`, và các trường được trích xuất.

### Phạm Vi Frontend

1. Mở rộng type trong `apps/web/types/document.ts`.

2. Mở rộng service/composable:
   - `document.service.ts` gửi đủ metadata fields.
   - `useDocuments.ts` giữ loading/error state hiện có.

3. Mở rộng form metadata ở `/documents/[id]`:
   - Loại văn bản hành chính.
   - Confidence chỉ hiển thị.
   - Cơ quan ban hành, số văn bản, ký hiệu, ngày ban hành, địa danh.
   - Trích yếu, nơi nhận, người ký, chức vụ người ký.
   - Có dấu, có phụ lục, số trang.
   - Trạng thái source/review metadata.

4. Bố trí UI để đối chiếu:
   - Metadata form/summary ở một vùng.
   - OCR text/source preview ở vùng còn lại.
   - Người dùng có thể sửa và lưu ngay sau khi kiểm tra.

### Kiểm Tra Cần Có

Backend:
- Test classifier với fixture OCR cho `CV`, `QĐ`, `TB`, `BB`, `GM`, `UNKNOWN`.
- Test parse ngày ban hành và dòng `V/v`.
- Test OCR worker tự lưu metadata sau OCR.
- Test reprocess không ghi đè metadata đã sửa thủ công.
- Test PATCH metadata cập nhật đủ field và tạo audit log.

Frontend:
- Build/typecheck pass.
- Form detail hiển thị đủ field.
- Save metadata gửi đúng payload.
- Polling sau OCR cập nhật metadata tự động khi job hoàn tất.
