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

## Kế Hoạch Chi Tiết: Review Queue UI và Appendix Search Filter

### Mục Tiêu

Tận dụng metadata chunk đã có (`requires_review`, `section_role=appendix`, `contains_appendix`, `section_path`) để admin nhanh chóng tìm và kiểm tra các chunk OCR/chunking chưa chắc chắn, đặc biệt phụ lục.

Kết quả mong muốn:
- Admin nhìn được danh sách chunk cần review trong document detail hoặc Dashboard.
- Dashboard search có option rõ ràng để lọc `section_role=appendix`.
- Smoke API xác nhận semantic search filter `section_role=appendix` hoạt động.
- Không thêm stack mới, không dùng cloud, không thêm migration nếu schema hiện tại đủ.

### Phạm Vi MVP

Frontend:
- Ưu tiên cập nhật `/documents/[id]` để có filter/chế độ xem nhanh chunks `requires_review=true`.
- Cập nhật `/dashboard` để thêm option `Phụ lục` cho filter vai trò section.
- Không tạo page mới nếu document detail và dashboard đã đủ dùng.
- Không gọi API trực tiếp trong component ngoài luồng sẵn có; giữ `page -> composable -> service -> API`.

Backend:
- Nếu API detail document đã trả `chunks.requires_review`, `section_role`, `section_path`, không cần endpoint mới.
- Semantic search API hiện đã nhận `section_role`; chỉ cần smoke thêm `appendix`.
- Nếu phát hiện response thiếu `contains_appendix`, cân nhắc bổ sung vào schema/result chỉ khi UI thật sự cần hiển thị.

### Luồng UI Đề Xuất

Document detail:
- Trong card `Chunks`, thêm toggle/filter:
  - `Tất cả chunks`
  - `Cần review`
  - `Phụ lục`
  - `Phụ lục cần review`
- Hiển thị counter:
  - Tổng chunks.
  - Số chunks `requires_review=true`.
  - Số chunks `section_role=appendix`.
- Với chunk cần review, hiển thị tag `review`.
- Với chunk phụ lục, hiển thị tag `phụ lục` và `section_path`.
- Không làm mất khả năng xem toàn bộ chunks hiện tại.

Dashboard:
- Trong dropdown `section_role`, thêm option:
  - Label: `Phụ lục`
  - Value: `appendix`
- Search result đã hiển thị metadata chunk, chỉ cần đảm bảo phụ lục dễ nhận biết.

### Backend/Service Kiểm Tra

1. Document detail response:
   - Xác nhận `DocumentChunkRead` có `requires_review`, `section_role`, `section_path`.
   - Nếu đủ, không sửa backend.

2. Semantic search:
   - Dùng payload:

```json
{
  "query": "phụ lục",
  "limit": 5,
  "section_role": "appendix"
}
```

   - Kết quả phải trả toàn bộ `section_role=appendix` nếu có dữ liệu phụ lục đã index.
   - Nếu DB local chưa có phụ lục thật, smoke có thể tạo document/chunk fixture nhỏ qua repository hoặc dùng unit-level service test.

### Test/Smoke Cần Có

Frontend build:

```bash
docker compose run --rm --no-deps web npm run build
```

Backend compile nếu có sửa schema/service:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/document.py apps/api/app/schemas/search.py apps/api/app/services/search_service.py apps/api/app/routers/search.py
```

Semantic search smoke:

```bash
python3 <semantic search appendix filter smoke script>
```

Smoke script nên kiểm tra:
- Login admin.
- Gọi `/api/v1/search/semantic` với `section_role=appendix`.
- Nếu có result, assert mọi result có `section_role == "appendix"`.
- Nếu chưa có dữ liệu appendix local, ghi nhận rõ là filter API pass ở dạng empty-safe hoặc tạo fixture có cleanup.

Manual/browser check:
- Mở `/documents/{document_id}` có chunk `requires_review=true` hoặc phụ lục.
- Bật filter `Cần review`, kiểm tra danh sách chỉ còn chunk review.
- Bật filter `Phụ lục`, kiểm tra chỉ còn chunk appendix.
- Mở `/dashboard`, chọn section role `Phụ lục`, search và kiểm tra request/response.

### Acceptance Criteria

- Document detail có cách xem nhanh chunks `requires_review=true`.
- Document detail có cách xem nhanh chunks `section_role=appendix`.
- Dashboard có option `Phụ lục` cho filter `section_role`.
- Search API smoke với `section_role=appendix` pass.
- Frontend build pass.
- Không đổi stack, không thêm migration nếu không cần.
- Cập nhật `PROJECT_STATUS.md`, `TASK_NEXT.md`; chỉ cập nhật `README.md` nếu workflow người dùng thay đổi đáng kể.

### Rủi Ro Và Cách Xử Lý

- Nếu local DB chưa có chunk phụ lục:
  - Tạo smoke fixture tạm qua API/upload hoặc repository, sau đó cleanup.
  - Hoặc chỉ assert API trả 200 và mọi result nếu có đều là `appendix`, ghi rõ giới hạn.
- Nếu document detail đang render toàn bộ chunk dài:
  - Filter chỉ thay đổi computed list, không refactor lớn.
- Nếu muốn filter `contains_appendix` riêng:
  - Hoãn sau MVP vì `section_role=appendix` đã đủ cho bước này.

### Task Sau Đó

1. Review action:
   - Cho admin đánh dấu một chunk đã review để tắt `requires_review`.

2. Appendix metadata polish:
   - Hiển thị `contains_appendix` hoặc summary phụ lục trong document detail nếu người dùng cần truy vết nhanh hơn.
