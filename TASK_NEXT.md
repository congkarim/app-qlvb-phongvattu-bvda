# Task Tiếp Theo: API Reprocess Document Có Audit

Trạng thái: đề xuất.

Ngày cập nhật: 2026-06-03

## Task Vừa Hoàn Thành

Đã reprocess công văn cũ bằng OCR cleanup mới và thêm index hỗ trợ keyword search.

Kết quả chính:
- Thêm script:

```bash
python -m app.scripts.reprocess_document --document-id <document_id>
```

- Script hỗ trợ:
  - `--document-id` lặp lại được.
  - `--dry-run`.
  - `--batch-size`.
- Reprocess dùng lại file gốc đã upload, OCR lại bằng code hiện tại, replace page/chunk theo document, upsert lại Qdrant và xóa point dư nếu số chunk giảm.
- Repository có method replace page/chunk theo `page_number` và `chunk_index`, không tạo duplicate với unique index hiện tại.
- Qdrant service có `delete_points()` để loại bỏ vector không còn tương ứng với chunk active.
- Thêm Alembic migration `0002_chunk_text_trgm`:
  - `CREATE EXTENSION IF NOT EXISTS pg_trgm`.
  - GIN trigram index `ix_document_chunks_text_trgm` trên `document_chunks.text` với điều kiện `deleted_at IS NULL`.

Đã reprocess document:
- Document ID: `718b0db1-6c8c-4da4-b6aa-5689173d219a`.
- File: `0f53863c-d731-4b39-b0ff-d883ab039a88.jpeg`.
- Dry-run: `old_pages=1`, `new_pages=1`, `old_chunks=1`, `new_chunks=1`, average confidence `0.9043`.
- Reprocess thật: document `searchable`, `1/1` chunk có `content_hash` và `qdrant_point_id`, `deleted_chunks=0`.

Kết quả OCR cải thiện:
- `Số: 72]/UBND-KT` -> `Số: 72/UBND-KT`.
- `27IS/2026` -> `27/5/2026`.
- Bỏ nhiễu đầu dòng như `Thuật`, `Nhất`, `Thành`, `Nhà Tháng`, `Các thuận`, `Anh thuận`.
- `Thông bảo` -> `Thông báo`.

Đã kiểm tra:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/scripts/reprocess_document.py /app/app/repositories/document_repository.py /app/app/services/qdrant_service.py /app/alembic/versions/0002_document_chunk_text_trgm_index.py
docker compose exec -T api alembic upgrade head
docker compose exec -T api python -m app.scripts.reprocess_document --document-id 718b0db1-6c8c-4da4-b6aa-5689173d219a --dry-run
docker compose exec -T api python -m app.scripts.reprocess_document --document-id 718b0db1-6c8c-4da4-b6aa-5689173d219a
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Lê Thế Anh hồ sơ xin thôi việc Xuân Lâm","limit":3}'
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Số 72 UBND KT Kính gửi Ban chỉ huy 32 xóm","limit":3}'
```

Kết quả search:
- Query `Lê Thế Anh hồ sơ xin thôi việc Xuân Lâm` trả công văn JPEG đã cleanup ở top 1.
- Query `Số 72 UBND KT Kính gửi Ban chỉ huy 32 xóm` trả công văn JPEG đã cleanup ở top 1.

Kết quả keyword index:
- Trước index, query keyword đại diện dùng seq scan khoảng `23ms` với 478 chunks.
- Sau migration, planner vẫn chọn seq scan vì bảng nhỏ; khi `enable_seqscan=off`, index trigram dùng `Bitmap Index Scan` và chạy khoảng `4.8ms`.

## Mục Tiêu Task Tiếp Theo

Đưa reprocess document từ script CLI thành API/backend workflow có audit, để thao tác được có kiểm soát từ admin hoặc tool nội bộ.

## Ràng Buộc Không Đổi

- Không dùng cloud OCR.
- Không dùng API LLM để sửa nội dung pháp lý.
- Docker Compose first.
- MVP first.
- Backend giữ `router -> service -> repository`.
- OCR pipeline local/on-prem.
- Không commit model files hoặc runtime artifacts.

## Phạm Vi Đề Xuất

### 1. Reprocess API

Vấn đề:
- Script CLI đã chạy được nhưng chưa có API để thao tác qua backend.
- Chưa có audit rõ ràng cho các lần reprocess.

Hướng xử lý:
- Thêm endpoint backend dạng `POST /documents/{id}/reprocess`.
- Tạo OCR job hoặc reprocess job mới thay vì xử lý inline nếu runtime lâu.
- Response trả job/document status.
- Giữ router mỏng, logic nằm ở service.

### 2. Audit Và An Toàn Dữ Liệu

Vấn đề:
- Reprocess thay thế page/chunk hiện tại, cần truy vết khi chạy từ UI/API.

Hướng xử lý:
- Ghi `ocr_jobs` mới cho mỗi lần reprocess hoặc thêm trường lý do vào job nếu cần.
- Lưu error message khi reprocess lỗi.
- Đảm bảo document đang reprocess không bị reprocess song song.

## Tiêu Chí Hoàn Thành

- Có API reprocess document hoặc job tương đương, không xử lý business logic trong router.
- Reprocess qua API tạo/trả trạng thái job rõ ràng.
- Search sau reprocess vẫn trả document nguồn đúng.
- Không phát sinh model/runtime artifact trong git.
