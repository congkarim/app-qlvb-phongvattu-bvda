# Task Vừa Hoàn Thành: Metadata Nghiệp Vụ Cho Văn Bản

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-04

## Phạm Vi Đã Thực Hiện

Đã triển khai metadata nghiệp vụ dùng chung trên bảng `documents`, chưa tập trung tiếp vào preview/kiểm soát zip theo yêu cầu hiện tại.

## Kết Quả Chính

Database/backend:
- Thêm migration `0006_document_business_metadata`.
- Bảng `documents` có thêm:
  - `document_number`: số văn bản.
  - `issued_date`: ngày ban hành.
  - `issuing_agency`: đơn vị ban hành.
  - `business_type`: loại nghiệp vụ.
- `GET /api/v1/documents` hỗ trợ:
  - Tìm `q` theo title, original filename, số văn bản hoặc đơn vị ban hành.
  - Lọc `business_type`.
  - Sort thêm `issued_date` và `business_type`.
- Upload một tệp, nhiều tệp và zip đều nhận metadata nghiệp vụ qua form data.
- Audit metadata khi upload có ghi kèm các trường nghiệp vụ.

Frontend:
- `/upload` có form metadata nghiệp vụ:
  - Số văn bản.
  - Ngày ban hành.
  - Đơn vị ban hành.
  - Loại nghiệp vụ: công văn đến, công văn đi, hợp đồng, quyết định.
- `/documents` có filter loại nghiệp vụ, sort ngày ban hành/loại nghiệp vụ và hiển thị thêm số văn bản, ngày ban hành, đơn vị ban hành.
- `/documents/[id]` hiển thị đầy đủ metadata nghiệp vụ trong card `Metadata`.

## Đã Kiểm Tra

```bash
docker compose config --quiet
docker compose run --rm --no-deps api python -m py_compile app/models/document.py app/schemas/document.py app/repositories/document_repository.py app/services/document_service.py app/routers/documents.py
docker compose run --rm --no-deps api python -m py_compile alembic/versions/0006_document_business_metadata.py
docker compose run --rm api alembic upgrade head
docker compose run --rm --no-deps web npm run build
docker compose up -d api web
curl -fsS http://localhost:8000/health
curl -fsS -I http://localhost:3000/login
```

Kết quả:
- Backend compile pass.
- Alembic upgrade pass, DB local đã lên revision `0006_document_business_metadata`.
- Frontend build pass qua Docker.
- `npm run build` trực tiếp trên host fail do thiếu `apps/web/node_modules/.bin/nuxt`; dùng Docker Compose là workflow hợp lệ.
- Smoke upload `metadata-smoke.txt` với metadata nghiệp vụ trả đúng response.
- Search/list theo `q=123/CV-VT`, `business_type=incoming_dispatch`, `sort_by=issued_date` trả đúng document smoke.
- Web `/upload` và `/documents` redirect về `/login` khi chưa đăng nhập; `/login` trả 200.

## Giới Hạn Còn Lại

- Chưa có batch zip: một zip chứa nhiều văn bản riêng.
- Chưa có preview nội dung zip trước khi upload.
- Chưa có kéo thả reorder; hiện dùng nút lên/xuống.
- Chưa có khôi phục source file đã soft-delete.
- Metadata hiện là field chung trên `documents`, chưa tách bảng riêng cho công văn/hợp đồng/quyết định.
- Chưa có màn sửa metadata sau upload.
- Chưa có RBAC role admin/user.

## Task Tiếp Theo Đề Xuất

Ưu tiên tiếp theo nên là một trong các hướng sau:

1. Sửa metadata sau upload:
   - API `PATCH /api/v1/documents/{id}/metadata`.
   - Form chỉnh sửa trong trang detail.
   - Ghi audit log `document.metadata_updated`.

2. RBAC nhẹ:
   - Role `admin` và `user`.
   - Chỉ admin được reprocess, xóa source file, đổi source file.
   - User thường chỉ upload/search/xem.

3. Preview và kiểm soát zip, tạm để sau:
   - Xem danh sách file trong zip trước khi tạo document.
   - Cho phép bỏ chọn file trong zip.
   - Cảnh báo file unsupported trước OCR.
