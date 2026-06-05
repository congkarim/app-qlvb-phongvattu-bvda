# Task Vừa Hoàn Thành: Review Queue Dashboard

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-05

## Phạm Vi Đã Thực Hiện

Đã thêm review queue tập trung trong Dashboard để admin xem và xử lý nhiều chunks `requires_review=true`. Không đổi stack, không thêm migration và không thêm queue/runtime mới.

## Kết Quả Chính

Backend:
- Thêm endpoint admin-only `GET /api/v1/documents/chunks/review-queue`.
- Endpoint trả danh sách chunk active `requires_review=true` kèm:
  - `document_id`, `document_title`, số/ngày văn bản, loại nghiệp vụ.
  - `chunk_index`, text preview, page range.
  - `doc_group`, `chunk_level`, `section_role`, `section_path`, `chunk_confidence`.
- Hỗ trợ filter:
  - `section_role`
  - `document_id`
  - `max_confidence`
  - `limit`, `offset`
- Giữ kiến trúc `router -> service -> repository`.
- User thường bị chặn 403 qua `require_admin`.

Frontend:
- Cập nhật `/dashboard` để có card `Review queue` chỉ hiện cho admin.
- Queue có filter:
  - Tất cả review.
  - Phụ lục.
  - Không xác định.
  - Confidence thấp.
  - Document ID.
  - Limit.
- Mỗi item hiển thị document title, chunk index, role/path, confidence, text preview và link mở document detail.
- Tái dùng endpoint review chunk hiện có để admin bấm `Đã review` ngay trong queue.
- Không gọi API trực tiếp trong page; luồng vẫn là `page -> composable -> service -> API`.

Docs:
- Cập nhật `README.md`.
- Cập nhật `PROJECT_STATUS.md`.
- Cập nhật `TASK_NEXT.md`.

## Đã Kiểm Tra

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/document.py apps/api/app/repositories/document_repository.py apps/api/app/services/document_service.py apps/api/app/routers/documents.py
docker compose run --rm --no-deps web npm run build
python3 <review queue smoke script>
git diff --check
```

Kết quả:
- Backend compile pass.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.
- Review queue smoke pass:
  - Admin nhận 10 chunks cần review.
  - Mọi item trả về đều `requires_review=true`.
  - Filter `max_confidence=0.65` trả 10 chunks hợp lệ.
  - Filter `section_role=appendix` trả 0 do local chưa có appendix indexed trong queue.
  - User thường `queue-smoke-de1c52133fac@example.com` gọi endpoint nhận 403.
- Diff check pass.

## Task Tiếp Theo Đề Xuất

1. Appendix data smoke:
   - Tạo hoặc upload fixture có phụ lục thật để smoke `section_role=appendix` không còn empty-safe.
   - Kiểm tra phụ lục OCR/layout yếu xuất hiện trong review queue.
   - Kiểm tra Dashboard search filter `section_role=appendix` trả result thật.

2. Queue pagination polish:
   - Thêm phân trang `offset` trong Dashboard review queue nếu số chunk review lớn.
   - Hiển thị tổng số item nếu cần endpoint count.

## Kế Hoạch Chi Tiết: Appendix Data Smoke

### Mục Tiêu

Tạo dữ liệu kiểm thử local có phụ lục thật để xác nhận đầy đủ luồng appendix từ chunking đến Qdrant/search/review queue, thay vì chỉ smoke empty-safe.

### Phạm Vi MVP

Backend/data:
- Tạo fixture text hoặc PDF text-layer đơn giản có heading `PHỤ LỤC I` và nội dung phụ lục.
- Nếu dùng upload API, chờ worker xử lý tới `searchable`.
- Nếu cần phụ lục cần review, tạo fixture có layout/confidence yếu qua test service hoặc seed chunk test rõ ràng, tránh làm bẩn dữ liệu nghiệp vụ thật.
- Không thêm cloud service, không đổi OCR stack.

Smoke cần kiểm tra:
- Document detail có chunk `section_role=appendix`.
- `GET /api/v1/documents/chunks/review-queue?section_role=appendix` trả phụ lục nếu fixture được đánh `requires_review=true`.
- `POST /api/v1/search/semantic` với `section_role=appendix` trả result thật.
- Nếu bấm `Đã review`, queue appendix giảm hoặc chunk biến mất khỏi filter `requires_review=true`.

### Acceptance Criteria

- Có fixture hoặc script smoke tái chạy được.
- Search appendix không còn chỉ pass empty-safe.
- Review queue appendix có dữ liệu thật khi fixture chứa phụ lục cần review.
- Docs ghi rõ cách chạy smoke và cleanup nếu có tạo dữ liệu tạm.
