# Task Vừa Hoàn Thành: Documents Filter, Source File Management Và Zip Upload

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-04

## Phạm Vi Đã Thực Hiện

Đã triển khai theo đúng thứ tự:

1. Lọc/tối ưu danh sách tài liệu.
2. Quản lý source files sau upload.
3. Zip upload dựa trên `document_files`.

## Kết Quả Chính

Danh sách tài liệu:
- `GET /api/v1/documents` hỗ trợ:
  - `q`: tìm theo title hoặc original filename.
  - `status`: lọc trạng thái.
  - `document_type`: lọc loại văn bản.
  - `sort_by`: `created_at`, `updated_at`, `title`, `status`, `document_type`.
  - `sort_dir`: `asc` hoặc `desc`.
- Frontend `/documents` có filter/search/sort và nút xóa lọc.
- Bảng danh sách hiển thị thêm `Cập nhật`.

Quản lý source files:
- Thêm API `POST /api/v1/documents/{document_id}/files`.
- Thêm API `PATCH /api/v1/documents/{document_id}/files/order`.
- Thêm API `DELETE /api/v1/documents/{document_id}/files/{document_file_id}`.
- Thêm source file, đổi thứ tự hoặc soft-delete source file đều tạo OCR job `reprocess` async.
- Không cho sửa source files khi document đang có OCR/reprocess job active.
- Không cho xóa source file cuối cùng.
- Detail UI có:
  - chọn thêm nhiều source files,
  - nút lên/xuống để đổi thứ tự,
  - nút xóa source file,
  - tự polling sau khi tạo reprocess job.
- Audit log có label cho:
  - `document.source_files_added`,
  - `document.source_files_reordered`,
  - `document.source_file_deleted`.

Zip upload:
- Thêm API `POST /api/v1/documents/upload/zip`.
- Mode zip hiện là: một `.zip` = một document nghiệp vụ gồm nhiều tệp nguồn.
- Mỗi file entry trong zip được lưu thành một `document_files` record.
- Không tự đoán zip chứa nhiều văn bản riêng.
- Frontend `/upload` có mode `Zip cùng văn bản`.
- Audit log có event `document.upload_zip`.

## Đã Kiểm Tra

```bash
docker compose run --rm --no-deps api python -m py_compile app/services/document_service.py app/routers/documents.py app/repositories/document_repository.py app/schemas/document.py
docker compose run --rm --no-deps web npm run build
docker compose up -d --build api worker web
curl -fsS -I http://localhost:3000/login
```

Smoke test:
- Filter list với `q=multi`, `status=searchable`, `sort_by=updated_at`, `sort_dir=desc` trả đúng document multi-file smoke.
- Zip upload tạo document `53fc35a4-dfc6-43bd-9e8b-0c2baf94be2a`, có 2 source files, OCR xong `searchable`.
- Thêm source file vào document zip tạo reprocess job, OCR xong có 3 pages.
- Đổi thứ tự source files tạo reprocess job, page 1 đổi đúng theo file mới đứng đầu.
- Soft-delete source file tạo reprocess job, OCR xong còn 2 source files và 2 pages.
- SSR `/documents` có nhãn filter/sort.
- SSR `/upload` có mode `Zip cùng văn bản`.

## Giới Hạn Còn Lại

- Chưa có batch zip: một zip chứa nhiều văn bản riêng.
- Chưa có preview nội dung zip trước khi upload.
- Chưa có kéo thả reorder; hiện dùng nút lên/xuống.
- Chưa có khôi phục source file đã soft-delete.
- Chưa có metadata nghiệp vụ riêng cho công văn/hợp đồng/quyết định.
- Chưa có RBAC role admin/user.

## Task Tiếp Theo Đề Xuất

Ưu tiên tiếp theo nên là một trong các hướng sau:

1. Metadata nghiệp vụ:
   - Số văn bản.
   - Ngày ban hành.
   - Đơn vị ban hành.
   - Loại nghiệp vụ: công văn đến/đi, hợp đồng, quyết định.

2. RBAC nhẹ:
   - Role `admin` và `user`.
   - Chỉ admin được reprocess, xóa source file, đổi source file.
   - User thường chỉ upload/search/xem.

3. Preview và kiểm soát zip:
   - Xem danh sách file trong zip trước khi tạo document.
   - Cho phép bỏ chọn file trong zip.
   - Cảnh báo file unsupported trước OCR.
