# Trạng Thái Dự Án

Cập nhật lần cuối: 2026-06-05

## Giai Đoạn Hiện Tại

MVP end-to-end đã được triển khai, đã kiểm tra thủ công và workflow web cơ bản đã được hoàn thiện.

Dự án hiện đang ở trạng thái có thể chạy đồng thời backend, worker, database, Qdrant, Redis và frontend Nuxt bằng Docker Compose. Người dùng có thể đăng nhập bằng admin local, thao tác workflow MVP từ browser: upload văn bản, mở chi tiết, theo dõi trạng thái OCR/extract, search và mở lại document nguồn.

## Đã Xây Dựng

Hạ tầng agent:
- `AGENTS.md`
- `.agents/skills/backend-fastapi/SKILL.md`
- `.agents/skills/frontend-nuxt/SKILL.md`
- `.agents/skills/ocr-pipeline/SKILL.md`
- `.agents/skills/semantic-search-rag/SKILL.md`
- `.agents/skills/database-designer/SKILL.md`
- `.agents/skills/solution-architect/SKILL.md`
- `.agents/skills/project-git-manager/SKILL.md`

Quản lý repo:
- Đã thêm skill `project-git-manager` để quy định workflow git cho đầu task, trong task và khi hoàn thành task.
- Skill yêu cầu cập nhật `PROJECT_STATUS.md`, `TASK_NEXT.md` hoặc `README.md` khi task làm thay đổi trạng thái/kế hoạch/cách chạy dự án.
- Skill quy định commit có chọn lọc sau khi task hoàn thành và kiểm tra phù hợp đã chạy.

Docker services:
- `api`
- `worker`
- `web`
- `postgres`
- `redis`
- `qdrant`

Backend skeleton:
- FastAPI app.
- Health endpoint.
- Auth login skeleton.
- Upload API.
- API danh sách/chi tiết văn bản.
- Model và repository cho OCR job.
- Semantic search endpoint.
- Alembic migration ban đầu cho:
  - `users`
  - `departments`
  - `documents`
  - `document_pages`
  - `document_chunks`
  - `ocr_jobs`

Worker:
- Poll OCR job đang pending.
- Trích xuất text trực tiếp cho `.txt`, `.md`, `.docx`, `.xlsx`, `.xls`.
- PDF có text nhúng được trích xuất trực tiếp bằng `pypdfium2` để giữ Unicode tiếng Việt.
- OCR thật cho PDF/image scan bằng PaddleOCR/OpenCV khi page không có text nhúng.
- OCR scan tiếng Việt mặc định chạy `OCR_ENGINE=paddle_vietocr`: PaddleOCR detect text box, VietOCR recognize crop tiếng Việt.
- PaddleOCR baseline vẫn giữ được bằng `OCR_ENGINE=paddleocr`.
- Render PDF scan thành image từng page bằng `pypdfium2`.
- Preprocess ảnh bằng OpenCV trước OCR, hỗ trợ `OCR_PREPROCESS_MODE=auto/raw/clahe/threshold`.
- Lưu OCR/extracted text theo page logic.
- Tạo document chunks, giới hạn `section_title` ngắn hơn schema PostgreSQL để tránh lỗi insert.
- Đã thêm module chunking OCR text mới tại `apps/api/app/services/ocr_chunking/` cho văn bản hành chính tiếng Việt:
  - Input hỗ trợ OCR text theo document/page/block, bbox, confidence và layout confidence.
  - Detect `doc_type` theo thể thức văn bản, map vào nhóm A/B/C/D/E và chọn strategy riêng cho từng nhóm.
  - Output trả dataclass `Chunk` có `to_dict()` đúng JSON schema retrieval/RAG, gồm path, role, page/bbox, confidence, flags review/table/signature/appendix, entities và fallback info.
  - Nhận diện phụ lục rule-based từ heading `PHỤ LỤC`, `PHỤ LỤC I/II/01/A` hoặc dòng đính kèm độc lập, tách section/chunk `section_role=appendix`, giữ `section_path` theo tên phụ lục và tránh false positive khi chỉ nhắc tới phụ lục trong thân câu.
  - Worker mặc định dùng module mới qua `CHUNKING_BACKEND=ocr_chunking`; có thể rollback tạm thời bằng `CHUNKING_BACKEND=legacy`.
  - Migration `0008_document_chunk_metadata` bổ sung `doc_group`, `chunk_level`, `section_role`, `section_path`, `chunk_confidence`, `requires_review` vào `document_chunks`.
  - Metadata chi tiết hơn như fallback/entities vẫn được đưa vào Qdrant payload.
  - Backfill metadata chunk đã chạy trên DB local/dev, không còn active chunk thiếu metadata. Chunk dư khi số chunk sinh lại lệch số chunk cũ được đánh fallback `requires_review=true`.
- Tạo embedding qua backend cấu hình được: fake deterministic cho dev hoặc local `sentence-transformers`.
- Upsert vector vào Qdrant.
- Chuyển document sang trạng thái `searchable`.
- Đánh document/job `failed` với error rõ ràng cho định dạng lỗi hoặc unsupported như `.doc`.

Frontend skeleton:
- Nuxt 3 app.
- PrimeVue plugin.
- TailwindCSS.
- Pinia auth store.
- Các page:
  - `/login`
  - `/dashboard`
  - `/documents`
  - `/upload`
  - `/documents/[id]`
- Cấu trúc service/composable:
  - `page -> composable -> service -> API`

Auth MVP:
- API seed admin local khi khởi động nếu chưa tồn tại.
- Admin mặc định cho Docker Compose: `admin@example.com` / `admin123`.
- Frontend lưu access token bằng cookie.
- Frontend lưu user role bằng cookie sau login.
- API client frontend tự gắn `Authorization: Bearer <token>`.
- Frontend có route guard cơ bản: chưa login thì chuyển về `/login`, đã login thì không quay lại `/login`.
- RBAC nhẹ:
  - `admin`: được reprocess, thêm/xóa/đổi thứ tự source file.
  - `user`: được upload, search, xem tài liệu/source file và sửa metadata.

Workflow web đã hoàn thiện:
- `/upload` có hai mode: một tệp là một văn bản, hoặc nhiều tệp thuộc cùng một văn bản nghiệp vụ.
- `/upload` có trường `Tên văn bản`; mode nhiều tệp bắt buộc nhập tên văn bản và hiển thị danh sách tệp nguồn đã chọn.
- `/upload` có mode `Zip cùng văn bản` để upload một `.zip` thành một document gồm nhiều source files.
- `/upload` cho phép nhập metadata nghiệp vụ dùng chung: số văn bản, ngày ban hành, đơn vị ban hành và loại nghiệp vụ.
- `/documents` hỗ trợ tìm theo tên, filename, số văn bản hoặc đơn vị ban hành; lọc/sort theo loại nghiệp vụ và ngày ban hành.
- `/documents/[id]` hiển thị metadata, OCR job status, OCR text, chunks và tự polling tới khi document `searchable`.
- `/documents/[id]` hiển thị metadata nghiệp vụ gồm số văn bản, ngày ban hành, đơn vị ban hành và loại nghiệp vụ.
- `/documents/[id]` cho phép sửa tên văn bản và metadata nghiệp vụ sau upload; mỗi lần lưu ghi audit log `document.metadata_updated`.
- `/documents/[id]` hiển thị metadata OCR tự trích xuất theo thể thức văn bản hành chính: loại văn bản, confidence, số/ký hiệu, ngày/địa danh ban hành, đơn vị ban hành, trích yếu, nơi nhận, người ký, chức vụ, dấu, phụ lục và số trang.
- `/documents/[id]` cho phép sửa thủ công các metadata OCR; khi lưu sẽ đánh dấu `metadata_source=manual` và `metadata_reviewed_at`.
- Reprocess không ghi đè metadata đã được sửa/review thủ công; kết quả auto extraction mới chỉ ghi audit log `document.metadata_auto_extracted` với `applied=false`.
- `/documents/[id]` hiển thị card `Tệp nguồn` để xem một hoặc nhiều file nguồn thuộc cùng document.
- `/documents/[id]` có nút `Xem trước` để preview inline PDF/image/text cạnh metadata/OCR text; nút `Mở` vẫn mở tab mới hoặc download fallback cho DOCX/XLSX.
- `/documents/[id]` cho phép admin thêm source files, đổi thứ tự file và soft-delete source file; mỗi thay đổi tạo reprocess job async.
- `/documents/[id]` có action reprocess dành cho admin, khóa nút khi document đang `ocr_pending`, `ocr_running`, `reprocess_pending`, `reprocess_running` hoặc `chunking`.
- `/documents/[id]` hiển thị audit OCR/reprocess job gồm `job_type`, `status`, `reason`, attempts, error message và thời gian tạo/cập nhật.
- `/documents/[id]` có filter trong card `Chunks` để xem tất cả chunk, chunk cần review, phụ lục và phụ lục cần review; hiển thị counter tổng chunk, `requires_review=true` và `section_role=appendix`.
- `/documents/[id]` cho phép admin đánh dấu chunk `requires_review=true` là đã review; thao tác ghi audit log `document_chunk.reviewed` và cập nhật payload Qdrant để search filter đồng bộ.
- `/documents` có refresh action, filter/search/sort, loading state, empty state và link sang detail.
- `/dashboard` có validation search input, loading/empty/error state, filter semantic search theo metadata nghiệp vụ/chunk, bao gồm option `section_role=appendix`, và result link sang document nguồn.
- `/dashboard` có card `Review queue` chỉ dành cho admin để xem chunks `requires_review=true`, lọc theo phụ lục/document/confidence thấp, mở document detail và đánh dấu chunk đã review ngay từ queue.
- `/users` cho phép admin xem audit log theo từng user, gồm actor, action, thời gian và metadata thao tác quản trị.

