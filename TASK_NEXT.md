# Task Vừa Hoàn Thành: Appendix Data Smoke

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-05

## Phạm Vi Đã Thực Hiện

Đã thêm fixture và script smoke tái chạy được để kiểm tra luồng phụ lục có dữ liệu thật, thay vì chỉ kiểm tra `section_role=appendix` theo kiểu empty-safe. Không đổi stack, không thêm migration và không thêm runtime mới.

## Kết Quả Chính

Backend/data:
- Thêm fixture `tests/fixtures/appendix_smoke/appendix_review_fixture.txt` có heading phụ lục và nội dung danh mục vật tư.
- Thêm script `python -m app.scripts.smoke_appendix_data`.
- Script seed document smoke tạm có:
  - `status=searchable`.
  - Source file text fixture.
  - OCR page confidence thấp.
  - Chunk `section_role=appendix`, `requires_review=true`, `chunk_confidence=0.42`.
  - Qdrant payload đầy đủ qua `build_qdrant_payload`.
- Script cleanup document smoke và Qdrant point mặc định; tùy chọn `--keep-data` để giữ dữ liệu kiểm tra UI thủ công.

Smoke kiểm tra:
- Document detail có chunk `section_role=appendix`.
- Review queue filter `section_role=appendix` và `document_id` trả chunk phụ lục thật.
- Semantic search filter `section_role=appendix` trả result thật.
- Action `Đã review` chuyển `requires_review=false`.
- Review queue appendix không còn chunk đã review.
- Search với `section_role=appendix` và `requires_review=true` không còn trả chunk đã review.

Docs:
- Cập nhật `README.md` với cách chạy smoke và cleanup behavior.
- Cập nhật `PROJECT_STATUS.md`.
- Cập nhật `TASK_NEXT.md`.

## Đã Kiểm Tra

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/scripts/smoke_appendix_data.py
docker compose exec -T api python -m app.scripts.smoke_appendix_data
```

Kết quả:
- Backend script compile pass.
- Appendix smoke pass:
  - `document_id=cb2eef12-a279-4d52-966b-59b71def7198`
  - `chunk_id=a419a355-b387-4370-90ac-a7d65f3f1be0`
  - `cleanup=removed`

## Task Tiếp Theo Đề Xuất

Queue pagination polish:
- Thêm phân trang `offset` trong Dashboard review queue nếu số chunk review lớn.
- Hiển thị tổng số item nếu cần endpoint count.
- Giữ frontend theo luồng `page -> composable -> service -> API`.

## Kế Hoạch Chi Tiết: Queue Pagination Polish

### Mục Tiêu

Hoàn thiện review queue trong Dashboard để admin xử lý danh sách chunk cần review dài hơn một trang mà không phải tăng `limit` thủ công. UI cần có phân trang rõ ràng, giữ filter hiện tại khi chuyển trang và không phá vỡ workflow review chunk hiện có.

### Phạm Vi MVP

Backend:
- Mở rộng endpoint admin-only hiện có `GET /api/v1/documents/chunks/review-queue`.
- Giữ filter hiện tại:
  - `section_role`
  - `document_id`
  - `max_confidence`
  - `limit`
  - `offset`
- Bổ sung tổng số item matching filter nếu cần cho frontend pagination.
- Ưu tiên response dạng object có `items`, `total`, `limit`, `offset` nếu cần count; nếu đổi response model, cập nhật frontend service/composable đồng bộ.
- Giữ kiến trúc `router -> service -> repository`.
- Không thêm migration nếu chỉ count dữ liệu hiện có.

Repository/service:
- Thêm repository method count review queue matching cùng bộ filter với list.
- Tránh duplicate logic filter bằng helper nội bộ nếu code hiện tại bắt đầu lặp nhiều.
- Đảm bảo count chỉ tính chunk active:
  - `DocumentChunk.deleted_at is null`
  - `DocumentChunk.requires_review=true`
  - document chưa soft-delete.

Frontend:
- Cập nhật `document.service.ts` để nhận response phân trang.
- Cập nhật `useDocuments` hoặc composable tương ứng, không gọi API trực tiếp trong page.
- Cập nhật `/dashboard` card `Review queue`:
  - Có state `limit`, `offset`, `total`.
  - Nút `Trước`/`Sau` hoặc pagination control đơn giản.
  - Disable `Trước` khi `offset=0`.
  - Disable `Sau` khi `offset + items.length >= total`.
  - Reset `offset=0` khi đổi filter `section_role`, `document_id`, `max_confidence` hoặc `limit`.
  - Sau khi bấm `Đã review`, refresh lại page hiện tại; nếu page hiện tại rỗng và `offset > 0`, lùi về page trước.
- Giữ card chỉ hiển thị cho admin như hiện tại.

Docs:
- Cập nhật `README.md` nếu workflow Dashboard review queue thay đổi đáng kể.
- Cập nhật `PROJECT_STATUS.md` và `TASK_NEXT.md` sau khi hoàn thành task.

### Acceptance Criteria

- Dashboard review queue hiển thị tổng số chunk cần review matching filter.
- Admin chuyển trang được bằng `offset`/pagination UI.
- Filter hiện tại được giữ khi chuyển trang.
- Đổi filter hoặc limit đưa queue về trang đầu.
- Mark reviewed trên item hiện tại làm list refresh đúng, không để UI kẹt ở trang rỗng nếu còn dữ liệu ở trang trước.
- User thường vẫn không thấy card review queue và endpoint vẫn trả `403`.
- Frontend vẫn theo luồng `page -> composable -> service -> API`.

### Kiểm Tra Đề Xuất

Backend:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile \
  apps/api/app/schemas/document.py \
  apps/api/app/repositories/document_repository.py \
  apps/api/app/services/document_service.py \
  apps/api/app/routers/documents.py
```

Frontend:

```bash
docker compose run --rm --no-deps web npm run build
```

Smoke API:
- Admin gọi review queue với `limit=5&offset=0`, kiểm tra response có `items`, `total`, `limit`, `offset`.
- Admin gọi `limit=5&offset=5`, kiểm tra không trùng item với page đầu khi đủ dữ liệu.
- Filter `section_role=appendix` vẫn hoạt động với response phân trang.
- User thường gọi review queue vẫn nhận `403`.

Smoke UI:
- Mở Dashboard bằng admin.
- Kiểm tra tổng số item, nút `Trước/Sau`, đổi filter và đổi limit.
- Bấm `Đã review` trên một item rồi xác nhận queue refresh đúng.

Final checks:

```bash
git diff --check
git diff --stat
```
