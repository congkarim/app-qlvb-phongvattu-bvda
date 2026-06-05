# Task Vừa Hoàn Thành: User Audit UI

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-05

## Phạm Vi Đã Thực Hiện

Đã thêm truy vết audit log theo user trong màn hình quản trị user local.

## Kết Quả Chính

Backend:
- Tách schema audit dùng chung sang `app.schemas.audit`.
- Thêm `UserService.list_user_audit_logs`.
- Thêm endpoint admin-only `GET /api/v1/users/{user_id}/audit-logs`.
- Endpoint kiểm tra user tồn tại và trả `404` nếu user không còn trong danh sách active records.

Frontend:
- Thêm type `UserAuditLog` và service `listAuditLogs`.
- Composable `useUsers` có loading/error riêng cho audit.
- Page `/users` có nút `Audit` trên từng dòng user.
- Audit panel hiển thị actor, action đã Việt hóa, thời gian, event ID và metadata.

Docs:
- Cập nhật `PROJECT_STATUS.md`.
- Cập nhật `README.md`.
- Cập nhật `TASK_NEXT.md`.

## Đã Kiểm Tra

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/audit.py apps/api/app/schemas/document.py apps/api/app/services/user_service.py apps/api/app/routers/users.py
docker compose run --rm --no-deps web npm run build
git diff --check
```

Kết quả:
- Backend compile pass.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.
- Diff check pass.

## Task Tiếp Theo Đề Xuất

1. User audit smoke:
   - Khi cần kiểm thử sâu hơn, chạy API smoke có DB để xác nhận `GET /users/{user_id}/audit-logs` trả đúng các event `user.created`, `user.updated`, `user.password_reset`, `user.deleted`.

2. Chunk metadata rollout:
   - Chạy backfill thật trên DB local/dev sau khi review dry-run.
   - Reindex Qdrant nếu cần đưa metadata chi tiết mới vào payload search cho toàn bộ document cũ.
