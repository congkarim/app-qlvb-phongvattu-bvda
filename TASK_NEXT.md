# Task Tiếp Theo: Document List Filters Hoặc RBAC Nhẹ

Trạng thái: đề xuất.

Ngày cập nhật: 2026-06-04

## Task Vừa Hoàn Thành

Đã triển khai phương án 2: Audit Log Admin MVP cho upload và reprocess.

Kết quả chính:
- Thêm migration `0004_audit_logs`.
- Thêm model/repository audit log.
- Ghi event `document.upload` khi upload document.
- Ghi event `document.reprocess_requested` khi request reprocess.
- Document detail API trả `audit_logs` kèm actor và metadata.
- Frontend document detail hiển thị card `Admin audit log`.
- Không triển khai RBAC trong task này để giữ scope đúng phương án đã chọn.

Đã kiểm tra:

```bash
docker compose run --rm --no-deps api python -m py_compile /app/app/models/audit_log.py /app/app/repositories/audit_log_repository.py /app/app/repositories/document_repository.py /app/app/services/document_service.py /app/app/routers/documents.py /app/app/schemas/document.py /app/alembic/versions/0004_audit_logs.py
docker compose run --rm --no-deps web npm run build
docker compose up -d --build api web
docker compose exec -T api alembic current
curl -fsS http://localhost:8000/health
curl -fsS -I http://localhost:3000/login
git diff --check
```

Kết quả verify:
- Alembic current là `0004_audit_logs`.
- Reprocess audit event `0a8fa045-67b4-4b96-8d7d-ebceaf4b0206` ghi actor admin, reason và OCR job ID đúng.
- Upload audit event cho document `9f92a517-6e03-49f7-b112-f0279e53f3c2` ghi filename, content type, document type và OCR job ID đúng.
- Headless Chrome xác nhận UI có `Admin audit log`, `Yêu cầu reprocess`, actor admin và reason audit verify.
- Search sau reprocess audit vẫn trả document nguồn `718b0db1-6c8c-4da4-b6aa-5689173d219a` top 1.
- Không phát sinh runtime artifact trong git.

## Mục Tiêu Task Tiếp Theo

Cải thiện khả năng vận hành danh sách tài liệu hoặc thêm RBAC nhẹ nếu có nhu cầu phân quyền thật.

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

### 1. Document List Filters

Vấn đề:
- Danh sách documents hiện còn đơn giản, khó lọc theo trạng thái, loại file, hoặc thời gian khi dữ liệu tăng.

Hướng xử lý:
- Thêm query params backend cho `/documents`: status, document_type, q, created_from/created_to.
- Frontend `/documents` có filter panel MVP.
- Giữ pagination limit/offset hiện có.

### 2. RBAC Nhẹ

Vấn đề:
- Hiện mọi user active đã đăng nhập có thể upload/search/reprocess.

Hướng xử lý:
- Chỉ làm nếu cần phân quyền thật cho nhóm 50 người dùng nội bộ.
- Thêm role `admin/user` và `require_admin`.
- Giới hạn upload/reprocess cho admin; list/detail/search vẫn cho user active.

## Tiêu Chí Hoàn Thành

- Nếu làm filters, danh sách documents lọc được theo status/type/search text và UI vẫn dùng service/composable.
- Nếu làm RBAC, user thường bị chặn khỏi endpoint admin-only và audit log vẫn ghi actor.
- Không làm chậm workflow upload -> OCR -> search hiện tại.
