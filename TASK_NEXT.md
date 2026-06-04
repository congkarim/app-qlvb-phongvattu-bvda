# Task Vừa Hoàn Thành: Metadata Chunk Trong PostgreSQL Và UI Detail

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-04

## Phạm Vi Đã Thực Hiện

Đã đưa metadata chunk quan trọng từ pipeline `ocr_chunking` vào PostgreSQL để trang detail hiển thị trực tiếp role/path/confidence của chunks, không chỉ phụ thuộc vào Qdrant payload.

## Kết Quả Chính

Backend/database:
- Thêm migration `0008_document_chunk_metadata`.
- Bổ sung các cột vào `document_chunks`:
  - `doc_group`
  - `chunk_level`
  - `section_role`
  - `section_path`
  - `chunk_confidence`
  - `requires_review`
- Thêm index cho:
  - `doc_group`
  - `section_role`
  - `requires_review`
- Mở rộng SQLAlchemy model `DocumentChunk`.
- Repository lưu metadata khi tạo chunk mới và khi reprocess/replace chunks.
- API detail trả metadata chunk qua `DocumentChunkRead`.

Frontend:
- Mở rộng type `DocumentChunk`.
- Trang `/documents/[id]` hiển thị trong card `Chunks`:
  - Nhóm chunk.
  - Role chunk.
  - Cờ `Cần review`.
  - Confidence.
  - Section path.

## Đã Kiểm Tra

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/models/document.py apps/api/app/schemas/document.py apps/api/app/repositories/document_repository.py apps/api/app/workers/ocr_worker.py apps/api/alembic/versions/0008_document_chunk_metadata.py
docker compose run --rm --no-deps web npm run build
docker compose config --quiet
docker compose run --rm api alembic upgrade head
```

Kết quả:
- Backend compile pass.
- Frontend build pass.
- Docker Compose config pass.
- Alembic upgrade pass, DB local lên revision `0008_document_chunk_metadata`.
- Frontend build vẫn có warning chunk PrimeVue lớn như trước, không fail.

## Task Tiếp Theo Đề Xuất

1. RBAC nhẹ:
   - Role `admin` và `user`.
   - Chỉ admin được reprocess, xóa source file, đổi thứ tự source file.
   - User thường chỉ upload/search/xem/sửa metadata theo quyền được cấp.

2. Chunk metadata backfill:
   - Reprocess các document cũ để populate metadata chunk mới.
   - Hoặc viết script backfill nhẹ nếu cần giữ nguyên OCR text hiện có.
