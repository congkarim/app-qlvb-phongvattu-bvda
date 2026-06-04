# Task Vừa Hoàn Thành: User Management Polish

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-04

## Phạm Vi Đã Thực Hiện

Đã hoàn thiện thêm quản trị user local sau MVP.

## Kết Quả Chính

Backend:
- `GET /api/v1/users` trả response phân trang gồm `items`, `total`, `limit`, `offset`.
- Thêm `UserRepository.count_users`.
- Thêm `UserRepository.update_password`.
- Thêm `UserService.reset_password`.
- Thêm endpoint admin-only `POST /api/v1/users/{user_id}/reset-password`.
- Reset password có audit log `user.password_reset`.

Frontend:
- User service/composable hỗ trợ response phân trang.
- Page `/users` hiển thị tổng số user, trang hiện tại, nút `Trước/Sau` và page size `10/20/50/100`.
- Thêm reset password trực tiếp trên từng dòng user.

Docs:
- Cập nhật `README.md`.
- Cập nhật `PROJECT_STATUS.md`.

## Đã Kiểm Tra

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/repositories/user_repository.py apps/api/app/schemas/user.py apps/api/app/services/user_service.py apps/api/app/routers/users.py
docker compose run --rm --no-deps web npm run build
python3 <users polish smoke script>
docker compose config --quiet
git diff --check
```

Kết quả:
- Backend compile pass.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.
- Smoke API pass:
  - `GET /users?limit=1&offset=0` trả `items/total/limit/offset`.
  - Admin tạo user tạm.
  - Admin reset password user tạm.
  - Login bằng mật khẩu cũ trả `401`.
  - Login bằng mật khẩu mới thành công.
  - User thường gọi `/users` trả `403`.
  - Admin xóa mềm user tạm.
  - User đã xóa mềm login lại trả `401`.
- Docker Compose config pass.
- Diff check pass.

## Task Tiếp Theo Đề Xuất

1. User audit UI:
   - Hiển thị audit log theo user trong trang `/users` nếu cần truy vết thao tác quản trị.

2. Chunk metadata rollout:
   - Chạy backfill thật trên DB local/dev sau khi review dry-run.
   - Reindex Qdrant nếu cần đưa metadata chi tiết mới vào payload search cho toàn bộ document cũ.
