# Task Vừa Hoàn Thành: Review Action cho Chunk

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-05

## Phạm Vi Đã Thực Hiện

Đã thêm thao tác admin để đánh dấu chunk `requires_review=true` là đã review ngay trong trang chi tiết document. Không đổi stack, không thêm migration và không thêm queue mới.

## Kết Quả Chính

Backend:
- Thêm endpoint admin-only `PATCH /api/v1/documents/{document_id}/chunks/{chunk_id}/reviewed`.
- Giữ kiến trúc `router -> service -> repository`:
  - Router chỉ validate auth/admin và map lỗi HTTP.
  - Service xử lý nghiệp vụ review, audit log và sync Qdrant.
  - Repository lấy chunk active theo document và cập nhật `requires_review=false`.
- Ghi audit log `document_chunk.reviewed` trên entity `document`, nên log xuất hiện trong document detail hiện có.
- Cập nhật Qdrant payload bằng `set_payload`, tránh re-embedding vì text/vector không đổi.
- Nếu Qdrant sync lỗi, service không commit DB để tránh lệch trạng thái search filter.

Frontend:
- Cập nhật document service/composable để gọi endpoint review chunk qua đúng luồng `page -> composable -> service -> API`.
- Trong `/documents/[id]`, admin thấy nút `Đã review` trên chunk đang có `requires_review=true`.
- Khi thao tác thành công, detail được refresh và filter chunk hiện tại vẫn được giữ.
- User thường không thấy nút review.

Docs:
- Cập nhật `README.md`.
- Cập nhật `PROJECT_STATUS.md`.
- Cập nhật `TASK_NEXT.md`.

## Đã Kiểm Tra

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/repositories/document_repository.py apps/api/app/services/qdrant_service.py apps/api/app/services/document_service.py apps/api/app/routers/documents.py apps/api/app/schemas/document.py
docker compose run --rm --no-deps web npm run build
python3 <review chunk smoke script>
python3 <review chunk user forbidden smoke script>
git diff --check
```

Kết quả:
- Backend compile pass.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.
- Review smoke pass với document `419a80f8-dc60-4148-a62d-c55a6acf6bc9`, chunk `eaed75ab-b7e9-43e8-9ee7-0a005250a413`.
- Sau review, response/detail đều có `requires_review=false`.
- Audit log `document_chunk.reviewed` xuất hiện trong document detail.
- Search `requires_review=true` không còn trả chunk vừa review.
- User thường `review-smoke-e49755296dac@example.com` gọi endpoint nhận 403.
- Diff check pass.

## Task Tiếp Theo Đề Xuất

1. Review queue dashboard:
   - Thêm view trong Dashboard để admin xem nhiều chunks `requires_review=true` theo danh sách tập trung.
   - Hỗ trợ lọc theo `section_role=appendix`, document, confidence thấp và ngày xử lý.
   - Cho phép mở document detail hoặc đánh dấu reviewed từ queue nếu API hiện có đủ dùng.

2. Appendix data smoke:
   - Tạo hoặc upload fixture có phụ lục thật để smoke `section_role=appendix` không còn empty-safe.
   - Kiểm tra phụ lục OCR yếu xuất hiện trong review queue và search appendix filter.

## Kế Hoạch Chi Tiết: Review Queue Dashboard

### Mục Tiêu

Tạo điểm xem tập trung cho admin khi số lượng chunk cần review lớn, thay vì phải mở từng document detail để lọc chunk.

### Phạm Vi MVP

Backend:
- Ưu tiên dùng semantic search hiện có với filter `requires_review=true`.
- Nếu cần danh sách không phụ thuộc query search, thêm endpoint list chunks review theo metadata:
  - `GET /api/v1/documents/chunks/review-queue`
  - Query: `limit`, `offset`, `section_role`, `document_id`, `max_confidence`.
  - Response gồm chunk metadata, document title, document id và excerpt text ngắn.
- Giữ router-service-repository, không đưa query DB vào router.

Frontend:
- Trong `/dashboard`, thêm tab hoặc block `Review queue` chỉ hiện cho admin.
- Filter tối thiểu:
  - Tất cả review.
  - Phụ lục.
  - Confidence thấp.
- Mỗi item hiển thị document title, chunk index, role/path, confidence, text preview và action mở document.
- Có thể thêm action `Đã review` trực tiếp nếu tái dùng endpoint hiện tại rõ ràng và không làm UI rối.

### Acceptance Criteria

- Admin có thể xem danh sách chunk cần review từ Dashboard.
- User thường không thấy review queue.
- Có filter phụ lục trong queue.
- Có link mở document detail đúng document/chunk context tối thiểu.
- Backend/frontend checks pass và docs được cập nhật.
