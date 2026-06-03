# Task Tiếp Theo: UI Reprocess Và Job Audit

Trạng thái: đề xuất.

Ngày cập nhật: 2026-06-03

## Task Vừa Hoàn Thành

Đã thêm API reprocess document có audit và worker xử lý async.

Kết quả chính:
- Thêm endpoint:

```text
POST /api/v1/documents/{document_id}/reprocess
```

- Request body hỗ trợ:

```json
{"reason":"verify reprocess API workflow"}
```

- API chỉ tạo job, không OCR inline:
  - Tạo `ocr_jobs` mới với `job_type='reprocess'`.
  - Lưu `reason`.
  - Job `status='pending'`.
  - Document chuyển `reprocess_pending`.
  - Worker xử lý async.
- Thêm migration `0003_ocr_job_type`:
  - `ocr_jobs.job_type`.
  - `ocr_jobs.reason`.
- Worker phân biệt:
  - `job_type='ocr'`: OCR lần đầu, create page/chunk mới.
  - `job_type='reprocess'`: replace page/chunk hiện có, upsert lại Qdrant, xóa point dư nếu số chunk giảm.
- Worker commit trạng thái `ocr_running` hoặc `reprocess_running` ngay khi bắt đầu để UI/API thấy trạng thái đang xử lý.
- Nếu reprocess lỗi, document quay về trạng thái trước đó thay vì mất trạng thái `searchable`.
- Document detail API trả `job_type` và `reason` trong `ocr_jobs`.

Đã kiểm tra:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/models/document.py /app/app/repositories/document_repository.py /app/app/services/document_service.py /app/app/routers/documents.py /app/app/schemas/document.py /app/app/workers/ocr_worker.py /app/alembic/versions/0003_ocr_job_type.py
docker compose up -d --build api worker
curl -fsS http://localhost:8000/health
docker compose exec -T api alembic current
curl -fsS -X POST http://localhost:8000/api/v1/documents/718b0db1-6c8c-4da4-b6aa-5689173d219a/reprocess -H 'Content-Type: application/json' -d '{"reason":"verify reprocess API workflow"}'
curl -fsS http://localhost:8000/api/v1/documents/718b0db1-6c8c-4da4-b6aa-5689173d219a
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Số 72 UBND KT Kính gửi Ban chỉ huy 32 xóm","limit":3}'
```

Kết quả verify:
- API trả `202 Accepted`.
- Job ID: `6a154fc5-e3f6-4f45-b929-d59db6566163`.
- Job `job_type='reprocess'`, `reason='verify reprocess API workflow'`.
- Worker xử lý xong: job `completed`, attempts `1`, document `searchable`.
- Detail API trả cả job OCR ban đầu `job_type='ocr'` và job reprocess `job_type='reprocess'`.
- Document vẫn có `1/1` chunk active, có `content_hash` và `qdrant_point_id`.
- Search `Số 72 UBND KT Kính gửi Ban chỉ huy 32 xóm` vẫn trả công văn JPEG top 1.

## Mục Tiêu Task Tiếp Theo

Thêm UI hoặc frontend workflow để người dùng/admin kích hoạt reprocess và xem audit job ngay trong màn hình chi tiết document.

## Ràng Buộc Không Đổi

- Không dùng cloud OCR.
- Không dùng API LLM để sửa nội dung pháp lý.
- Docker Compose first.
- MVP first.
- Backend giữ `router -> service -> repository`.
- Frontend giữ `page -> composable -> service -> API`.
- OCR pipeline local/on-prem.
- Không commit model files hoặc runtime artifacts.

## Phạm Vi Đề Xuất

### 1. Frontend Reprocess Action

Vấn đề:
- API reprocess đã có nhưng người dùng vẫn phải gọi bằng curl.

Hướng xử lý:
- Thêm method `reprocessDocument(id, reason)` trong frontend document service.
- Thêm composable action trong `useDocuments`.
- Trên page document detail, thêm nút reprocess khi document không ở trạng thái đang xử lý.
- Sau khi gọi reprocess, refresh/poll detail như upload OCR flow hiện tại.

### 2. Job Audit Display

Vấn đề:
- Detail API đã trả `ocr_jobs`, nhưng UI chưa hiển thị rõ `job_type`, `reason`, attempts, error.

Hướng xử lý:
- Hiển thị danh sách OCR/reprocess jobs trong document detail.
- Badge theo status.
- Hiển thị reason nếu có.
- Hiển thị error message khi job failed.

## Tiêu Chí Hoàn Thành

- Người dùng có thể bấm reprocess từ document detail.
- UI không cho bấm reprocess khi document đang `ocr_pending`, `ocr_running`, `reprocess_pending`, `reprocess_running` hoặc `chunking`.
- Job audit hiển thị được OCR job và reprocess job.
- Search sau reprocess vẫn trả document nguồn đúng.
- Không phát sinh runtime artifact trong git.
