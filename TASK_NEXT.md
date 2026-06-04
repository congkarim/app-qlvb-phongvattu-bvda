# Task Tiếp Theo: RBAC Hoặc Audit Log Admin

Trạng thái: đề xuất.

Ngày cập nhật: 2026-06-04

## Task Vừa Hoàn Thành

Đã hoàn thiện UX admin MVP quanh trạng thái reprocess và xác định auth scope tối thiểu.

Kết quả chính:
- Document detail hiển thị thời điểm refresh detail gần nhất.
- Polling OCR/reprocess cập nhật timestamp refresh theo từng lần fetch.
- Nút `Reprocess` có confirm trước khi tạo job.
- Job audit làm nổi bật job `pending/running` và gắn badge `Đang xử lý`.
- Header document, reason và chunk title wrap tốt hơn trên mobile.
- Auth scope MVP được chốt: mọi user active đã đăng nhập được dùng documents/search/reprocess; chưa thêm role/RBAC ở bước này để tránh over-engineering.

Đã kiểm tra:

```bash
docker compose run --rm --no-deps web npm run build
docker compose up -d --build web
curl -fsS -I http://localhost:3000/login
git diff --check
```

Kết quả verify:
- Nuxt production build thành công.
- `/login` trả HTTP 200 sau khi recreate web.
- Headless Chrome với cookie `auth_token` xác nhận UI có `Cập nhật detail lần cuối`, `Lần refresh gần nhất`, `Reprocess`, `Job audit`.
- Confirm cancel smoke test gọi được `window.confirm` và không tạo job reprocess mới.
- Mobile viewport `390px` không phát hiện overflow ngang (`scrollWidth=390`).
- Không phát sinh runtime artifact trong git.

## Mục Tiêu Task Tiếp Theo

Chọn giữa RBAC MVP hoặc audit log admin cho thao tác nghiệp vụ nhạy cảm.

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

### 1. RBAC MVP

Vấn đề:
- Hiện mọi user active đã đăng nhập đều có thể upload/search/reprocess.

Hướng xử lý:
- Nếu dự án cần tách admin/user, thêm field `role` vào `users` bằng migration.
- Seed admin local có role `admin`.
- Thêm dependency `require_admin`.
- Giới hạn reprocess và upload cho admin nếu phù hợp nghiệp vụ.

### 2. Audit Log Admin

Vấn đề:
- Reprocess job có reason nhưng chưa có bảng audit log nghiệp vụ riêng cho thao tác admin.

Hướng xử lý:
- Thêm bảng `audit_logs` MVP với actor, action, entity type/id, metadata, created_at.
- Ghi log khi upload và request reprocess.
- Hiển thị audit log đơn giản trong document detail nếu cần.

## Tiêu Chí Hoàn Thành

- RBAC hoặc audit log được chọn rõ, không làm cả hai nếu chưa cần.
- Nếu làm RBAC, curl xác nhận user thường không gọi được endpoint admin-only.
- Nếu làm audit log, document detail hoặc API trả được audit event cơ bản.
- Không làm chậm workflow upload -> OCR -> search hiện tại.
