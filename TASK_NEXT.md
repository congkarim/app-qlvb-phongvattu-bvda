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

1. Queue pagination polish:
   - Thêm phân trang `offset` trong Dashboard review queue nếu số chunk review lớn.
   - Hiển thị tổng số item nếu cần endpoint count.
   - Giữ frontend theo luồng `page -> composable -> service -> API`.

2. Smoke API auth wrapper:
   - Nếu cần kiểm tra sát HTTP hơn, bổ sung smoke dùng login admin và gọi trực tiếp `/api/v1/documents/chunks/review-queue`, `/api/v1/search/semantic`, `/api/v1/documents/{document_id}/chunks/{chunk_id}/reviewed`.
   - Có thể dùng lại fixture/script hiện có để seed và cleanup dữ liệu.
