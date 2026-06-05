# Task Vừa Hoàn Thành: User Audit Smoke và Chunk Metadata Rollout

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-05

## Phạm Vi Đã Thực Hiện

Đã kiểm thử sâu endpoint audit log theo user và rollout metadata chunk cho toàn bộ dữ liệu local/dev hiện có.

## Kết Quả Chính

User audit:
- Smoke API tạo user tạm, cập nhật profile, reset password và xóa mềm.
- `GET /api/v1/users/{user_id}/audit-logs` trả đủ `user.created`, `user.updated`, `user.password_reset`, `user.deleted`.
- Sửa audit endpoint để vẫn xem được log của user đã soft-delete.

Chunk metadata:
- Sửa backfill để chunk dư trong document mismatch nhận fallback metadata thay vì bị bỏ qua.
- Chunk fallback được gán `doc_group=E`, `chunk_level=paragraph`, `section_role=unknown`, `chunk_confidence=0.0`, `requires_review=true`.
- Thêm helper `build_qdrant_payload` cho script reindex/reprocess để payload Qdrant có metadata nghiệp vụ và metadata chunk.
- Chạy backfill thật trên DB local/dev.
- Reindex Qdrant thật cho toàn bộ active chunks.

Docs:
- Cập nhật `README.md`.
- Cập nhật `PROJECT_STATUS.md`.
- Cập nhật `TASK_NEXT.md`.

## Đã Kiểm Tra

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/repositories/document_repository.py apps/api/app/repositories/user_repository.py apps/api/app/services/user_service.py apps/api/app/services/chunk_payload.py apps/api/app/scripts/backfill_chunk_metadata.py apps/api/app/scripts/reindex_embeddings.py apps/api/app/scripts/reprocess_document.py
python3 <user audit smoke script>
docker compose exec -T api python -m app.scripts.backfill_chunk_metadata --dry-run
docker compose exec -T api python -m app.scripts.backfill_chunk_metadata
docker compose exec -T api python -m app.scripts.reindex_embeddings --dry-run
docker compose exec -T api python -m app.scripts.reindex_embeddings
docker compose exec -T postgres psql -U legal -d legal_doc_ai -c "<chunk metadata count query>"
docker compose exec -T api python <qdrant payload check script>
git diff --check
```

Kết quả:
- Backend compile pass.
- User audit smoke pass, audit log trả đủ 4 event bắt buộc sau soft delete.
- Backfill dry-run sau rollout không còn document thiếu metadata.
- DB xác nhận `active_chunks=600`, `missing_metadata=0`, `requires_review=232`.
- Qdrant reindex pass: `indexed: 600 chunks`.
- Qdrant payload mẫu có metadata chunk mới.
- Diff check pass.

## Task Tiếp Theo Đề Xuất

1. Search filter rollout:
   - Mở rộng API semantic search để filter theo `business_type`, `document_number`, `issued_date`, `doc_group`, `section_role` hoặc `requires_review` nếu cần khai thác metadata đã rollout.

2. Review queue UI:
   - Thêm màn hình hoặc filter trong document detail để admin xem nhanh các chunks `requires_review=true`.
