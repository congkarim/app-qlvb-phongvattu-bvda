# Task Vừa Hoàn Thành: Tích Hợp OCR Chunking Vào Worker Và Qdrant Payload

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-04

## Phạm Vi Đã Thực Hiện

Đã tích hợp module `ocr_chunking` vào OCR worker để workflow OCR/indexing dùng chunking theo nhóm văn bản hành chính tiếng Việt thay cho chunking legacy mặc định.

Pipeline worker hiện tại:
- OCR/extract pages.
- Auto classify/extract metadata nếu chưa review thủ công.
- Chunk bằng `ocr_chunking` theo `doc_type` và nhóm A/B/C/D/E.
- Lưu chunk vào bảng `document_chunks` theo schema hiện có.
- Upsert embedding vào Qdrant kèm metadata chunk chi tiết.
- Có rollback path về `ChunkingService` cũ bằng `CHUNKING_BACKEND=legacy`.

## Kết Quả Chính

Backend:
- Thêm setting `CHUNKING_BACKEND`, mặc định `ocr_chunking`.
- Thêm `apps/api/app/services/ocr_chunking/adapter.py` để map `Chunk` sang payload lưu DB và metadata Qdrant.
- Worker dùng `ocr_chunking` mặc định khi tạo chunks.
- Nếu `CHUNKING_BACKEND=legacy` hoặc backend không hợp lệ, worker fallback về `ChunkingService` cũ.
- `document_chunks` vẫn lưu `text`, `section_title`, `page_from`, `page_to`, `content_hash`.
- Qdrant payload được bổ sung:
  - `chunking_backend`
  - `chunk_doc_type`
  - `doc_group`
  - `chunk_level`
  - `section_role`
  - `section_path`
  - `article_number`, `clause_number`, `point_number`
  - `chunk_confidence`, `ocr_confidence`, `layout_confidence`, `classification_confidence`
  - `source_anchor`
  - `contains_table`, `contains_signature`, `contains_appendix`
  - `requires_review`
  - `fallback_info`, `fallback_used`, `fallback_reason`
  - `entities` và một số entity flattened cho filter/rerank sau này.

Docs/config:
- Cập nhật `docker-compose.yml` cho `api` và `worker`.
- Cập nhật `apps/api/.env.example`.
- Cập nhật `README.md`, `PROJECT_STATUS.md` và README module `ocr_chunking`.

## Đã Kiểm Tra

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/core/config.py apps/api/app/repositories/document_repository.py apps/api/app/workers/ocr_worker.py apps/api/app/services/ocr_chunking/*.py apps/api/app/services/ocr_chunking/tests/test_pipeline.py
PYTHONPATH=apps/api python3 -m unittest app.services.ocr_chunking.tests.test_pipeline
docker compose config --quiet
```

Kết quả:
- Compile pass.
- Unit test pass 6/6.
- Docker Compose config pass.

Ghi chú:
- Lệnh compile thông thường từng bị chặn bởi `__pycache__` root-owned sẵn trong `apps/api/app/core`, nên kiểm tra compile dùng `PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache` để không ghi pycache vào repo.

## Task Tiếp Theo Đề Xuất

1. Preview file inline trong detail:
   - Preview PDF/image/text cạnh OCR text và metadata.
   - Fallback download cho DOCX/XLSX.

2. Metadata chunk trong PostgreSQL nếu cần UI chi tiết:
   - Thêm migration cho `section_role`, `section_path`, `doc_group`, `requires_review`.
   - Hiển thị role/path/confidence trong trang document detail.