## Đã Kiểm Tra Thủ Công

Các kiểm tra sau đã chạy thành công:

Appendix data smoke kiểm tra ngày 2026-06-05:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/scripts/smoke_appendix_data.py
docker compose exec -T api python -m app.scripts.smoke_appendix_data
```

Kết quả:
- Thêm fixture `tests/fixtures/appendix_smoke/appendix_review_fixture.txt` có heading phụ lục và nội dung vật tư.
- Thêm script `python -m app.scripts.smoke_appendix_data` để seed document smoke tạm có chunk `section_role=appendix`, `requires_review=true`, confidence thấp và index chunk vào Qdrant.
- Smoke xác nhận document detail có chunk phụ lục thật, review queue filter `section_role=appendix` trả chunk đó và semantic search filter `section_role=appendix` trả result thật thay vì chỉ pass empty-safe.
- Smoke gọi action review chunk, xác nhận queue appendix không còn chunk đã review và search `requires_review=true` không còn trả chunk đó.
- Mặc định script cleanup document smoke và Qdrant point; có thể dùng `--keep-data` để giữ dữ liệu kiểm tra UI thủ công.

Review queue dashboard kiểm tra ngày 2026-06-05:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/document.py apps/api/app/repositories/document_repository.py apps/api/app/services/document_service.py apps/api/app/routers/documents.py
docker compose run --rm --no-deps web npm run build
python3 <review queue smoke script>
git diff --check
```

Kết quả:
- Thêm endpoint admin-only `GET /api/v1/documents/chunks/review-queue`.
- Endpoint trả danh sách chunk active `requires_review=true` kèm document title/id, metadata chunk, confidence, text preview và hỗ trợ filter `section_role`, `document_id`, `max_confidence`.
- Dashboard hiển thị card `Review queue` chỉ cho admin, có filter tất cả/phụ lục/unknown, confidence thấp, document id, limit và action `Đã review`.
- Smoke queue pass: admin nhận 10 chunks cần review, filter `max_confidence=0.65` trả 10 chunks hợp lệ, filter `section_role=appendix` trả 0 do local chưa có appendix indexed trong queue.
- Smoke phân quyền pass: user thường `queue-smoke-de1c52133fac@example.com` gọi review queue nhận 403.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.

Review action cho chunk kiểm tra ngày 2026-06-05:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/repositories/document_repository.py apps/api/app/services/qdrant_service.py apps/api/app/services/document_service.py apps/api/app/routers/documents.py apps/api/app/schemas/document.py
docker compose run --rm --no-deps web npm run build
python3 <review chunk smoke script>
python3 <review chunk user forbidden smoke script>
git diff --check
```

Kết quả:
- Thêm endpoint admin-only `PATCH /api/v1/documents/{document_id}/chunks/{chunk_id}/reviewed`.
- Endpoint cập nhật `document_chunks.requires_review=false`, ghi audit log `document_chunk.reviewed` trên document và cập nhật Qdrant payload bằng `set_payload`.
- Trang `/documents/[id]` hiển thị nút `Đã review` cho admin trên chunk đang cần review; sau thao tác refresh detail và giữ filter hiện tại.
- Smoke review pass với document `419a80f8-dc60-4148-a62d-c55a6acf6bc9`, chunk `eaed75ab-b7e9-43e8-9ee7-0a005250a413`: response/detail đều `requires_review=false`, audit log xuất hiện và search `requires_review=true` không còn trả chunk này.
- Smoke phân quyền pass: user thường `review-smoke-e49755296dac@example.com` gọi endpoint nhận 403.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.

Review queue UI và appendix search filter kiểm tra ngày 2026-06-05:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/document.py apps/api/app/schemas/search.py apps/api/app/services/search_service.py apps/api/app/routers/search.py
docker compose run --rm --no-deps web npm run build
python3 <semantic search appendix filter smoke script>
git diff --check
```

Kết quả:
- Trang `/documents/[id]` có filter card `Chunks` cho tất cả, cần review, phụ lục và phụ lục cần review.
- Card `Chunks` hiển thị counter tổng chunk, chunk cần review và chunk phụ lục; tag phụ lục dùng label `Phụ lục`.
- Dashboard search có option `Phụ lục` cho filter `section_role=appendix`.
- Semantic search smoke login admin và gọi `POST /api/v1/search/semantic` với `section_role=appendix`; API trả 200 và mọi result nếu có đều là appendix.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.

User audit UI kiểm tra ngày 2026-06-05:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/audit.py apps/api/app/schemas/document.py apps/api/app/services/user_service.py apps/api/app/routers/users.py
docker compose run --rm --no-deps web npm run build
```

Kết quả:
- Backend compile pass cho schema audit dùng chung, user service và user router.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.
- Thêm endpoint admin-only `GET /api/v1/users/{user_id}/audit-logs`.
- Trang `/users` có nút `Audit` để tải và hiển thị audit log của từng user.

User audit smoke và chunk metadata rollout kiểm tra ngày 2026-06-05:

```bash
python3 <user audit smoke script>
docker compose exec -T api python -m app.scripts.backfill_chunk_metadata --dry-run
docker compose exec -T api python -m app.scripts.backfill_chunk_metadata
docker compose exec -T api python -m app.scripts.backfill_chunk_metadata --dry-run
docker compose exec -T api python -m app.scripts.reindex_embeddings --dry-run
docker compose exec -T api python -m app.scripts.reindex_embeddings
docker compose exec -T postgres psql -U legal -d legal_doc_ai -c "<chunk metadata count query>"
docker compose exec -T api python <qdrant payload check script>
```

Kết quả:
- User audit smoke pass cho user tạm `audit-smoke-92eb7147bf@example.com`: tạo, cập nhật, reset mật khẩu, xóa mềm và `GET /api/v1/users/{user_id}/audit-logs` trả đủ `user.created`, `user.updated`, `user.password_reset`, `user.deleted`.
- Sửa audit endpoint để vẫn xem được audit log của user đã soft-delete.
- Sửa backfill để chunk dư khi mismatch nhận fallback metadata và `requires_review=true`, tránh bị quét lặp.
- Backfill dry-run ban đầu: 13 documents, 459 chunks dự kiến cập nhật, 7 documents mismatch.
- Backfill thật hoàn tất; lần chạy cuối xử lý 2 documents còn thiếu, cập nhật 127 chunks và đánh fallback 141 chunks.
- Backfill dry-run sau rollout: `scanned_documents=0`, `missing_metadata=0`.
- Reindex Qdrant thật: `indexed: 600 chunks`.
- DB xác nhận `active_chunks=600`, `missing_metadata=0`, `requires_review=232`.
- Qdrant payload mẫu có `doc_group=A`, `chunk_level=subsection`, `section_role=clause`, `section_path`, `chunk_confidence=0.9`, `requires_review=false`.

Search filter rollout kiểm tra ngày 2026-06-05:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/search.py apps/api/app/routers/search.py apps/api/app/services/qdrant_service.py apps/api/app/repositories/document_repository.py apps/api/app/services/search_service.py
docker compose run --rm --no-deps web npm run build
python3 <semantic search filter smoke script>
git diff --check
```

