# Task Vừa Hoàn Thành: Multi-file Document Upload Và Source File Model

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-04

## Kết Quả Chính

Đã triển khai MVP để một văn bản nghiệp vụ có thể có nhiều tệp nguồn.

Thay đổi chính:
- Thêm migration `0005_document_files`.
- Thêm bảng/model/schema/repository `document_files`.
- Detail API trả danh sách `files`.
- `POST /api/v1/documents/upload/multi-file` tạo 1 document, nhiều source files, 1 OCR job.
- Upload single cũ vẫn hoạt động và cũng tạo 1 `document_files` record.
- Worker OCR ưu tiên xử lý `document_files` theo `file_order`, page number nối tiếp qua nhiều file.
- Worker fallback `documents.file_path` cho dữ liệu cũ chưa có `document_files`.
- Audit event `document.upload` ghi `file_count` và file list cho multi-file.
- Frontend `/upload` có hai mode:
  - `Một tệp`
  - `Nhiều tệp cùng văn bản`
- UI tách rõ `Tên văn bản` và danh sách `Tệp nguồn`.
- Frontend document detail có card `Tệp nguồn`.
- Header detail dùng `document.title`, không coi filename là tên nghiệp vụ chính.

## Đã Kiểm Tra

```bash
docker compose run --rm --no-deps api python -m py_compile app/services/document_service.py app/routers/documents.py app/workers/ocr_worker.py app/models/document.py app/repositories/document_repository.py app/schemas/document.py
docker compose run --rm --no-deps web npm run build
docker compose up -d --build api worker web
docker compose exec -T api alembic current
curl -fsS -I http://localhost:3000/login
```

Kết quả verify:
- Alembic current là `0005_document_files`.
- Multi-file smoke tạo document `904886a1-30cf-46ad-bade-161d8c12461c` với 2 files.
- Hai files `qlvb_multi_a.txt`, `qlvb_multi_b.txt` đều chuyển `completed`.
- Document multi-file chuyển `searchable`.
- Page 1 lấy text từ file thứ nhất, page 2 lấy text từ file thứ hai.
- Search query `zeta` trả đúng document multi-file ở top 1, chunk page 2.
- Single upload cũ vẫn chạy, có title form tùy chọn và 1 source file record.
- `/upload` SSR có các nhãn `Một tệp`, `Nhiều tệp cùng văn bản`, `Tên văn bản`.
- Nuxt production build trong Docker Compose hoàn tất.

## Giới Hạn Còn Lại

- Chưa hỗ trợ `.zip`.
- Chưa hỗ trợ batch upload nhiều document riêng trong một lần.
- Chưa có partial success theo từng source file; nếu một file lỗi thì OCR job failed.
- Chưa có UI kéo thả sắp xếp lại `file_order`; thứ tự hiện theo thứ tự file gửi lên.
- Chưa có chức năng thêm tệp nguồn vào document đã tồn tại.
- Chưa có xóa/soft-delete một source file riêng lẻ.

## Task Tiếp Theo Đề Xuất

Ưu tiên 1 trong 3 hướng sau:

1. Lọc/tối ưu danh sách tài liệu:
   - Tìm theo title/filename.
   - Lọc status/document_type.
   - Sắp xếp theo ngày tạo/cập nhật.

2. Quản lý source files sau upload:
   - Thêm file vào document đã tồn tại.
   - Đổi thứ tự file.
   - Soft-delete file nguồn.
   - Reprocess sau khi thay đổi source files.

3. Zip upload dựa trên `document_files`:
   - Mode zip là một văn bản gồm nhiều tệp nguồn.
   - Chưa tự đoán zip chứa nhiều văn bản riêng để tránh sai nghiệp vụ.

RBAC role admin/user vẫn là hướng riêng nếu cần phân quyền thật sự cho nội bộ.
