# Task Vừa Hoàn Thành: User Management MVP

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-04

## Phạm Vi Đã Thực Hiện

Đã thêm quản trị user local mức MVP cho role `admin`.

Quy tắc quyền:
- `admin`: xem danh sách user, tạo user, đổi role `admin/user`, kích hoạt/vô hiệu hóa và xóa mềm user.
- `user`: không truy cập được API/UI quản trị user.
- API chặn admin tự hạ role, tự vô hiệu hóa hoặc tự xóa tài khoản đang dùng.

## Kết Quả Chính

Backend:
- Thêm schemas `UserRead`, `UserCreateRequest`, `UserUpdateRequest`.
- Mở rộng `UserRepository` để list/filter/sort, update profile, set active và soft delete.
- Thêm `UserService` xử lý validate role/email, hash password, audit log và transaction.
- Thêm router `/api/v1/users` admin-only:
  - `GET /users`
  - `POST /users`
  - `PATCH /users/{user_id}`
  - `POST /users/{user_id}/activate`
  - `POST /users/{user_id}/deactivate`
  - `DELETE /users/{user_id}`
- Email response dùng string để hỗ trợ domain local/on-prem như `example.local`.

Frontend:
- Thêm typed user service và composable `useUsers`.
- Thêm page `/users` với:
  - Form tạo user.
  - Filter theo email/họ tên, role, trạng thái.
  - Sort cơ bản.
  - Inline edit họ tên, role, trạng thái.
  - Action kích hoạt/vô hiệu hóa và xóa mềm.
- Route guard chuyển user thường khỏi `/users`.
- Nav chỉ hiện link `Users` với admin.

Docs:
- Cập nhật `README.md`.
- Cập nhật `PROJECT_STATUS.md`.

## Đã Kiểm Tra

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/repositories/user_repository.py apps/api/app/schemas/auth.py apps/api/app/schemas/user.py apps/api/app/services/auth_service.py apps/api/app/services/user_service.py apps/api/app/routers/users.py apps/api/app/main.py
docker compose run --rm --no-deps web npm run build
python3 <users smoke script>
docker compose config --quiet
git diff --check
```

Kết quả:
- Backend compile pass.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.
- Smoke API pass:
  - Admin login thành công.
  - `GET /users` trả danh sách.
  - Admin tạo user tạm.
  - User thường gọi `/users` trả `403`.
  - Admin deactivate/activate/update/delete mềm user tạm thành công.
  - User đã delete mềm login lại trả `401`.
- Docker Compose config pass.
- Diff check pass.

## Task Tiếp Theo Đề Xuất

1. User management polish:
   - Thêm reset password cho admin.
   - Thêm phân trang server-side cho bảng users khi dữ liệu lớn.
   - Hiển thị audit user trong UI admin nếu cần truy vết.

2. Chunk metadata rollout:
   - Chạy backfill thật trên DB local/dev sau khi review dry-run.
   - Reindex Qdrant nếu cần đưa metadata chi tiết mới vào payload search cho toàn bộ document cũ.
