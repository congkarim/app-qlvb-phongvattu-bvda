# Task Vừa Hoàn Thành: Review Queue UI và Appendix Search Filter

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-05

## Phạm Vi Đã Thực Hiện

Đã thêm UI lọc nhanh chunk cần review/phụ lục trên document detail và thêm option lọc phụ lục rõ ràng trong Dashboard search. Không đổi stack, không thêm migration và không thêm endpoint mới vì schema/search API hiện tại đã đủ metadata.

## Kết Quả Chính

Frontend:
- Cập nhật `/documents/[id]` trong `apps/web/pages/documents/[...id].vue`.
- Card `Chunks` có filter:
  - `Tất cả chunks`
  - `Cần review`
  - `Phụ lục`
  - `Phụ lục cần review`
- Card `Chunks` hiển thị counter tổng chunk, chunk `requires_review=true` và chunk `section_role=appendix`.
- Chunk phụ lục hiển thị label `Phụ lục`; chunk cần kiểm tra hiển thị tag `Cần review`.
- Khi filter không có kết quả, UI hiển thị empty state riêng mà không làm mất dữ liệu chunk gốc.
- Cập nhật `/dashboard` để thêm option `Phụ lục` cho filter `section_role=appendix`.

Backend/search:
- Xác nhận `DocumentChunkRead` và semantic search schema đã có `section_role`, `section_path`, `chunk_confidence`, `requires_review`.
- Không cần sửa API vì search filter `section_role=appendix` đã đi qua service hiện có.
- Smoke API kiểm tra `section_role=appendix` ở dạng empty-safe: API phải trả 200 và mọi result nếu có đều là appendix.

Docs:
- Cập nhật `README.md`.
- Cập nhật `PROJECT_STATUS.md`.
- Cập nhật `TASK_NEXT.md`.

## Đã Kiểm Tra

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/document.py apps/api/app/schemas/search.py apps/api/app/services/search_service.py apps/api/app/routers/search.py
docker compose run --rm --no-deps web npm run build
python3 <semantic search appendix filter smoke script>
git diff --check
```

Kết quả:
- Backend compile pass cho schemas/search service/router liên quan.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.
- Semantic search smoke login admin và gọi `POST /api/v1/search/semantic` với `section_role=appendix`; API trả 200 và filter hợp lệ.
- Diff check pass.

## Task Tiếp Theo Đề Xuất

1. Review action:
   - Thêm action admin để đánh dấu một chunk đã review và tắt `requires_review`.
   - Ghi audit log cho thao tác review chunk.
   - Cập nhật Qdrant payload sau khi trạng thái review thay đổi để search filter đồng bộ.

2. Review queue dashboard:
   - Thêm view dashboard chuyên cho chunks `requires_review=true` khi số lượng review lớn hơn MVP hiện tại.
   - Hỗ trợ lọc theo `section_role=appendix`, document, confidence thấp và ngày xử lý.

## Kế Hoạch Chi Tiết: Review Action cho Chunk

### Mục Tiêu

Cho admin xử lý hàng đợi review ngay trên document detail: khi một chunk đã được kiểm tra, admin có thể đánh dấu đã review để không còn xuất hiện trong filter `Cần review`.

### Phạm Vi MVP

Backend:
- Thêm endpoint admin-only để cập nhật trạng thái review của chunk.
- Giữ kiến trúc `router -> service -> repository`.
- Chỉ cho phép thao tác với chunk active, không hard delete.
- Cập nhật `document_chunks.requires_review=false`.
- Ghi audit log `document_chunk.reviewed` hoặc action tương đương.
- Cập nhật payload Qdrant cho chunk sau khi đổi trạng thái, hoặc re-upsert vector nếu service hiện tại yêu cầu.

Frontend:
- Trong `/documents/[id]`, với chunk `requires_review=true`, hiển thị nút admin `Đã review`.
- Khi bấm thành công, refresh document detail và giữ filter hiện tại.
- Không gọi API trực tiếp trong page nếu đã có pattern service/composable; thêm method vào service/composable documents.

### Acceptance Criteria

- Admin có thể tắt `requires_review` cho một chunk.
- User thường không thấy hoặc không gọi được action này.
- Audit log document ghi nhận chunk đã review.
- Search filter `requires_review=true` không còn trả chunk đã review sau khi payload đồng bộ.
- Backend compile/test pass, frontend build pass và smoke API pass.
