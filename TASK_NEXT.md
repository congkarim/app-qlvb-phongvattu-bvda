# Task Vừa Hoàn Thành: Search Filter Rollout

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-05

## Phạm Vi Đã Thực Hiện

Đã mở rộng semantic search để khai thác metadata nghiệp vụ và metadata chunk đã rollout.

## Kết Quả Chính

Backend:
- `POST /api/v1/search/semantic` nhận thêm filter `business_type`, `document_number`, `issued_date`, `doc_group`, `section_role`, `requires_review`.
- Search result trả thêm metadata document/chunk để frontend hiển thị và debug filter.
- Qdrant vector hits dùng filter payload tương ứng.
- Vector hits được đối chiếu lại với PostgreSQL active chunks để không trả dữ liệu soft-delete hoặc stale payload.
- PostgreSQL keyword candidates dùng cùng bộ filter với vector search.

Frontend:
- Search service/composable nhận `SemanticSearchFilters`.
- Dashboard có filter UI cho loại nghiệp vụ, số văn bản, ngày ban hành, nhóm chunk, vai trò section, trạng thái review và limit.
- Kết quả search hiển thị metadata nghiệp vụ, metadata chunk và tag `review` nếu chunk cần kiểm tra.

Docs:
- Cập nhật `README.md`.
- Cập nhật `PROJECT_STATUS.md`.
- Cập nhật `TASK_NEXT.md`.

## Đã Kiểm Tra

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/search.py apps/api/app/routers/search.py apps/api/app/services/qdrant_service.py apps/api/app/repositories/document_repository.py apps/api/app/services/search_service.py
docker compose run --rm --no-deps web npm run build
python3 <semantic search filter smoke script>
git diff --check
```

Kết quả:
- Backend compile pass.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.
- Smoke API pass cho `doc_group=A`, `section_role=clause`, `requires_review=true`, `document_number=1589/QĐ-BYT`, `business_type=decision`, `issued_date=2025-08-04`.
- Diff check pass.

## Task Tiếp Theo Đề Xuất

1. Review queue UI:
   - Thêm màn hình hoặc filter trong document detail để admin xem nhanh các chunks `requires_review=true`.

2. Search filter refinement:
   - Nếu cần, bổ sung date range cho `issued_date` và dropdown option động từ dữ liệu thật thay vì option tĩnh.
