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

1. Appendix-aware chunking:
   - Nhận diện phần `Phụ lục` trong một văn bản có kèm phụ lục, tách thành section/chunk riêng và gắn metadata truy vết.

## Kế Hoạch Chi Tiết: Appendix-aware Chunking

### Mục Tiêu

Khi OCR/chunk một văn bản có phần phụ lục, hệ thống cần nhận diện được phụ lục ở mức rule-based MVP, không dùng cloud/LLM, và lưu metadata đủ để search/filter/review:
- `section_role=appendix`
- `contains_appendix=true` trong Qdrant payload nếu có metadata chi tiết.
- `section_path` bắt đầu bằng tên phụ lục, ví dụ `["Phụ lục I"]`.
- `requires_review=true` nếu tín hiệu phụ lục yếu hoặc OCR/layout không chắc.

### Phạm Vi MVP

Backend/chunking:
- Cập nhật module `apps/api/app/services/ocr_chunking/`.
- Thêm rule nhận diện heading phụ lục trong normalizer/anchors/classifier/pipeline tùy vị trí code phù hợp.
- Không đổi stack, không thêm service mới.
- Không dùng model cloud hoặc LLM.
- Không thay đổi schema DB nếu `section_role`, `section_path`, `requires_review` đã đủ.

Frontend:
- Chưa cần màn hình mới trong task này.
- Chỉ cần đảm bảo metadata chunk hiện có có thể hiển thị được ở document detail/search result.

### Tín Hiệu Nhận Diện Phụ Lục

Rule mạnh:
- Dòng ngắn dạng heading: `PHỤ LỤC`, `PHỤ LỤC I`, `PHỤ LỤC II`, `PHỤ LỤC 01`, `PHỤ LỤC A`.
- Dòng có cụm `ban hành kèm theo`, `kèm theo Quyết định số`, `kèm theo Công văn số`.
- Heading phụ lục xuất hiện ở đầu trang hoặc sau phần chữ ký/nơi nhận.
- Heading phụ lục đi kèm bảng/danh sách ngay sau đó.

Rule yếu:
- Từ `phụ lục` xuất hiện trong thân câu nhưng không phải heading.
- OCR lỗi dấu/chữ hoa chữ thường nhưng vẫn gần giống `phụ lục`.
- Phụ lục bắt đầu giữa trang, không có khoảng cách layout rõ.

Chống false positive:
- Không đánh `appendix` nếu `phụ lục` chỉ xuất hiện trong câu mô tả, ví dụ `xem phụ lục kèm theo` trong thân văn bản chính.
- Chỉ coi là heading khi dòng ngắn, có dạng tiêu đề, hoặc có anchor `kèm theo...` ngay sau/trước.

### Logic Chunking Đề Xuất

1. Detect appendix anchors:
   - Thêm hàm nhận diện heading phụ lục, ví dụ `is_appendix_heading(line)`.
   - Normalize Unicode, bỏ dấu khi match, nhưng giữ text gốc cho `section_title`.

2. Tạo section boundary:
   - Khi gặp heading phụ lục, đóng section hiện tại.
   - Bắt đầu section mới với role nội bộ/public là `appendix`.
   - `section_path` reset về `[appendix_title]`.

3. Lan truyền context phụ lục:
   - Các chunk sau heading phụ lục giữ `section_role=appendix` hoặc role con nếu có cấu trúc nhỏ hơn.
   - Với role con, `section_path` vẫn bắt đầu bằng phụ lục, ví dụ `["Phụ lục I", "Mục 1"]`.

4. Đánh confidence/review:
   - Rule mạnh: `requires_review=false` nếu OCR confidence đủ tốt.
   - Rule yếu hoặc OCR confidence thấp: `requires_review=true`.
   - Nếu phát hiện bảng sau heading phụ lục, đánh thêm `contains_table=true` nếu pipeline đã hỗ trợ flag này.

5. Qdrant payload:
   - Đảm bảo payload reindex/worker có `section_role`, `section_path`, `requires_review`.
   - Nếu metadata chi tiết đã có `contains_appendix`, đưa vào payload để filter/search sau này.

### Test Cần Có

Thêm hoặc mở rộng unit test trong `apps/api/app/services/ocr_chunking/tests/test_pipeline.py`:
- Văn bản không có phụ lục không tạo chunk `section_role=appendix`.
- Văn bản có `PHỤ LỤC` sau chữ ký tạo chunk appendix.
- Văn bản có nhiều phụ lục `PHỤ LỤC I`, `PHỤ LỤC II` tạo đúng `section_path`.
- Câu thân bài có từ `phụ lục` nhưng không phải heading không bị false positive.
- Phụ lục dạng bảng/danh sách giữ context appendix và không mất source page.
- OCR lỗi nhẹ hoặc heading không rõ đánh `requires_review=true`.

Fixtures tối thiểu:
- Text hành chính có phụ lục sau quyết định/công văn.
- Text chỉ nhắc tới phụ lục trong thân văn bản.
- Text có nhiều phụ lục và mục con.

### Kiểm Tra Sau Khi Làm

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/services/ocr_chunking/*.py apps/api/app/services/ocr_chunking/tests/test_pipeline.py
PYTHONPATH=apps/api python3 -m unittest apps.api.app.services.ocr_chunking.tests.test_pipeline
docker compose run --rm --no-deps web npm run build
git diff --check
```

Nếu có thay đổi payload/reindex:

```bash
docker compose exec -T api python -m app.scripts.backfill_chunk_metadata --dry-run --limit 5
docker compose exec -T api python -m app.scripts.reindex_embeddings --dry-run --limit 20
```

### Acceptance Criteria

- Chunk phụ lục được nhận diện với `section_role=appendix`.
- `section_path` thể hiện đúng tên phụ lục.
- Không false positive với câu thân bài chỉ nhắc tới phụ lục.
- Trường hợp không chắc chắn được đánh `requires_review=true`.
- Unit test pass.
- Không đổi stack và không cần migration DB nếu schema hiện tại đủ dùng.

### Task Sau Đó

1. Review queue UI:
   - Thêm filter trong document detail hoặc dashboard để admin xem nhanh chunks `requires_review=true`, bao gồm các phụ lục OCR không chắc.

2. Appendix search filter:
   - Nếu cần, thêm option `section_role=appendix` rõ ràng trong Dashboard search filter.
