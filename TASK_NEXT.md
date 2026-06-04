# Task Vừa Hoàn Thành: Chunk Metadata Backfill

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-04

## Phạm Vi Đã Thực Hiện

Đã thêm script backfill nhẹ để populate metadata chunk cho document cũ từ OCR pages đã lưu.

Nguyên tắc vận hành:
- Không thay `document_chunks.text`.
- Không thay `content_hash`.
- Không thay `qdrant_point_id`.
- Không re-embedding.
- Map metadata theo `chunk_index` hiện có và báo mismatch nếu số chunk tái tạo khác số chunk đang lưu.

## Kết Quả Chính

Backend:
- Thêm repository method list document cần backfill metadata chunk.
- Thêm repository method cập nhật metadata chunk theo payload từ module `ocr_chunking`.
- Tái sử dụng `create_chunk_payloads` để metadata backfill nhất quán với worker OCR hiện tại.

Script:
- Thêm `python -m app.scripts.backfill_chunk_metadata`.
- Hỗ trợ `--dry-run`.
- Hỗ trợ `--document-id` repeatable.
- Hỗ trợ `--batch-size`, `--limit`, `--include-complete`.
- In log từng document và summary cuối.

Docs:
- Cập nhật README cách chạy backfill.
- Cập nhật `PROJECT_STATUS.md`.

## Cách Chạy

Dry-run trước:

```bash
docker compose exec -T api python -m app.scripts.backfill_chunk_metadata --dry-run --limit 20
```

Chạy thật theo batch:

```bash
docker compose exec -T api python -m app.scripts.backfill_chunk_metadata --batch-size 20
```

Một document cụ thể:

```bash
docker compose exec -T api python -m app.scripts.backfill_chunk_metadata --document-id <document_id>
```

## Đã Kiểm Tra

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/repositories/document_repository.py apps/api/app/scripts/backfill_chunk_metadata.py
PYTHONPATH=apps/api python3 -m unittest app.services.ocr_chunking.tests.test_pipeline
docker compose exec -T api python -m app.scripts.backfill_chunk_metadata --dry-run --limit 2
docker compose config --quiet
git diff --check
```

Kết quả:
- Backend compile pass.
- Unit test chunking pass 6 mẫu.
- Backfill dry-run chạy được trên DB local.
- Docker Compose config pass.
- Diff check pass.

## Task Tiếp Theo Đề Xuất

1. User management MVP:
   - API/list UI tạo user thường.
   - Admin đổi role `admin/user`.
   - Admin soft-delete hoặc deactivate user.

2. Chunk metadata rollout:
   - Chạy backfill thật trên DB local/dev sau khi review dry-run.
   - Reindex Qdrant nếu cần đưa metadata chi tiết mới vào payload search cho toàn bộ document cũ.
