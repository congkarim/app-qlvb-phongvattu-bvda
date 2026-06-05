# Task Vừa Hoàn Thành: Queue Pagination Polish

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-05

## Phạm Vi Đã Thực Hiện

Đã hoàn thiện phân trang cho Dashboard review queue để admin xử lý danh sách chunk cần review dài hơn một trang. Không đổi stack, không thêm migration và giữ đúng kiến trúc backend/frontend.

## Kết Quả Chính

Backend:
- Mở rộng endpoint admin-only `GET /api/v1/documents/chunks/review-queue`.
- Response mới trả object:
  - `items`
  - `total`
  - `limit`
  - `offset`
- Giữ filter hiện có:
  - `section_role`
  - `document_id`
  - `max_confidence`
  - `limit`
  - `offset`
- Thêm repository count matching cùng bộ filter với list.
- Tách helper filter nội bộ cho review queue để tránh lệch logic giữa list và count.
- Thêm sort tie-breaker `DocumentChunk.id.asc()` sau confidence và `updated_at` để pagination ổn định, tránh item trùng giữa các page.
- Giữ router chỉ nhận request và gọi service; business/query logic nằm trong service/repository.

Frontend:
- Cập nhật type `ReviewQueueResponse`.
- Cập nhật `document.service.ts` để nhận response phân trang.
- Cập nhật `useDocuments` để quản lý `reviewQueue`, `reviewQueueTotal`, `reviewQueueLimit`, `reviewQueueOffset`.
- Cập nhật `/dashboard` card `Review queue`:
  - Hiển thị tổng số chunk cần review.
  - Hiển thị khoảng item hiện tại.
  - Có nút `Trước/Sau`.
  - Disable `Trước` khi ở trang đầu.
  - Disable `Sau` khi hết dữ liệu.
  - Reset `offset=0` khi bấm lọc lại.
  - Giữ filter hiện tại khi chuyển trang.
  - Sau khi bấm `Đã review`, refresh page hiện tại; nếu page rỗng và còn dữ liệu trước đó thì tự lùi về page trước.
- Frontend vẫn theo luồng `page -> composable -> service -> API`.

Docs:
- Cập nhật `README.md`.
- Cập nhật `PROJECT_STATUS.md`.
- Cập nhật `TASK_NEXT.md`.

## Đã Kiểm Tra

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/document.py apps/api/app/repositories/document_repository.py apps/api/app/services/document_service.py apps/api/app/routers/documents.py apps/api/app/scripts/smoke_appendix_data.py
docker compose run --rm --no-deps web npm run build
docker compose exec -T api python -m app.scripts.smoke_appendix_data
python3 <review queue pagination smoke script>
python3 <review queue user forbidden smoke script>
git diff --check
```

Kết quả:
- Backend compile pass.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.
- Appendix smoke pass sau khi cập nhật response shape.
- Pagination smoke pass:
  - `limit=5&offset=0` trả 5 items.
  - `limit=5&offset=5` trả 5 items.
  - `total=230`.
  - Hai page không trùng item.
  - Response có đủ `items`, `total`, `limit`, `offset`.
  - Filter `section_role=appendix` vẫn hoạt động.
- User forbidden smoke pass: user thường `queue-page-smoke-1780659295@example.local` gọi review queue nhận `403`.

## Task Tiếp Theo Đề Xuất

1. Smoke API auth wrapper:
   - Chuẩn hóa các smoke script HTTP đang chạy inline thành script tái chạy được.
   - Dùng login admin/user để kiểm tra review queue, semantic search và review action sát API hơn.
   - Cleanup user/document smoke sau khi chạy.

2. Review queue UX polish:
   - Cân nhắc dùng PrimeVue paginator nếu queue cần nhiều trang hơn và UI hiện tại chưa đủ tiện.
   - Thêm page number/current page nếu admin cần nhảy nhanh giữa các page.