Kết quả:
- API `POST /api/v1/search/semantic` hỗ trợ filter `business_type`, `document_number`, `issued_date`, `doc_group`, `section_role`, `requires_review`.
- Search service áp filter cho cả Qdrant vector hits và PostgreSQL keyword candidates; vector hits được đối chiếu lại với DB active chunks để tránh trả dữ liệu soft-delete/stale payload.
- Dashboard có filter UI cho nghiệp vụ, số văn bản, ngày ban hành, nhóm chunk, role section, trạng thái cần review và limit.
- Smoke pass cho từng filter: `doc_group=A`, `section_role=clause`, `requires_review=true`, `document_number=1589/QĐ-BYT`, `business_type=decision`, `issued_date=2025-08-04`.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.

Appendix-aware chunking kiểm tra ngày 2026-06-05:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/services/ocr_chunking/*.py apps/api/app/services/ocr_chunking/tests/test_pipeline.py apps/api/app/services/chunk_payload.py
PYTHONPATH=apps/api python3 -m unittest apps.api.app.services.ocr_chunking.tests.test_pipeline
docker compose exec -T api python -m app.scripts.backfill_chunk_metadata --dry-run --limit 5
docker compose exec -T api python -m app.scripts.reindex_embeddings --dry-run --limit 20
docker compose run --rm --no-deps web npm run build
git diff --check
```

Kết quả:
- Pipeline nhận diện heading phụ lục và tạo chunk `section_role=appendix`.
- Phụ lục sau chữ ký/nơi nhận giữ `section_path` như `PHỤ LỤC I`.
- Nhiều phụ lục giữ context con, ví dụ `["PHỤ LỤC I", "Điều 1"]`.
- Câu thân bài chỉ nhắc tới phụ lục không bị false positive.
- Phụ lục OCR/layout yếu được đánh `requires_review=true`.
- Unit test `ocr_chunking` pass 10 test.
- Backfill dry-run không còn document thiếu metadata; reindex dry-run xác nhận 20 chunks.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.

```bash
docker compose up --build
```

```bash
curl http://localhost:8000/health
```

Metadata nghiệp vụ kiểm tra ngày 2026-06-04:

```bash
docker compose config --quiet
docker compose run --rm --no-deps api python -m py_compile app/models/document.py app/schemas/document.py app/repositories/document_repository.py app/services/document_service.py app/routers/documents.py
docker compose run --rm --no-deps api python -m py_compile alembic/versions/0006_document_business_metadata.py
docker compose run --rm api alembic upgrade head
docker compose run --rm --no-deps web npm run build
docker compose up -d api web
curl -fsS http://localhost:8000/health
curl -fsS -I http://localhost:3000/login
```

Kết quả:
- Alembic đã nâng DB local từ `0005_document_files` lên `0006_document_business_metadata`.
- Frontend build thành công qua Docker; build có warning chunk PrimeVue lớn như trước, không fail.
- `npm run build` trực tiếp trên host fail vì `apps/web/node_modules/.bin/nuxt` không tồn tại; workflow Docker vẫn chạy được.
- Smoke upload `metadata-smoke.txt` với `document_number=123/CV-VT`, `issued_date=2026-06-04`, `issuing_agency=Phòng Vật tư`, `business_type=incoming_dispatch` trả đúng metadata trong response.
- `GET /api/v1/documents?q=123%2FCV-VT&business_type=incoming_dispatch&sort_by=issued_date&sort_dir=desc` trả đúng document smoke và worker đã chuyển sang `searchable`.
- `/upload` và `/documents` redirect `302 /login` khi chưa đăng nhập, `/login` trả 200.

Sửa metadata sau upload kiểm tra ngày 2026-06-04:

```bash
docker compose config --quiet
docker compose run --rm --no-deps api python -m py_compile app/schemas/document.py app/repositories/document_repository.py app/services/document_service.py app/routers/documents.py
docker compose run --rm --no-deps web npm run build
curl -fsS -X PATCH http://localhost:8000/api/v1/documents/{document_id}/metadata \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Metadata smoke updated","document_number":"456/CV-VT","issued_date":"2026-06-04","issuing_agency":"Phòng Vật tư cập nhật","business_type":"outgoing_dispatch"}'
curl -fsS http://localhost:8000/api/v1/documents/{document_id} -H "Authorization: Bearer <token>"
curl -fsS -I http://localhost:3000/login
curl -fsS -I http://localhost:3000/documents/{document_id}
```

Kết quả:
- `PATCH /api/v1/documents/{id}/metadata` cập nhật được title, số văn bản, ngày ban hành, đơn vị ban hành và loại nghiệp vụ.
- Detail response có audit event `document.metadata_updated`.
- Frontend build pass qua Docker; build có warning chunk PrimeVue lớn như trước, không fail.
- `/login` trả 200, detail route redirect `302 /login` khi chưa đăng nhập.

Xem/download source file khi sửa metadata kiểm tra ngày 2026-06-04:

```bash
docker compose config --quiet
docker compose run --rm --no-deps api python -m py_compile app/repositories/document_repository.py app/services/document_service.py app/routers/documents.py
docker compose run --rm --no-deps web npm run build
curl -fsS -I http://localhost:3000/login
curl -fsS -I http://localhost:3000/documents/{document_id}
```

Kết quả:
- `GET /api/v1/documents/{document_id}/files/{file_id}/download` trả 200, `content-disposition: inline` và không expose file path server.
- File id sai trả 404.
- Nút `Xem` trong card `Tệp nguồn` dùng API blob có auth header; PDF/image/text mở tab mới, định dạng Office fallback download.
- Frontend build pass qua Docker; build có warning chunk PrimeVue lớn như trước, không fail.
- `/login` trả 200, detail route redirect `302 /login` khi chưa đăng nhập.

Tự động lưu metadata sau OCR kiểm tra ngày 2026-06-04:

```bash
docker compose config --quiet
docker compose run --rm --no-deps api python -m py_compile app/models/document.py app/schemas/document.py app/repositories/document_repository.py app/services/document_classifier_service.py app/services/document_service.py app/workers/ocr_worker.py app/routers/documents.py app/scripts/check_document_classifier.py alembic/versions/0007_document_ocr_metadata.py
docker compose run --rm --no-deps api python -m app.scripts.check_document_classifier
docker compose run --rm api alembic upgrade head
docker compose run --rm --no-deps web npm run build
docker compose up -d api worker web
```

Kết quả:
- Thêm migration `0007_document_ocr_metadata` và đã nâng DB local lên head.
- Classifier local/rule-based pass cho các mẫu `CV`, `QĐ`, `TB`, `BB`, `GM`, `UNKNOWN`.
- OCR worker tự lưu metadata sau OCR/reprocess khi document chưa được review thủ công.
- Smoke công văn text lưu được `document_type=CV`, `document_number=789/CV-BV`, `document_symbol=CV-BV`, `issued_date=2026-06-04`, `issued_place=Hà Nội`, `metadata_source=auto`.
- Sau khi sửa metadata thủ công, reprocess giữ nguyên metadata thủ công và chỉ audit auto extraction mới với `applied=false`.
- Frontend build pass qua Docker; build có warning chunk PrimeVue lớn như trước, không fail.

Test upload:

```bash
printf 'Điều 1. Quy định về quản lý vật tư. Khoản 1. Văn bản được OCR mô phỏng và lập chỉ mục semantic search.' > sample.txt

curl -X POST "http://localhost:8000/api/v1/documents/upload?document_type=document" \
  -F "file=@sample.txt"
```

Test trích xuất/OCR đã chạy thành công cho:
- `.txt`: đọc text trực tiếp, document chuyển `searchable`.
- `.docx`: trích xuất paragraph/table text, document chuyển `searchable`.
- `.xlsx`: trích xuất sheet/row text, document chuyển `searchable`.
- `.png`: OCR thật bằng PaddleOCR, document chuyển `searchable`.
- `.pdf`: trích xuất text nhúng trước, fallback OCR cho page scan, document chuyển `searchable`.
- `.doc`: document/job chuyển `failed` với message yêu cầu convert sang `.docx` hoặc `.pdf`.

Test semantic search:

```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query":"quản lý vật tư","limit":5}'
```

Frontend routes đã kiểm tra:
- `http://localhost:3000/` redirect sang `/dashboard`.
- `http://localhost:3000/dashboard` trả 200.
- `http://localhost:3000/documents` trả 200.
- Browser workflow đã được chuẩn bị cho upload -> detail polling -> search.

Auth kiểm tra ngày 2026-05-31:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

Kết quả: HTTP 200, response có `access_token` và `token_type= bearer`.

OCR tiếng Việt kiểm tra ngày 2026-06-01:

```bash
docker compose config
docker compose build api worker
docker compose up -d api worker
docker compose exec -T worker sh -lc 'python -m py_compile /app/app/core/config.py /app/app/services/document_content_service.py /app/app/services/ocr/*.py /app/app/scripts/benchmark_ocr_vi.py'
curl -fsS http://localhost:8000/health
```

Kết quả `OCR_ENGINE=paddle_vietocr` trên fixture `tests/fixtures/ocr_vi/sample_001.png`:

```text
confidence=0.9259
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc
Điều 1. Phạm vi điều chỉnh đấu thầu
Khoản 1. Văn bản scan phải giữ dấu tiếng Việt.
Số 74/VBHN-VPQH ngày 15 tháng 5 năm 2025.
```

Benchmark fixture:

```text
paddleocr: CER 0.0053, WER 0.0238, accent loss 0.0294, 34.944s
paddle_vietocr: CER 0.0, WER 0.0, accent loss 0.0, 49.487s
```

OCR fixture mở rộng kiểm tra ngày 2026-06-02:

```bash
docker compose config --quiet
docker compose run --rm --no-deps worker python -m py_compile /app/app/scripts/benchmark_ocr_vi.py
docker compose run --rm --no-deps -e OCR_PREPROCESS_MODE=raw worker python -m py_compile /app/app/scripts/benchmark_ocr_vi.py /app/tests/fixtures/ocr_vi/generate_fixtures.py
docker compose run --rm --no-deps -e OCR_PREPROCESS_MODE=raw worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --engine all --format json
```

Kết quả chính:
- Đã mở rộng `tests/fixtures/ocr_vi` lên 6 fixture không nhạy cảm, gồm 5 ảnh scan và 1 PDF scan 2 trang.
- `benchmark_ocr_vi.py` đã benchmark được cả PDF, gom text nhiều page và báo runtime/page.
- Với `OCR_PREPROCESS_MODE=raw`, `paddle_vietocr` giữ dấu tiếng Việt tốt hơn `paddleocr` trên các mẫu scan rõ, scan mờ và ảnh nghiêng.
- `sample_004.png` hai cột vẫn sai thứ tự đọc; đây là lỗi layout/detection cần xử lý riêng.
- `sample_006.pdf` giữ dấu tốt hơn với VietOCR nhưng còn tách dòng tiêu đề; runtime khoảng 39.6s/page.
- Benchmark full với `OCR_PREPROCESS_MODE=auto` bị dừng sau hơn 5 phút vì quá chậm cho kiểm tra thường xuyên.

OCR tài liệu thực tế kiểm tra ngày 2026-06-02:

```bash
docker compose ps
docker compose logs --tail=160 worker
docker compose exec -T postgres psql -U legal -d legal_doc_ai -c "select id, original_filename, content_type, document_type, status, created_at, updated_at from documents order by created_at desc limit 8;"
docker compose exec -T postgres psql -U legal -d legal_doc_ai -c "select j.document_id, d.original_filename, j.status as job_status, d.status as doc_status, j.attempts, j.error_message, j.updated_at from ocr_jobs j join documents d on d.id=j.document_id order by j.created_at desc limit 4;"
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Lê Thế Anh hồ sơ xin thôi việc Xuân Lâm","limit":5}'
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Luật Đấu thầu phạm vi điều chỉnh","limit":5}'
```

Kết quả:
- `22-qh-15.signed.pdf`: document `searchable`, OCR job `completed`, 84 pages, 184 chunks, average confidence `0.9272`, total OCR text `175497` chars.
- `0f53863c-d731-4b39-b0ff-d883ab039a88.jpeg`: document `searchable`, OCR job `completed`, 1 page, 1 chunk, confidence `0.9037`.
- Qdrant đã nhận upsert cho PDF lúc `2026-06-02T08:26:44Z` và JPEG lúc `2026-06-02T08:28:05Z`.
- Search `Lê Thế Anh hồ sơ xin thôi việc Xuân Lâm` trả JPEG mới nhất ở top 1.
- Search `Luật Đấu thầu phạm vi điều chỉnh` có chunk đúng `Điều 1. Phạm vi điều chính` nhưng chỉ đứng thứ 5, đồng thời kết quả còn lẫn bản PDF upload cũ.

Lỗi OCR thực tế đã thấy:
- PDF `22-qh-15.signed.pdf`: giữ dấu tiếng Việt khá tốt nhưng có lỗi từ như `LUẶT`, `điều chính`, `dầu khi`, và dấu phân tách header `CÔNG BÁO/SỐ 869 ? 870`.
- JPEG công văn xã Xuân Lâm: có hallucination/nhiễu như `Thuật`, `Nhất`, `Thành`, `Nhà Tháng`, `Các thuận`; số hiệu/ngày có lỗi `72]`, `27IS/2026`.
- Search cần dedup/reranking vì cùng file `22-qh-15.signed.pdf` đã được upload nhiều lần và chunk đúng không luôn đứng top 1.

Tối ưu OCR/search kiểm tra ngày 2026-06-02:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/services/document_content_service.py /app/app/services/ocr/paddle_vietocr_engine.py /app/app/services/search_service.py /app/app/workers/ocr_worker.py /app/app/scripts/reindex_embeddings.py
docker compose run --rm --no-deps -e OCR_PREPROCESS_MODE=raw worker python - <<'PY'
from pathlib import Path
from app.services.document_content_service import DocumentContentService
service = DocumentContentService()
service.settings = service.settings.model_copy(update={"ocr_engine": "paddle_vietocr", "ocr_preprocess_mode": "raw"})
page = service.extract_pages(Path('/app/tests/fixtures/ocr_vi/sample_004.png'), 'sample_004.png')[0]
print(page.text)
PY
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Luật Đấu thầu phạm vi điều chỉnh","limit":5}'
```

Kết quả:
- `sample_004.png` đã đọc đúng thứ tự cột: tiêu đề, toàn bộ `Điều 5. Kiểm kê vật tư`, sau đó đến `Điều 6. Báo cáo sử dụng`.
- JPEG công văn xã Xuân Lâm khi OCR lại bằng code mới đạt confidence `0.9043`; số hiệu đọc đúng `Số: 72/UBND-KT`, ngày đọc đúng `27/5/2026`, giảm các nhiễu `Thuật`, `Nhất`, `Thành`, `Nhà Tháng`, `Các thuận`, `1990`, `1992`, `E`, `16`, `6n`, `2`.
- Search `Luật Đấu thầu phạm vi điều chỉnh` đưa chunk `Điều 1. Phạm vi điều chính` lên top 2 và top 5 không còn lẫn các bản upload cũ của cùng file PDF.

Tối ưu PDF scan và search kiểm tra bổ sung ngày 2026-06-02:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/scripts/benchmark_ocr_vi.py /app/app/services/document_content_service.py /app/app/services/search_service.py
docker compose run --rm --no-deps -e OCR_PREPROCESS_MODE=raw worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --files sample_006.pdf --engine paddle_vietocr --format json
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Luật Đấu thầu phạm vi điều chỉnh","limit":5}'
```

Kết quả:
- `benchmark_ocr_vi.py` có chế độ kiểm tra nhanh bằng `--files` và `--limit`, tránh phải chạy toàn bộ fixture khi chỉ cần kiểm tra một file/page.
- `sample_006.pdf` với `paddle_vietocr` và `OCR_PREPROCESS_MODE=raw` đạt `CER=0.0`, `WER=0.0`, `accent_loss=0.0`; tiêu đề đã nối đúng `TỔNG CÔNG TY HẠ TẦNG KỸ THUẬT` và `KẾ HOẠCH MUA SẮM VẬT TƯ NĂM 2026`.
- OCR riêng page 1 của `22-qh-15.signed.pdf` đạt confidence `0.9256`; header đọc đúng `CÔNG BÁO/SỐ 869 + 870/NGÀY 31-7-2023`, `LUẬT`, `ĐẦU THẦU`, `Điều 1. Phạm vi điều chỉnh`.
- Search `Luật Đấu thầu phạm vi điều chỉnh` đưa chunk `Điều 1. Phạm vi điều chính` lên top 1.

Giảm runtime OCR benchmark và reindex payload kiểm tra ngày 2026-06-03:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/scripts/benchmark_ocr_vi.py /app/app/services/ocr/__init__.py /app/tests/fixtures/ocr_vi/generate_fixtures.py
docker compose run --rm --no-deps worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --files sample_001.png --engine paddle_vietocr --preprocess-mode raw clahe --format json
docker compose exec -T api python -m app.scripts.reindex_embeddings --dry-run
docker compose exec -T api python -m app.scripts.reindex_embeddings
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Luật Đấu thầu phạm vi điều chỉnh","limit":5}'
```

Kết quả:
- `benchmark_ocr_vi.py` hỗ trợ `--preprocess-mode raw/clahe/threshold/auto/all`, output có cột `preprocess_mode`.
- Benchmark tái sử dụng `DocumentContentService` theo engine/preprocess mode; OCR engine cache không còn phụ thuộc preprocess mode nên không khởi tạo lại model khi chỉ đổi preprocess.
- Benchmark nhanh `sample_001.png` với `paddle_vietocr`:
  - `raw`: CER `0.0`, WER `0.0`, accent loss `0.0`, confidence `0.9264`, runtime `20.682s`.
  - `clahe`: CER `0.0`, WER `0.0`, accent loss `0.0`, confidence `0.9259`, runtime `11.944s`.
- Đã thêm fixture không nhạy cảm `sample_007.png` mô phỏng công văn xã/phòng ban với header hai bên, số hiệu, ngày tháng, kính gửi, nội dung yêu cầu, dấu mộc và nhiễu nhẹ.
- Benchmark `sample_007.png` với `paddle_vietocr/raw`: confidence `0.9228`, accent loss `0.0`; còn lỗi thứ tự header và thiếu một phần dòng liên hệ, phù hợp để theo dõi hồi quy OCR công văn.
- Reindex dry-run xác nhận `453` chunks; reindex thật đã index `453` chunks vào Qdrant collection `document_chunks_bkai_768_v1`.
- Kiểm tra Qdrant payload mẫu cho thấy các point đã có `content_hash`.
- Search `Luật Đấu thầu phạm vi điều chỉnh` sau reindex vẫn trả chunk `Điều 1. Phạm vi điều chính` ở top 1.

Cải thiện OCR công văn và hybrid search kiểm tra ngày 2026-06-03:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/services/document_content_service.py /app/app/services/ocr/paddle_vietocr_engine.py /app/app/services/search_service.py /app/app/repositories/document_repository.py /app/app/routers/search.py
docker compose run --rm --no-deps worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --files sample_007.png --engine paddle_vietocr --preprocess-mode raw clahe threshold --format json
docker compose run --rm --no-deps worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --files sample_007.png --engine paddle_vietocr --preprocess-mode auto --format json
docker compose up -d --build api
curl -fsS http://localhost:8000/health
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Luật Đấu thầu phạm vi điều chỉnh","limit":3}'
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Nghị định 192 2026 chế độ phụ cấp đặc thù lĩnh vực y tế","limit":3}'
```

Kết quả:
- `sample_007.png` đã cải thiện ordering header hai bên: phần `ỦY BAN NHÂN DÂN XÃ MINH PHÚ`, `PHÒNG KINH TẾ`, `Số: 72/UBND-KT` đứng trước tiêu ngữ bên phải, không còn xen kẽ từng dòng.
- OCR postprocess nối lại các dòng tiêu ngữ, tên xã, ngày tháng và các câu nội dung bị tách dòng; lọc nhiễu `000001`/`CHUNICH` và sửa `số điện thoai` -> `số điện thoại`, `MINH PHỦ` -> `MINH PHÚ`.
- Chế độ `auto` ưu tiên kết quả có marker hành chính/pháp lý như `Số:`, `Kính gửi`, `Người liên hệ`, `Điều`, `Khoản`, giúp giữ được dòng liên hệ khi preprocess `threshold` phát hiện tốt hơn.
- Benchmark `sample_007.png`:
  - Trước tối ưu `raw`: CER `0.4241`, WER `0.4907`, confidence `0.9228`.
  - Sau tối ưu `raw`: CER `0.2342`, WER `0.2963`, confidence `0.9266`.
  - Sau tối ưu `auto`: CER `0.2658`, WER `0.2963`, confidence `0.9252`, giữ `Người liên hệ: Nguyễn Văn An, số điện thoại 0900`.
- Search service đã chuyển sang hybrid retrieval: Qdrant vector candidates + PostgreSQL keyword candidates trên `document_chunks.text`, sau đó rerank/dedup chung.
- Router search truyền DB session vào service, giữ kiến trúc `router -> service -> repository`.
- Search response `score` hiện là hybrid rerank score để thứ tự kết quả và điểm hiển thị nhất quán.
- Query `Luật Đấu thầu phạm vi điều chỉnh` vẫn trả chunk `Điều 1. Phạm vi điều chính` top 1.
- Query `Nghị định 192 2026 chế độ phụ cấp đặc thù lĩnh vực y tế` vẫn trả đúng `Điều 1` của file nghị định 192 top 1.

## Lỗi Đã Sửa

Docker/runtime:
- Thêm `email-validator` vì Pydantic `EmailStr` cần package này.
- Bỏ Alembic migration khỏi startup của worker để tránh race condition.
- Thêm healthcheck cho API.
- Worker đợi API healthy rồi mới start.

Frontend:
- Sửa lỗi `useApiClient is not defined` bằng cách import explicit `useApiClient` trong các frontend service.

## Giới Hạn Hiện Tại

OCR:
- Đã triển khai OCR thật cho PDF/image scan bằng PaddleOCR/OpenCV.
- Đã tích hợp VietOCR local cho nhận dạng tiếng Việt có dấu; mặc định `OCR_ENGINE=paddle_vietocr`.
- Đã nâng OCR scan lên PaddleOCR 3.3.0/PP-OCRv5 để detect/crop text line; `OCR_ENGINE=paddleocr` vẫn dùng recognizer Latin `latin_PP-OCRv5_mobile_rec` làm baseline/fallback thủ công.
- Có cấu hình OCR qua env: `OCR_ENGINE`, `OCR_LANG`, `OCR_DEVICE`, `OCR_MODEL_DIR`, `OCR_PREPROCESS_MODE`, `OCR_MIN_CONFIDENCE`, `OCR_RESTORE_VIETNAMESE_TERMS`, `VIETOCR_MODEL_DIR`, `VIETOCR_DEVICE`, `VIETOCR_CONFIG`, `VIETOCR_WEIGHT_PATH`.
- PDF có text nhúng được trích xuất trực tiếp bằng `pypdfium2` trước khi fallback OCR để giữ dấu tiếng Việt.
- Worker đọc trực tiếp file `.txt` và `.md`.
- Worker trích xuất text thật từ `.docx`, `.xlsx`, `.xls`.
- `.doc` legacy chưa hỗ trợ LibreOffice converter, hiện fail rõ ràng.
- PaddleOCR model có thể được tải ở lần OCR đầu tiên nếu container chưa có model cache.
- Nếu chuẩn bị sẵn `models/ocr/PP-OCRv5_server_det` và `models/ocr/latin_PP-OCRv5_mobile_rec`, worker sẽ dùng model local qua `/models/ocr`.
- VietOCR weight local đã được chuẩn bị tại `models/ocr/vietocr/transformerocr.pth` trên máy local và không được commit.
- Nếu `OCR_ENGINE=paddle_vietocr` nhưng thiếu `VIETOCR_WEIGHT_PATH`, worker báo `FileNotFoundError` rõ ràng.
- Chất lượng OCR scan xấu vẫn phụ thuộc detection box và chất lượng crop; fixture hai cột đã được cải thiện bằng column-aware line ordering.
- PDF scan với VietOCR giữ dấu tốt hơn baseline; page 1 PDF thật và fixture PDF scan đã giảm lỗi header/tiêu đề, nhưng runtime vẫn cao.
- Tài liệu thực tế upload từ web đã chạy hết pipeline đến `searchable`; JPEG công văn đã giảm lỗi số hiệu/ngày tháng và nhiễu từ khi OCR lại bằng code mới, nhưng vẫn cần theo dõi thêm trên nhiều ảnh scan thật.
- Fixture công văn `sample_007.png` đã cải thiện rõ thứ tự header và giữ được số hiệu/ngày/kính gửi; với `auto` đã giữ được dòng `Người liên hệ`, nhưng số điện thoại vẫn có thể bị thiếu phần cuối nếu detection không bắt đủ vùng chữ.

Chunking:
- Đã sửa lỗi `section_title` quá dài làm PostgreSQL báo `value too long for type character varying(512)`.
- Các document VBHN lỗi cũ đã reprocess lại, trạng thái `searchable/completed`.

Embedding:
- Đã thêm backend local `sentence-transformers` có thể bật bằng env.
- Mặc định Docker Compose có thể dùng fake embedding để dev khởi động nhanh, nhưng `.env` local hiện đã bật `sentence_transformers`.
- Model khuyến nghị: `bkai-foundation-models/vietnamese-bi-encoder`, `EMBEDDING_DIMENSIONS=768`.
- Đã thêm script reindex chunks hiện có sang Qdrant collection đang cấu hình.
- Model BKAI đã được chuẩn bị local tại `models/embeddings/bkai-vietnamese-bi-encoder`.

Search:
- Qdrant search đã chạy được cho skeleton flow.
- Score có ý nghĩa hơn khi bật local embedding thật và reindex sang collection version mới.
- Đã reindex 1.584 chunks sang Qdrant collection `document_chunks_bkai_768_v1`, vector size `768`.
- Benchmark 5 query tiếng Việt cho kết quả đúng ngữ cảnh hơn fake embedding, đặc biệt với `hiệu lực thi hành luật đấu thầu`, `trách nhiệm của chủ đầu tư`, `lựa chọn nhà thầu`.
- Semantic search đã có reranking/dedup nhẹ: lấy nhiều hit hơn từ Qdrant, boost exact legal markers và giảm kết quả yếu trùng theo document/title/text.
- Semantic search đã có hybrid retrieval MVP: lấy candidate từ Qdrant vector và PostgreSQL keyword, cộng tín hiệu exact phrase/term coverage trước khi dedup.
- Keyword search có migration `0002_chunk_text_trgm` tạo extension `pg_trgm` và GIN trigram index `ix_document_chunks_text_trgm` trên `document_chunks.text` cho các chunk chưa soft delete.
- Query `Luật Đấu thầu phạm vi điều chỉnh` đã đưa chunk Điều 1 lên top 1 và giảm bản upload cũ trong top 5.
- Metadata filters hiện còn tối thiểu.

Reprocess công văn cũ và tối ưu keyword index kiểm tra ngày 2026-06-03:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/scripts/reprocess_document.py /app/app/repositories/document_repository.py /app/app/services/qdrant_service.py /app/alembic/versions/0002_document_chunk_text_trgm_index.py
docker compose exec -T api alembic upgrade head
docker compose exec -T postgres psql -U legal -d legal_doc_ai -c "EXPLAIN ANALYZE ..."
docker compose exec -T api python -m app.scripts.reprocess_document --document-id 718b0db1-6c8c-4da4-b6aa-5689173d219a --dry-run
docker compose exec -T api python -m app.scripts.reprocess_document --document-id 718b0db1-6c8c-4da4-b6aa-5689173d219a
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Lê Thế Anh hồ sơ xin thôi việc Xuân Lâm","limit":3}'
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Số 72 UBND KT Kính gửi Ban chỉ huy 32 xóm","limit":3}'
```

Kết quả:
- Thêm script `python -m app.scripts.reprocess_document --document-id <id>` để OCR lại file đã upload, replace page/chunk theo document, upsert lại Qdrant và xóa point dư nếu số chunk giảm.
- Reprocess công văn JPEG `0f53863c-d731-4b39-b0ff-d883ab039a88.jpeg`:
  - Dry-run: `old_pages=1`, `new_pages=1`, `old_chunks=1`, `new_chunks=1`, average confidence `0.9043`.
  - Reprocess thật: document vẫn `searchable`, `1/1` chunk có `content_hash` và `qdrant_point_id`, không có chunk dư.
- Text sau reprocess đã cải thiện các lỗi cũ:
  - `Số: 72]/UBND-KT` -> `Số: 72/UBND-KT`.
  - `27IS/2026` -> `27/5/2026`.
  - Bỏ nhiễu đầu dòng như `Thuật`, `Nhất`, `Thành`, `Nhà Tháng`, `Các thuận`, `Anh thuận`.
  - `Thông bảo` -> `Thông báo`.
- Search `Lê Thế Anh hồ sơ xin thôi việc Xuân Lâm` trả công văn JPEG đã cleanup ở top 1.
- Search `Số 72 UBND KT Kính gửi Ban chỉ huy 32 xóm` trả công văn JPEG đã cleanup ở top 1.
- `EXPLAIN ANALYZE` trước index dùng seq scan trên `document_chunks.text`, khoảng `23ms` với 478 chunks.
- Sau migration, planner vẫn chọn seq scan do bảng nhỏ, nhưng khi `enable_seqscan=off` xác nhận index trigram usable bằng `Bitmap Index Scan`, khoảng `4.8ms` cho query keyword đại diện.

API reprocess document có audit kiểm tra ngày 2026-06-03:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/models/document.py /app/app/repositories/document_repository.py /app/app/services/document_service.py /app/app/routers/documents.py /app/app/schemas/document.py /app/app/workers/ocr_worker.py /app/alembic/versions/0003_ocr_job_type.py
docker compose up -d --build api worker
curl -fsS http://localhost:8000/health
docker compose exec -T api alembic current
curl -fsS -X POST http://localhost:8000/api/v1/documents/718b0db1-6c8c-4da4-b6aa-5689173d219a/reprocess -H 'Content-Type: application/json' -d '{"reason":"verify reprocess API workflow"}'
curl -fsS http://localhost:8000/api/v1/documents/718b0db1-6c8c-4da4-b6aa-5689173d219a
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Số 72 UBND KT Kính gửi Ban chỉ huy 32 xóm","limit":3}'
```

Kết quả:
- Thêm API `POST /api/v1/documents/{document_id}/reprocess`.
- Request body hỗ trợ `reason` để audit lý do reprocess.
- API không OCR inline; chỉ tạo `ocr_jobs` mới với `job_type='reprocess'`, `status='pending'`, document chuyển `reprocess_pending`, worker xử lý async.
- Thêm migration `0003_ocr_job_type` cho `ocr_jobs.job_type` và `ocr_jobs.reason`.
- Worker phân biệt `job_type='ocr'` và `job_type='reprocess'`:
  - OCR lần đầu vẫn create page/chunk mới.
  - Reprocess replace page/chunk hiện có, upsert lại Qdrant, xóa point dư nếu số chunk giảm.
- Worker commit trạng thái `ocr_running` hoặc `reprocess_running` ngay khi bắt đầu để API/UI thấy trạng thái đang xử lý.
- Nếu reprocess lỗi, document quay về trạng thái trước đó thay vì mất trạng thái `searchable`.
- Kiểm tra API trên document `718b0db1-6c8c-4da4-b6aa-5689173d219a`:
  - API trả `202 Accepted`, job `6a154fc5-e3f6-4f45-b929-d59db6566163`, `job_type='reprocess'`, `reason='verify reprocess API workflow'`.
  - Worker xử lý xong: job `completed`, attempts `1`, document `searchable`.
  - Detail API trả cả job OCR ban đầu `job_type='ocr'` và job reprocess `job_type='reprocess'`.
  - Document vẫn có `1/1` chunk active, có `content_hash` và `qdrant_point_id`.
  - Search `Số 72 UBND KT Kính gửi Ban chỉ huy 32 xóm` vẫn trả công văn JPEG top 1.

UI reprocess và job audit kiểm tra ngày 2026-06-04:

```bash
docker compose run --rm --no-deps web npm run build
```

Kết quả:
- Frontend document service đã có `reprocess(id, reason)` gọi `POST /api/v1/documents/{document_id}/reprocess`.
- Composable `useDocuments` đã có action `reprocessDocument` và loading state riêng cho reprocess.
- Trang `/documents/[id]` đã có form nhập lý do reprocess, nút reprocess, polling lại detail sau khi tạo job và không cho bấm khi document đang xử lý.
- Trang `/documents/[id]` đã hiển thị danh sách audit OCR/reprocess job thay vì chỉ job mới nhất.
- Nuxt production build trong Docker Compose hoàn tất thành công.

Sửa lỗi Nuxt dev app manifest ngày 2026-06-04:

```bash
docker compose run --rm --no-deps web npm run build
docker compose up -d --build web
curl -fsS -I http://localhost:3000/login
docker compose logs --tail=160 web | rg -n "#app-manifest|Pre-transform|ERROR|Failed to resolve" || true
```

Kết quả:
- Tắt `experimental.appManifest` trong Nuxt vì MVP hiện không dùng route rules/app manifest.
- Dev server không còn lỗi Vite pre-transform `Failed to resolve import "#app-manifest"`.
- `/login` trả HTTP 200 sau khi rebuild service `web`.

Browser verify reprocess UI và auth guard backend ngày 2026-06-04:

```bash
docker compose run --rm --no-deps api python -m py_compile /app/app/dependencies.py /app/app/repositories/user_repository.py /app/app/routers/documents.py /app/app/routers/search.py
docker compose up -d --build api worker web
curl -fsS http://localhost:8000/health
curl -sS -o /tmp/documents_no_token.json -w '%{http_code}\n' http://localhost:8000/api/v1/documents
curl -sS -o /tmp/search_no_token.json -w '%{http_code}\n' -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Số 72 UBND KT","limit":3}'
docker compose run --rm --no-deps web npm run build
docker compose config --quiet
```

Kết quả:
- Thêm `app.dependencies.get_current_user` để validate Bearer JWT, load user active từ DB và trả `401 Not authenticated` nếu thiếu/sai token.
- Thêm `UserRepository.get_by_id`.
- Gắn auth dependency ở router `/api/v1/documents` và `/api/v1/search`; `/health` vẫn public.
- Không token:
  - `GET /api/v1/documents` trả `401`.
  - `POST /api/v1/search/semantic` trả `401`.
- Token admin local vẫn gọi được:
  - `GET /api/v1/documents` trả `200`.
  - `POST /api/v1/search/semantic` trả `200`.
- Headless Chrome mở `/documents/718b0db1-6c8c-4da4-b6aa-5689173d219a` với cookie `auth_token`, thấy `Reprocess`, `Job audit`, trạng thái `searchable`, nhập reason và click nút `Reprocess` thành công.
- Job UI-created `99dcdfd8-cbf1-4332-a8b8-298d1a30abcf` chạy `reprocess_pending` -> `reprocess_running` -> `searchable/completed`, attempts `1`, reason `headless browser UI reprocess 2026-06-04 retry`, không có error.
- Search sau reprocess UI với query `Số 72 UBND KT Kính gửi Ban chỉ huy 32 xóm` vẫn trả document `718b0db1-6c8c-4da4-b6aa-5689173d219a` top 1.

Admin UX polish và auth scope MVP ngày 2026-06-04:

```bash
docker compose run --rm --no-deps web npm run build
docker compose up -d --build web
curl -fsS -I http://localhost:3000/login
```

Kết quả:
- Document detail hiển thị thời điểm detail được refresh gần nhất ở header và trong khu reprocess.
- Khi polling OCR/reprocess, timestamp refresh được cập nhật theo từng lần fetch detail.
- Nút `Reprocess` có confirm trước khi tạo job để giảm rủi ro click nhầm OCR lại tài liệu lớn.
- Job audit làm nổi bật job `pending/running` bằng nền vàng nhạt và badge `Đang xử lý`.
- Header document, reason job và chunk title đã wrap tốt hơn trên màn hình nhỏ.
- Headless Chrome kiểm tra document detail bằng cookie `auth_token`, xác nhận có `Cập nhật detail lần cuối`, `Lần refresh gần nhất`, `Reprocess`, `Job audit`.
- Smoke test override `window.confirm` trả `false`; confirm được gọi và không tạo thêm job với reason `confirm cancel smoke 2026-06-04`.
- Mobile viewport `390px` có `scrollWidth=390`, không phát hiện overflow ngang rõ ràng.
- Auth scope MVP hiện giữ đơn giản: mọi user active đã đăng nhập được dùng documents/search/reprocess. Chưa thêm role/RBAC để tránh migration và phân quyền sớm khi hệ thống mới có admin local.

Audit Log Admin MVP ngày 2026-06-04:

```bash
docker compose run --rm --no-deps api python -m py_compile /app/app/models/audit_log.py /app/app/repositories/audit_log_repository.py /app/app/repositories/document_repository.py /app/app/services/document_service.py /app/app/routers/documents.py /app/app/schemas/document.py /app/alembic/versions/0004_audit_logs.py
docker compose run --rm --no-deps web npm run build
docker compose up -d --build api web
docker compose exec -T api alembic current
curl -fsS http://localhost:8000/health
curl -fsS -I http://localhost:3000/login
```

Kết quả:
- Thêm migration `0004_audit_logs` tạo bảng `audit_logs` với actor, action, entity type/id, metadata JSONB và audit timestamp.
- Thêm model `AuditLog` và repository `AuditLogRepository`.
- Document detail API trả `audit_logs` cho entity document, gồm actor user và metadata.
- `DocumentService.upload` ghi event `document.upload` với filename, content type, document type và OCR job ID.
- `DocumentService.request_reprocess` ghi event `document.reprocess_requested` với reason, OCR job ID và previous status.
- Trang `/documents/[id]` hiển thị card `Admin audit log`, actor, action, timestamp và metadata.
- Verify reprocess audit trên document `718b0db1-6c8c-4da4-b6aa-5689173d219a`:
  - Tạo job `683b14d0-ec3f-4299-87e1-6c637dfa5a03`.
  - Event `0a8fa045-67b4-4b96-8d7d-ebceaf4b0206`, action `document.reprocess_requested`, actor `admin@example.com`, reason `audit log verify 2026-06-04`.
  - Job chạy xong `searchable/completed`, attempts `1`, không có error.
- Verify upload audit bằng file tạm `/tmp/audit_upload_smoke.txt`:
  - Document `9f92a517-6e03-49f7-b112-f0279e53f3c2` chuyển `searchable`.
  - Event `document.upload` có actor admin và metadata file/job đúng.
- Headless Chrome xác nhận UI có `Admin audit log`, `Yêu cầu reprocess`, actor admin và reason audit verify.
- Search `Số 72 UBND KT Kính gửi Ban chỉ huy 32 xóm` sau reprocess audit vẫn trả document `718b0db1-6c8c-4da4-b6aa-5689173d219a` top 1.

Multi-file document upload và source file model ngày 2026-06-04:

```bash
docker compose run --rm --no-deps api python -m py_compile app/services/document_service.py app/routers/documents.py app/workers/ocr_worker.py app/models/document.py app/repositories/document_repository.py app/schemas/document.py
docker compose run --rm --no-deps web npm run build
docker compose up -d --build api worker web
docker compose exec -T api alembic current
curl -fsS -I http://localhost:3000/login
```

Kết quả:
- Thêm migration `0005_document_files` tạo bảng `document_files` để một document nghiệp vụ có nhiều file nguồn.
- Thêm model/schema/repository cho `DocumentFile`; detail API trả `files`.
- Endpoint `POST /api/v1/documents/upload/multi-file` tạo 1 document, nhiều source files, 1 OCR job và audit event `document.upload` có `file_count`/file list.
- Endpoint upload single cũ vẫn giữ response cũ, đồng thời tạo `document_files` một phần tử và hỗ trợ title form tùy chọn.
- Worker ưu tiên xử lý `document_files` theo `file_order`, đánh số page liên tục qua nhiều file, fallback `documents.file_path` cho dữ liệu cũ.
- Frontend `/upload` đã phân biệt `Tên văn bản` và `Tệp nguồn`, hỗ trợ mode nhiều tệp thuộc cùng một văn bản.
- Frontend `/documents/[id]` hiển thị card `Tệp nguồn`; header dùng `document.title`, không coi filename là tên nghiệp vụ chính.
- Alembic current là `0005_document_files`.
- Smoke multi-file:
  - Document `904886a1-30cf-46ad-bade-161d8c12461c` có title `Công văn multi-file smoke 2026-06-04`.
  - Có 2 source files `qlvb_multi_a.txt`, `qlvb_multi_b.txt`, đều `completed`.
  - Worker tạo 2 pages, page 1 từ file thứ nhất, page 2 từ file thứ hai, document chuyển `searchable`.
  - Search query `zeta` trả đúng document multi-file ở top 1, chunk page 2.
- Smoke single upload:
  - Document `10aa4e6e-fa93-49ff-adc0-7a0755757bf7` giữ title form `Single upload title smoke 2026-06-04`.
  - Có 1 source file `qlvb_single.txt`, OCR xong và document `searchable`.
- `/upload` SSR có các nhãn `Một tệp`, `Nhiều tệp cùng văn bản`, `Tên văn bản`.

Documents filters, source file management và zip upload ngày 2026-06-04:

```bash
docker compose run --rm --no-deps api python -m py_compile app/services/document_service.py app/routers/documents.py app/repositories/document_repository.py app/schemas/document.py
docker compose run --rm --no-deps web npm run build
docker compose up -d --build api worker web
curl -fsS -I http://localhost:3000/login
```

Kết quả:
- `GET /api/v1/documents` hỗ trợ `q`, `status`, `document_type`, `sort_by`, `sort_dir`, `limit`, `offset`.
- Frontend `/documents` có filter theo title/filename, status, document type và sort theo ngày tạo/cập nhật/title/status/type.
- Thêm endpoint `POST /api/v1/documents/upload/zip` cho mode zip là một văn bản gồm nhiều tệp nguồn.
- Zip upload không tự đoán nhiều văn bản riêng; mỗi entry file trong zip map thành một `document_files` record.
- Thêm endpoint `POST /api/v1/documents/{document_id}/files` để thêm source files vào document đã tồn tại.
- Thêm endpoint `PATCH /api/v1/documents/{document_id}/files/order` để đổi thứ tự source files.
- Thêm endpoint `DELETE /api/v1/documents/{document_id}/files/{document_file_id}` để soft-delete source file.
- Các thao tác thêm/đổi thứ tự/xóa source file đều tạo OCR job `reprocess` async, audit event và không chạy OCR inline trong request.
- Không cho đổi source files khi document đang có OCR/reprocess job active.
- Không cho xóa source file cuối cùng của document.
- Frontend document detail có UI thêm file nguồn, nút lên/xuống và xóa file nguồn.
- Audit UI hiển thị label cho `document.upload_zip`, `document.source_files_added`, `document.source_files_reordered`, `document.source_file_deleted`.
- Smoke filter list:
  - Query `q=multi`, `status=searchable`, `sort_by=updated_at`, `sort_dir=desc` trả đúng document multi-file smoke.
- Smoke zip upload:
  - Document `53fc35a4-dfc6-43bd-9e8b-0c2baf94be2a` tạo từ zip, có 2 source files, OCR xong `searchable`.
  - Page 1 lấy `zip_a.txt`, page 2 lấy `zip_b.txt`, audit `document.upload_zip` có `file_count=2`.
- Smoke add source file:
  - Thêm `qlvb_added_source.txt` vào document zip, tạo reprocess job và sau xử lý có 3 pages.
- Smoke reorder:
  - Đưa `qlvb_added_source.txt` lên đầu, reprocess xong page 1 đổi sang text của file này.
- Smoke delete:
  - Soft-delete `zip_b.txt`, reprocess xong còn 2 source files và 2 pages.
- SSR `/documents` có nhãn filter/sort; SSR `/upload` có `Zip cùng văn bản`.

Auth:
- Đã có JWT login skeleton.
- Đã có seed admin local.
- Frontend đã có route guard cơ bản.
- API tài liệu/search đã enforce backend Bearer JWT dependency.
- Auth scope MVP: active authenticated user với role `admin` hoặc `user`.
- Admin đã có user management MVP để tạo user, đổi role, reset password, kích hoạt/vô hiệu hóa và xóa mềm user.

Frontend:
- UI hiện đã đủ cho MVP workflow cơ bản.
- Đã có auth route guard cơ bản.
- Đã có page `/users` dành cho admin để quản lý tài khoản local, gồm filter/sort, phân trang và reset password.
- Upload UI đã hỗ trợ một văn bản có nhiều tệp nguồn.
- Upload UI đã hỗ trợ zip là một văn bản gồm nhiều tệp nguồn.
- Document list đã có filter/sort cơ bản.
- Document detail đã có quản lý source files sau upload, preview inline PDF/image/text và hiển thị role/path/confidence của chunks.
- Chưa có layout/form polish ở mức production.

Generated files:
- Sau khi chạy dev server, Nuxt có thể sinh file trong `apps/web/.nuxt/`.
- Các file này đã nằm trong `.gitignore` và không phải source chính.

Chunking OCR text hành chính kiểm tra ngày 2026-06-04:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/models/document.py apps/api/app/schemas/document.py apps/api/app/repositories/document_repository.py apps/api/app/workers/ocr_worker.py apps/api/alembic/versions/0008_document_chunk_metadata.py
PYTHONPATH=apps/api python3 -m unittest app.services.ocr_chunking.tests.test_pipeline
docker compose run --rm --no-deps web npm run build
docker compose config --quiet
docker compose run --rm api alembic upgrade head
```

Kết quả:
- Compile pass cho model/schema/repository/worker và migration chunk metadata.
- Unit test pass 6 mẫu, gồm 5 mẫu bắt buộc và test adapter payload metadata Qdrant.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.
- Docker Compose config pass với `CHUNKING_BACKEND`.
- Alembic nâng DB local từ `0007_document_ocr_metadata` lên `0008_document_chunk_metadata`.

## Quyết Định Hiện Tại

OCR thật, trích xuất Office text, tự động lưu metadata hành chính sau OCR và tích hợp module chunking OCR text theo nhóm văn bản vào worker/UI mức MVP đã được triển khai.
OCR scan tiếng Việt hiện ưu tiên VietOCR local.

Task tiếp theo nên ưu tiên chunk metadata backfill hoặc màn hình quản trị user nếu cần tạo user thường từ UI.

RBAC nhẹ kiểm tra ngày 2026-06-04:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/models/user.py apps/api/app/repositories/user_repository.py apps/api/app/schemas/auth.py apps/api/app/services/auth_service.py apps/api/app/routers/auth.py apps/api/app/dependencies.py apps/api/app/routers/documents.py apps/api/alembic/versions/0009_user_roles.py
docker compose run --rm --no-deps web npm run build
docker compose config --quiet
docker compose run --rm api alembic upgrade head
curl -fsS http://localhost:8000/health
curl -fsS -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"email":"admin@example.com","password":"admin123"}'
```

Kết quả:
- Alembic nâng DB local từ `0008_document_chunk_metadata` lên `0009_user_roles`.
- Admin login response trả `user.role=admin` và JWT có claim `role=admin`.
- Smoke user thường gọi `POST /documents/{id}/reprocess` trả `403` với detail `Admin role required`.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.

Chunk metadata backfill kiểm tra ngày 2026-06-04:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/repositories/document_repository.py apps/api/app/scripts/backfill_chunk_metadata.py
PYTHONPATH=apps/api python3 -m unittest app.services.ocr_chunking.tests.test_pipeline
docker compose exec -T api python -m app.scripts.backfill_chunk_metadata --dry-run --limit 2
docker compose config --quiet
git diff --check
```

Kết quả:
- Thêm script `python -m app.scripts.backfill_chunk_metadata` để populate `doc_group`, `chunk_level`, `section_role`, `section_path`, `chunk_confidence`, `requires_review` cho chunks cũ từ OCR pages đã lưu.
- Backfill chỉ cập nhật metadata theo `chunk_index`, không thay text chunk, `content_hash`, `qdrant_point_id` và không re-embedding.
- Script hỗ trợ dry-run, chạy theo batch, chạy theo document id và báo mismatch khi số chunk tái tạo khác số chunk hiện có.
- Unit test chunking pass 6 mẫu.

User management MVP kiểm tra ngày 2026-06-04:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/repositories/user_repository.py apps/api/app/schemas/auth.py apps/api/app/schemas/user.py apps/api/app/services/auth_service.py apps/api/app/services/user_service.py apps/api/app/routers/users.py apps/api/app/main.py
docker compose run --rm --no-deps web npm run build
python3 <users smoke script>
docker compose config --quiet
git diff --check
```

Kết quả:
- Thêm router admin-only `/api/v1/users` cho list/create/update role/activate/deactivate/soft-delete user.
- Thêm service/repository user management, có audit log và chặn admin tự hạ quyền hoặc tự vô hiệu hóa/xóa tài khoản đang dùng.
- Email response đổi sang string để hỗ trợ domain local/on-prem như `example.local`.
- Thêm frontend `/users`, typed user service/composable, route guard admin và nav link chỉ hiện với admin.
- Smoke API pass: admin tạo user tạm, user thường bị `403` ở `/users`, admin deactivate/activate/update/delete mềm user tạm, user đã delete mềm login lại trả `401`.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.

User management polish kiểm tra ngày 2026-06-04:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/repositories/user_repository.py apps/api/app/schemas/user.py apps/api/app/services/user_service.py apps/api/app/routers/users.py
docker compose run --rm --no-deps web npm run build
python3 <users polish smoke script>
docker compose config --quiet
git diff --check
```

Kết quả:
- `GET /api/v1/users` trả response phân trang `items/total/limit/offset`.
- Thêm endpoint admin-only `POST /api/v1/users/{user_id}/reset-password`, hash password mới và ghi audit `user.password_reset`.
- Page `/users` có page size `10/20/50/100`, nút `Trước/Sau`, tổng số user và reset password trên từng dòng.
- Smoke API pass: admin reset password user tạm, mật khẩu cũ trả `401`, mật khẩu mới login thành công, user thường vẫn bị `403` ở `/users`, user xóa mềm login lại trả `401`.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.

Workflow MVP hiện có:

```text
web upload -> document detail -> OCR status refresh -> searchable -> dashboard search -> open source document
```

Chi tiết task vừa hoàn thành nằm trong `TASK_NEXT.md`.
