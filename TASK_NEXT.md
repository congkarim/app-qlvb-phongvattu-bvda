# Task Vừa Hoàn Thành: Appendix-aware Chunking

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-05

## Phạm Vi Đã Thực Hiện

Đã thêm nhận diện phụ lục rule-based trong pipeline chunking OCR text, không đổi stack và không thêm migration DB.

## Kết Quả Chính

Backend/chunking:
- Thêm rule nhận diện heading phụ lục trong `apps/api/app/services/ocr_chunking/pipeline.py`.
- Hỗ trợ các heading như `PHỤ LỤC`, `PHỤ LỤC I`, `PHỤ LỤC II`, `PHỤ LỤC 01`, `PHỤ LỤC A`.
- Tách phụ lục thành section/chunk riêng với `section_role=appendix`.
- Giữ `section_path` bắt đầu bằng tên phụ lục, ví dụ `["PHỤ LỤC I"]`.
- Lan truyền context phụ lục cho role con, ví dụ `["PHỤ LỤC I", "Điều 1"]`.
- Chống false positive khi `phụ lục` chỉ xuất hiện trong câu thân bài hoặc điều khoản.
- Phụ lục có OCR/layout yếu được đánh `requires_review=true`.
- `contains_appendix` được đưa vào Qdrant payload khi worker xử lý OCR và khi reindex từ DB qua `build_qdrant_payload`.

Tests:
- Bổ sung test phụ lục sau chữ ký.
- Bổ sung test nhiều phụ lục và context con.
- Bổ sung test false positive khi thân bài chỉ nhắc tới phụ lục.
- Bổ sung test phụ lục OCR yếu cần review.

Docs:
- Cập nhật `README.md`.
- Cập nhật `PROJECT_STATUS.md`.
- Cập nhật `TASK_NEXT.md`.

## Đã Kiểm Tra

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/services/ocr_chunking/*.py apps/api/app/services/ocr_chunking/tests/test_pipeline.py apps/api/app/services/chunk_payload.py
PYTHONPATH=apps/api python3 -m unittest apps.api.app.services.ocr_chunking.tests.test_pipeline
docker compose exec -T api python -m app.scripts.backfill_chunk_metadata --dry-run --limit 5
docker compose exec -T api python -m app.scripts.reindex_embeddings --dry-run --limit 20
docker compose run --rm --no-deps web npm run build
git diff --check
```

Kết quả:
- Backend compile pass.
- Unit test `ocr_chunking` pass 10 test.
- Backfill dry-run: không còn document thiếu metadata.
- Reindex dry-run: `20 chunks`.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.
- Diff check pass.

## Task Tiếp Theo Đề Xuất

1. Review queue UI:
   - Thêm filter trong document detail hoặc dashboard để admin xem nhanh chunks `requires_review=true`, bao gồm các phụ lục OCR không chắc.

2. Appendix search filter:
   - Thêm option `section_role=appendix` rõ ràng trong Dashboard search filter và smoke API cho filter này.
