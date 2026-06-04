# Task Vừa Hoàn Thành: RBAC Nhẹ Admin/User

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-04

## Phạm Vi Đã Thực Hiện

Đã thêm RBAC nhẹ với hai role `admin` và `user`.

Quy tắc quyền:
- `admin`: được reprocess document, thêm source file, đổi thứ tự source file và xóa source file.
- `user`: được upload, search, xem document/source file và sửa metadata.

## Kết Quả Chính

Backend/database:
- Thêm migration `0009_user_roles`.
- Bổ sung cột `users.role`, default migration là `user`.
- Migration set `admin@example.com` thành `admin`.
- Seed admin local sẽ tạo hoặc cập nhật admin với role `admin`.
- JWT login thêm claim `role`.
- Login response trả user object gồm `id`, `email`, `full_name`, `role`.
- Thêm dependency `require_admin`.
- Các endpoint admin-only:
  - `POST /documents/{document_id}/files`
  - `PATCH /documents/{document_id}/files/order`
  - `DELETE /documents/{document_id}/files/{document_file_id}`
  - `POST /documents/{document_id}/reprocess`

Frontend:
- Auth store lưu `auth_user` cookie và getter `isAdmin`.
- Login lưu cả token và user.
- Trang document detail:
  - User thường không thấy dropzone thêm source file.
  - User thường không được reprocess.
  - Nút đổi thứ tự/xóa source file bị khóa theo quyền admin.

Docs:
- Cập nhật `README.md`.
- Cập nhật `PROJECT_STATUS.md`.

## Đã Kiểm Tra

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/models/user.py apps/api/app/repositories/user_repository.py apps/api/app/schemas/auth.py apps/api/app/services/auth_service.py apps/api/app/routers/auth.py apps/api/app/dependencies.py apps/api/app/routers/documents.py apps/api/alembic/versions/0009_user_roles.py
docker compose run --rm --no-deps web npm run build
docker compose config --quiet
docker compose run --rm api alembic upgrade head
curl -fsS http://localhost:8000/health
curl -fsS -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"email":"admin@example.com","password":"admin123"}'
```

Kết quả:
- Backend compile pass.
- Frontend build pass.
- Docker Compose config pass.
- Alembic upgrade pass, DB local lên revision `0009_user_roles`.
- Admin login response trả `user.role=admin`.
- Smoke user thường gọi endpoint reprocess trả `403 Admin role required`.
- Frontend build vẫn có warning chunk PrimeVue lớn như trước, không fail.

## Task Tiếp Theo Đề Xuất

1. Chunk metadata backfill:
   - Reprocess các document cũ để populate metadata chunk mới.
   - Hoặc viết script backfill nhẹ nếu cần giữ nguyên OCR text hiện có.

2. User management MVP:
   - API/list UI tạo user thường.
   - Admin đổi role `admin/user`.
