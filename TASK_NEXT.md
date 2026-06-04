# Task Tiếp Theo: Browser Verify Reprocess UI Và Auth Guard Backend

Trạng thái: đề xuất.

Ngày cập nhật: 2026-06-04

## Task Vừa Hoàn Thành

Đã thêm UI reprocess và job audit trên màn hình chi tiết document.

Kết quả chính:
- Thêm method frontend service:

```text
reprocess(id, reason) -> POST /api/v1/documents/{document_id}/reprocess
```

- Thêm composable action `reprocessDocument(id, reason)` với loading state riêng.
- Trang `/documents/[id]` có form nhập lý do reprocess và nút `Reprocess`.
- UI không cho bấm reprocess khi document đang:
  - `ocr_pending`
  - `ocr_running`
  - `reprocess_pending`
  - `reprocess_running`
  - `chunking`
- Sau khi tạo reprocess job, page refresh detail và bật polling theo trạng thái xử lý.
- Job audit hiển thị danh sách OCR/reprocess jobs, gồm:
  - `job_type`
  - `status`
  - `reason`
  - `attempts`
  - `error_message`
  - thời gian tạo/cập nhật

Đã kiểm tra:

```bash
docker compose run --rm --no-deps web npm run build
git diff --check
```

Kết quả verify:
- Nuxt production build trong Docker Compose thành công.
- Không phát sinh runtime artifact trong git.

## Mục Tiêu Task Tiếp Theo

Kiểm tra browser workflow reprocess end-to-end và bổ sung auth guard backend cho API tài liệu/search.

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

### 1. Browser Verify Reprocess UI

Vấn đề:
- Build đã pass, nhưng cần kiểm tra thực tế trong browser với API/worker chạy đầy đủ.

Hướng xử lý:
- Chạy `docker compose up -d --build api worker web`.
- Đăng nhập admin local.
- Mở document đã `searchable`.
- Bấm reprocess với reason kiểm thử.
- Xác nhận UI chuyển `reprocess_pending`/`reprocess_running`, sau đó về `searchable`.
- Xác nhận job audit có job `reprocess` mới và reason đúng.
- Search lại query nguồn để xác nhận document vẫn đứng đúng.

### 2. Backend Auth Guard

Vấn đề:
- Frontend đã có route guard, nhưng API tài liệu/search hiện vẫn chưa enforce backend authorization dependency.

Hướng xử lý:
- Thêm dependency auth vào documents/search routers.
- Giữ endpoint `/health` public.
- Kiểm tra curl không token bị từ chối và token admin vẫn dùng được.

## Tiêu Chí Hoàn Thành

- Browser workflow reprocess chạy end-to-end.
- Search sau reprocess vẫn trả document nguồn đúng.
- API documents/search yêu cầu token backend.
- Frontend hiện tại vẫn gọi API thành công nhờ token từ auth store.
