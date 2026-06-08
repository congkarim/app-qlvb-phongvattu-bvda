# Trạng Thái Dự Án

Cập nhật lần cuối: 2026-06-08

## Giai Đoạn Hiện Tại

**Phase 0–17 đã hoàn thành.** **Phase 18 đang thực hiện** — mục tiêu 1–2 hoàn thành 2026-06-08.

**Phase 17 đã hoàn thành** (2026-06-07): RAG generative local-only qua Ollama — `LocalLLMService`, profile Compose `llm`, fallback extractive, ops LLM status, dashboard badge, runbook `docs/RAG_LLM_RUNBOOK.md`, smoke `smoke_rag_generative`.

Hệ thống chạy on-prem bằng Docker Compose (`api`, `worker`, `web`, `postgres`, `redis`, `qdrant`; `ollama` optional profile `llm`). Workflow web end-to-end: upload → OCR/extract → searchable → semantic search → RAG Q&A (extractive hoặc generative local) → review chunk → audit. Module nghiệp vụ MVP: hợp đồng, công văn, quyết định, mua sắm — liên kết document detail; gợi ý liên kết document rule-based (Phase 16).

**Phase 18 đang thực hiện** (2026-06-08): mục tiêu 1–2 hoàn thành — thiết kế + migration/model/repository `procurement_line_items`.

Con trỏ thực thi: `TASK_NEXT.md` mục tiêu 3 → service + API line items + smoke backend.

## Giới Hạn Còn Lại

Giới hạn còn lại (đồng bộ `ROADMAP.md`):
- Inventory/tồn kho, phiếu xuất/nhập, tồn tối thiểu: Phase 19+ (chưa lập kế hoạch).
- Workflow phê duyệt nhiều bước, SLA, assignee: Phase 19+.
- HA Ollama / scale horizontal LLM / tách LLM host production: Phase 19+ (ops).
- Line items procurement: **đang mở trong Phase 18** — không kèm tồn kho hay workflow phê duyệt.

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
- Claim OCR job pending bằng database row lock trước khi xử lý để tránh nhiều worker xử lý trùng job.
- OCR job có retry policy MVP: lỗi recoverable retry tối đa theo `max_attempts`, lỗi input/config rõ ràng final failed không retry, có `failed_reason` và `next_run_at`.
- Admin có endpoint `/api/v1/ops/worker-queue` để xem queue counters tối thiểu: `pending_ready`, `pending_delayed`, `running`, `failed`, `completed`, `active`.
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
  - `/contracts`
  - `/dispatches`
  - `/decisions`
  - `/users` (admin)
  - `/status` (admin)
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
- `/documents` có refresh action, filter/search/sort, pagination `limit/offset` có total count, loading state, empty state và link sang detail.
- `/dashboard` có validation search input, loading/empty/error state, filter semantic search theo metadata nghiệp vụ/chunk, bao gồm option `section_role=appendix`, và result link sang document nguồn.
- `/dashboard` có card `Review queue` chỉ dành cho admin để xem chunks `requires_review=true`, lọc theo phụ lục/document/confidence thấp, xem tổng số item, khoảng item, page/page count, nhảy đầu/cuối, chuyển trang bằng `offset`, mở document detail và đánh dấu chunk đã review ngay từ queue.
- `/users` cho phép admin xem audit log theo từng user, gồm actor, action, thời gian và metadata thao tác quản trị.

Search:
- Search rerank đã được tách khỏi `SearchService` sang `SearchRerankService` với config rule riêng để dễ chỉnh mà không trộn vào orchestration search.
- Đã thêm benchmark fixtures chạy lại được bằng `python -m app.scripts.benchmark_search_fixtures`, bao phủ truy vấn vật tư, phụ lục, điều khoản, ngày ban hành và đơn vị ban hành.
- Benchmark search hiện báo ranking metrics và kết luận đánh giá embedding/rerank local; cấu hình local `sentence_transformers` + BKAI đạt `hit_rate=1.00`, `mrr=1.00`, `top1=5/5` trên fixture MVP nên chưa đổi model hoặc thêm reranker nặng.
- Search response và dashboard result đã trả/hiển thị thêm `issuing_agency` để citation metadata rõ hơn.
- RAG foundation có endpoint `POST /api/v1/search/answer` local-only, tái dùng semantic search, tạo câu trả lời extractive từ chunk truy xuất, trả `citations` gồm document/chunk/source page và fallback `insufficient_evidence` khi không đủ căn cứ.

Domain modules:
- Phase 4 chọn module đầu tiên là **Hợp đồng và phụ lục hợp đồng**.
- Đã thêm endpoint `GET /api/v1/contracts/by-document/{document_id}` để tra cứu metadata hợp đồng active theo document core (Phase 7 mục tiêu 1).
- Frontend `/documents/[id]` hiển thị card Hợp đồng và liên kết hai chiều với `/contracts`; dashboard nhận preset search từ contracts (Phase 7 mục tiêu 2).
- Semantic search/dashboard lọc theo metadata hợp đồng (`contract_number`, `supplier_name`, `contract_status`) và hiển thị metadata hợp đồng trong kết quả (Phase 7 mục tiêu 3).
- Đã thiết kế module nghiệp vụ thứ hai **Công văn đến/đi** (`dispatch_records`) trong `docs/DOMAIN_MODULE_DECISION.md` trước khi implement schema/API/UI (Phase 7 mục tiêu 4).
- Đã thêm bảng `dispatch_records` bằng migration `0013_dispatch_records`, liên kết 1-1 `documents.id` và index filter MVP (Phase 7 mục tiêu 5).
- Đã thêm Dispatch API CRUD theo pattern contracts: `/api/v1/dispatches`, audit log và smoke `smoke_dispatch_api` (Phase 7 mục tiêu 6).
- Frontend `/dispatches` quản lý metadata công văn đến/đi; document detail liên kết hai chiều với module dispatch (Phase 7 mục tiêu 7).
- Quyết định được ghi tại `docs/DOMAIN_MODULE_DECISION.md`, scope MVP chỉ quản lý metadata hợp đồng liên kết document core, chưa mở rộng sang inventory/procurement workflow.
- Đã thêm bảng `contract_records` bằng migration `0011_contract_records`, có UUID primary key, `created_at`, `updated_at`, `deleted_at`, liên kết `documents.id` và index filter MVP cho số hợp đồng, nhà cung cấp, trạng thái, ngày ký và hiệu lực.
- Đã thêm backend Contract API theo `router -> service -> repository`, hỗ trợ list/filter/get/create/update/soft-delete metadata hợp đồng, audit log cho create/update/delete và smoke HTTP `python -m app.scripts.smoke_contract_api`.
- Đã thêm frontend `/contracts` theo `page -> composable -> service -> API`, có list/filter/pagination, form tạo/sửa metadata, link document nguồn và xóa mềm admin-only.

Admin configuration:
- Đã thiết kế danh mục admin tối thiểu trong `docs/ADMIN_CATEGORY_DESIGN.md`: `departments` là entity riêng; `business_type` và `document_type` dùng catalog item giới hạn, không mở thành framework cấu hình phức tạp.
- Danh mục MVP cần CRUD tiếp theo: đơn vị/phòng ban, loại nghiệp vụ, loại văn bản; write admin-only, read cho user đã đăng nhập, soft delete và audit log.
- Đã thêm backend Catalog API theo `router -> service -> repository`, gồm read option cho user đăng nhập và CRUD admin-only cho `departments`/`admin_catalog_items`, có soft delete và audit log create/update/delete.
- Frontend đã thêm `catalog.service` và `useCatalogs` theo luồng `page -> composable -> service -> API`.
- `/upload`, `/documents`, `/documents/[id]` và `/dashboard` lấy option `business_type`/`document_type` từ Catalog API, có fallback local khi API lỗi và vẫn hiển thị mã cũ nếu catalog không còn option.
- Đã thêm endpoint admin-only `/api/v1/ops/system-status` và trang `/status` theo luồng `page -> composable -> service -> API` để xem trạng thái tối thiểu của OCR, model embedding, Qdrant và worker queue.

Ops/runbook:
- `docs/WORKER_OPS_RUNBOOK.md` ghi command kiểm tra worker queue, chạy worker smoke, restart worker, xử lý job failed, reprocess, backup/restore PostgreSQL, Qdrant và uploaded source files.
- `docs/ON_PREM_ENV_RUNBOOK.md` ghi policy `.env`, JWT secret, admin password, CORS và database credential cho production nội bộ.
- `docs/STORAGE_BACKUP_RESTORE_RUNBOOK.md` ghi rõ named volumes Docker Compose, dữ liệu nằm trong PostgreSQL/Qdrant/uploads, quy trình backup/restore theo thứ tự và kiểm tra sau restore.
- `docs/LOG_POLICY_RUNBOOK.md` ghi policy log tối thiểu, `LOG_LEVEL`, cách xem log Docker Compose và phân biệt `/health/live` vs `/health/ready`.
- `docs/COMPOSE_RESOURCE_UPLOAD_RUNBOOK.md` ghi resource limits Docker Compose, upload policy và liên kết storage volumes.
- Backend có endpoint public `/health/live`, `/health/ready` và `/health` (liveness tương thích ngược); readiness kiểm tra PostgreSQL, Redis, Qdrant và uploads writable.
- Backend enforce upload limits qua `UPLOAD_MAX_FILE_SIZE_BYTES`, `UPLOAD_MAX_FILES_PER_REQUEST`, `UPLOAD_MAX_ZIP_SIZE_BYTES`; API trả `413` khi vượt giới hạn.
- Docker Compose có `deploy.resources.limits` cho các service chính và healthcheck cho `api`, `redis`, `qdrant`, `worker`.
- Worker ghi heartbeat `/tmp/worker.heartbeat`; frontend `/upload` hiển thị policy upload từ `NUXT_PUBLIC_UPLOAD_*`.
- Backend settings đã có production guard: `APP_ENV=production` sẽ fail nếu dùng default JWT secret, default admin password, wildcard CORS hoặc default `legal:legal` database credential.
- Docker Compose đã đọc secret/admin/CORS/database/API URL từ `.env`, có fallback dev rõ ràng cho local.

## Đã Kiểm Tra Thủ Công

Các kiểm tra sau đã chạy thành công:

Phase 7 frontend module công văn đến/đi kiểm tra ngày 2026-06-06:

```bash
docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=2048 web npm run build
docker compose exec -T api python -m app.scripts.smoke_dispatch_api
git diff --check
```

Kết quả:
- Thêm type/service/composable/page `/dispatches` theo pattern `/contracts`.
- Nav `Công văn`, list/filter/pagination, form tạo/sửa, link document và preset search dashboard.
- Document detail hiển thị card Công văn và link tạo/mở metadata.
- Frontend build pass; smoke dispatch API vẫn pass.
- Ghi chú: build cần tạm dừng container khác nếu máy thiếu RAM (tránh SIGKILL ở Nitro step).

Phase 7 backend API công văn đến/đi kiểm tra ngày 2026-06-06:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/dispatch.py apps/api/app/repositories/dispatch_repository.py apps/api/app/services/dispatch_service.py apps/api/app/routers/dispatches.py apps/api/app/scripts/smoke_dispatch_api.py apps/api/app/main.py
docker compose exec -T api python -m app.scripts.smoke_dispatch_api
docker compose exec -T api python -m app.scripts.smoke_contract_api
git diff --check
```

Kết quả:
- Dispatch API hỗ trợ list/filter/get/create/update/soft-delete và lookup theo `document_id`.
- User list/get/create/update; admin soft delete; audit `dispatch.created/updated/deleted`.
- Smoke dispatch API pass; smoke contract API vẫn pass sau khi thêm router mới.

Phase 7 schema công văn đến/đi kiểm tra ngày 2026-06-06:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/models/dispatch.py apps/api/app/models/document.py apps/api/alembic/versions/0013_dispatch_records.py
docker compose exec -T api alembic upgrade head
docker compose exec -T api alembic current
git diff --check
```

Kết quả:
- Thêm model `DispatchRecord` và relationship `Document.dispatch_record`.
- Migration `0013_dispatch_records` tạo bảng metadata công văn: `dispatch_type`, số/ký hiệu, ngày ban hành, đơn vị ban hành, nơi nhận, trích yếu, trạng thái, ghi chú.
- Partial unique index `ux_dispatch_records_document_active` và các index filter MVP đã có trên PostgreSQL.
- Alembic current là `0013_dispatch_records (head)`; bảng không lưu OCR text/chunk.

Phase 7 thiết kế module công văn đến/đi kiểm tra ngày 2026-06-06:

```bash
git diff --check
```

Kết quả:
- `docs/DOMAIN_MODULE_DECISION.md` bổ sung quyết định module `dispatch_records`: metadata MVP, status, quyền, audit, schema/API/frontend dự kiến theo pattern `contracts`.
- Metadata MVP gồm `dispatch_type` (đến/đi), số/ký hiệu, ngày ban hành, đơn vị ban hành, nơi nhận, trích yếu, trạng thái.
- Ghi rõ không làm inventory, workflow nhiều bước, LLM extraction.

Phase 7 search filter theo metadata hợp đồng kiểm tra ngày 2026-06-06:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/search.py apps/api/app/services/search_service.py apps/api/app/routers/search.py apps/api/app/repositories/contract_repository.py apps/api/app/repositories/document_repository.py apps/api/app/scripts/smoke_api_workflows.py
docker compose exec -T api python -m app.scripts.smoke_api_workflows
docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=2048 web npm run build
git diff --check
```

Kết quả:
- Search nhận filter `contract_number`, `supplier_name`, `contract_status`; giới hạn `document_id` từ `contract_records` active trước Qdrant/DB.
- Search không filter contract vẫn hoạt động như trước; kết quả có metadata hợp đồng khi document liên kết contract.
- Dashboard thêm filter hợp đồng và hiển thị số HĐ/nhà cung cấp/trạng thái trong result.
- Smoke API workflow pass, gồm filter supplier/contract number và empty result khi supplier không khớp.
- Frontend build pass.

Phase 7 liên kết hợp đồng ↔ document (frontend) kiểm tra ngày 2026-06-06:

```bash
docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=2048 web npm run build
git diff --check
```

Kết quả:
- Document detail hiển thị card Hợp đồng khi có metadata; empty state có link tạo mới trên `/contracts`.
- Contracts list có link document nguồn và preset search sang dashboard.
- Dashboard đọc query `q`/`document_number` để chạy search nhanh.
- Frontend build pass.

Phase 7 liên kết hợp đồng ↔ document (backend) kiểm tra ngày 2026-06-06:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/repositories/contract_repository.py apps/api/app/services/contract_service.py apps/api/app/routers/contracts.py apps/api/app/schemas/contract.py apps/api/app/scripts/smoke_contract_api.py
docker compose exec -T api python -m app.scripts.smoke_contract_api
git diff --check
```

Kết quả:
- Thêm `GET /api/v1/contracts/by-document/{document_id}` lookup contract active theo document.
- Trả `404` khi document không tồn tại hoặc chưa có contract active.
- Smoke contract API pass, gồm lookup trước create, sau create và sau soft delete.

Compose resource limits và upload policy kiểm tra ngày 2026-06-06:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/core/config.py apps/api/app/services/document_service.py apps/api/app/routers/documents.py apps/api/app/scripts/smoke_upload_limits.py
docker compose config
docker compose exec -T api python -m app.scripts.smoke_upload_limits
docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=2048 web npm run build
git diff --check
```

Kết quả:
- Docker Compose render pass với resource limits và biến upload policy.
- Smoke `python -m app.scripts.smoke_upload_limits` pass: file quá lớn và vượt số file bị từ chối đúng policy.
- Thêm runbook `docs/COMPOSE_RESOURCE_UPLOAD_RUNBOOK.md`, cập nhật `.env.example` và hiển thị policy trên `/upload`.
- Frontend build pass với `NODE_OPTIONS=--max-old-space-size=2048`.

Health, readiness và log policy kiểm tra ngày 2026-06-06:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/health.py apps/api/app/services/health_service.py apps/api/app/routers/health.py apps/api/app/core/logging_config.py apps/api/app/main.py apps/api/app/workers/ocr_worker.py apps/api/app/scripts/smoke_health_checks.py apps/worker/runner.py
docker compose config
docker compose up -d api postgres redis qdrant worker
PYTHONPATH=apps/api python3 -m app.scripts.smoke_health_checks --api-base http://localhost:8000
git diff --check
```

Kết quả:
- `/health/live` và `/health/ready` trả `status=ok` khi PostgreSQL, Redis, Qdrant và uploads sẵn sàng.
- Docker Compose healthcheck pass cho `api`, `redis`, `qdrant`, `worker`.
- Smoke `python -m app.scripts.smoke_health_checks` pass trên stack local đang chạy.
- Thêm `docs/LOG_POLICY_RUNBOOK.md` và `LOG_LEVEL` config cho API/worker.

Storage volumes và backup/restore runbook kiểm tra ngày 2026-06-06:

```bash
docker compose config
git diff --check
```

Kết quả:
- Thêm `docs/STORAGE_BACKUP_RESTORE_RUNBOOK.md` cho PostgreSQL, Qdrant và uploads named volumes.
- Runbook ghi cách kiểm tra volume thực tế, lưu ý prefix `COMPOSE_PROJECT_NAME`, policy backup đủ 3 phần và khuyến nghị dừng service ghi dữ liệu khi cần snapshot nhất quán.
- Runbook có command backup PostgreSQL bằng `pg_dump`, backup uploads/Qdrant bằng archive volume, restore theo thứ tự PostgreSQL -> uploads -> Qdrant, migration và smoke sau restore.
- README và worker ops runbook đã trỏ sang runbook storage mới để tránh hướng dẫn backup rời rạc.

Chuẩn hóa env và secret kiểm tra ngày 2026-06-06:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/core/config.py apps/api/app/main.py
docker compose config
docker compose run --rm --no-deps -e APP_ENV=production -e JWT_SECRET_KEY=local-dev-secret -e ADMIN_PASSWORD=admin123 -e CORS_ALLOWED_ORIGINS='*' api python - <<'PY'
from app.core.config import Settings
try:
    Settings()
except ValueError as exc:
    print(str(exc).splitlines()[0])
else:
    raise SystemExit('expected production config validation failure')
PY
docker compose run --rm --no-deps -e APP_ENV=production -e JWT_SECRET_KEY='prod-secret-prod-secret-prod-secret-01' -e ADMIN_PASSWORD='StrongAdminPass123' -e CORS_ALLOWED_ORIGINS='http://intranet.local:3000' -e DATABASE_URL='postgresql+psycopg://legal:strong-db-password@postgres:5432/legal_doc_ai' api python - <<'PY'
from app.core.config import Settings
settings = Settings()
print(settings.is_production)
print(settings.cors_origins_list)
PY
docker compose run --rm --no-deps api python - <<'PY'
from app.core.config import get_settings
from app.main import app
settings = get_settings()
print(settings.app_env)
print(settings.cors_origins_list)
print(app.title)
PY
```

Kết quả:
- Thêm `.env.example`.
- Thêm `APP_ENV`, `CORS_ALLOWED_ORIGINS`, explicit CORS middleware config và production validation trong backend settings.
- Compose render pass và services nhận biến từ `.env` với fallback dev.
- Production validation chặn default secret/password/CORS/database credential và nhận cấu hình tối thiểu hợp lệ.
- README và `docs/ON_PREM_ENV_RUNBOOK.md` đã ghi policy vận hành nội bộ.

Trang status tối thiểu kiểm tra ngày 2026-06-06:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/ops.py apps/api/app/services/ops_service.py apps/api/app/routers/ops.py
docker compose run --rm --no-deps web npm run build
docker compose up -d api postgres redis qdrant
TOKEN=$(curl -fsS -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"email":"admin@example.com","password":"admin123"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])') && curl -fsS http://localhost:8000/api/v1/ops/system-status -H "Authorization: Bearer $TOKEN"
```

Kết quả:
- Thêm endpoint admin-only `/api/v1/ops/system-status`.
- Status trả `ocr`, `embedding`, `qdrant` và `worker_queue`, gồm cấu hình chính, collection Qdrant, dimension kỳ vọng và lỗi degradation nếu có.
- Thêm type/service/composable frontend cho ops status.
- Thêm page `/status` và nav admin `Status`.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.
- Curl endpoint sau login admin trả `status=ok` với Qdrant collection hiện tại và worker queue counters.

Frontend dùng option catalog API kiểm tra ngày 2026-06-06:

```bash
docker compose run --rm --no-deps web npm run build
git diff --check
```

Kết quả:
- Thêm type `CatalogItem`/`CatalogOption` trong `apps/web/types/catalog.ts`.
- Thêm service `createCatalogService` gọi `/catalogs/business-types` và `/catalogs/document-types`.
- Thêm composable `useCatalogs` quản lý fallback option, load từ API và formatter dùng chung.
- `/upload` lấy option loại nghiệp vụ từ catalog API qua composable.
- `/documents` lấy filter loại văn bản và loại nghiệp vụ từ catalog API qua composable.
- `/documents/[id]` lấy option form metadata loại văn bản và loại nghiệp vụ từ catalog API, fallback về option local và vẫn hiển thị mã cũ nếu không có trong catalog.
- `/dashboard` lấy filter loại nghiệp vụ từ catalog API và dùng formatter chung cho kết quả search.
- Frontend build pass qua Docker; vẫn có warning chunk PrimeVue lớn như trước, không fail.

CRUD danh mục admin kiểm tra ngày 2026-06-06:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/models/catalog.py apps/api/app/models/department.py apps/api/app/db/base.py apps/api/app/models/__init__.py apps/api/app/schemas/catalog.py apps/api/app/repositories/catalog_repository.py apps/api/app/services/catalog_service.py apps/api/app/routers/catalogs.py apps/api/app/scripts/smoke_catalog_api.py apps/api/app/main.py apps/api/alembic/versions/0012_admin_catalogs.py
docker compose up -d api postgres redis qdrant
docker compose exec -T api alembic upgrade head
docker compose restart api
docker compose exec -T api alembic current
docker compose exec -T api python -m app.scripts.smoke_catalog_api
docker compose exec -T api python -m app.scripts.smoke_contract_api
git diff --check
```

Kết quả:
- Thêm model `AdminCatalogItem` và migration `0012_admin_catalogs`.
- Migration bổ sung `description`, `sort_order`, `is_active` cho `departments`, chuyển unique sang partial unique active và seed `VT`/`UNKNOWN`.
- Migration tạo bảng `admin_catalog_items` cho `business_type` và `document_type`, có UUID, `created_at`, `updated_at`, `deleted_at`, `sort_order`, `is_active` và unique active theo `catalog_type/code`.
- Thêm schema, repository, service và router `catalogs`.
- Endpoint read cho user đăng nhập: `/catalogs/departments`, `/catalogs/business-types`, `/catalogs/document-types`.
- Endpoint CRUD admin-only: `/admin/catalogs/departments` và `/admin/catalogs/items`.
- Smoke pass: user đọc được option seed, user không tạo được catalog, admin create/update/delete được department và item, duplicate trả `409`, audit log create/update/delete được ghi.
- Contract API smoke vẫn pass sau khi thêm catalog schema/API.

Thiết kế danh mục admin kiểm tra ngày 2026-06-06:

```bash
git diff --check
```

Kết quả:
- Chốt danh mục MVP gồm đơn vị/phòng ban, loại nghiệp vụ và loại văn bản.
- Giữ `departments` là bảng/entity riêng vì đã liên kết `users` và `documents`.
- Đề xuất bảng `admin_catalog_items` giới hạn cho `business_type` và `document_type`, có UUID, audit timestamps, `deleted_at`, `is_active`, `sort_order` và unique active theo `catalog_type/code`.
- Ghi seed MVP cho `business_type` và `document_type` dựa trên option đang dùng trong UI.
- Xác định boundary API/frontend cho CRUD và bước frontend lấy option từ API ở mục tiêu sau.

Frontend Contract UI kiểm tra ngày 2026-06-06:

```bash
docker compose run --rm --no-deps web npm run build
docker compose up -d web
curl -fsS http://localhost:3000/contracts
docker compose exec -T api python -m app.scripts.smoke_contract_api
git diff --check
```

Kết quả:
- Thêm type `ContractItem`, `ContractInput`, filter và response trong `apps/web/types/contract.ts`.
- Thêm service `createContractService` gọi `/contracts`.
- Thêm composable `useContracts` quản lý loading/error/pagination/save/delete.
- Thêm page `/contracts` với filter/list/form tạo-sửa metadata hợp đồng, link sang document nguồn và nút delete chỉ hiển thị với admin.
- Thêm nav `Contracts` trong app shell.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.
- `curl /contracts` trả redirect về `/login` khi chưa đăng nhập, đúng theo auth middleware.
- Contract API smoke vẫn pass sau khi thêm UI.
- Phase 4 đã đạt điều kiện hoàn thành: module mới có metadata/filter/API/UI, không phá upload/OCR/search core.

Backend Contract API kiểm tra ngày 2026-06-06:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/contract.py apps/api/app/repositories/contract_repository.py apps/api/app/services/contract_service.py apps/api/app/routers/contracts.py apps/api/app/scripts/smoke_contract_api.py apps/api/app/main.py
docker compose up -d api postgres redis qdrant
docker compose exec -T api python -m app.scripts.smoke_contract_api
git diff --check
```

Kết quả:
- Thêm `app.schemas.contract` cho request/response contract metadata.
- Thêm `ContractRepository`, `ContractService`, `contracts` router và include router trong FastAPI app.
- API hỗ trợ list/filter/get/create/update; soft delete yêu cầu admin.
- Filter tối thiểu: query, document id, số hợp đồng, nhà cung cấp, trạng thái, ngày ký và hiệu lực.
- Service validate document active, chặn trùng contract metadata active theo document, normalize currency và ghi audit `contract.created`, `contract.updated`, `contract.deleted`.
- Smoke HTTP pass: user tạo/list/get/update, duplicate create trả `409`, user delete trả `403`, admin delete mềm, deleted lookup trả `404`, audit logs được ghi.

Metadata/database module hợp đồng kiểm tra ngày 2026-06-06:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/models/contract.py apps/api/app/models/document.py apps/api/app/models/__init__.py apps/api/app/db/base.py apps/api/alembic/versions/0011_contract_records.py
docker compose up -d api postgres redis qdrant
docker compose exec -T api alembic upgrade head
docker compose exec -T api alembic current
docker compose exec -T api python - <<'PY'
from sqlalchemy.orm import configure_mappers
from app.models.contract import ContractRecord
from app.models.document import Document
configure_mappers()
print(Document.contract_record.property.uselist)
print(ContractRecord.document.property.uselist)
PY
docker compose exec -T postgres psql -U legal -d legal_doc_ai -c "select column_name, data_type, is_nullable from information_schema.columns where table_name = 'contract_records' order by ordinal_position;"
docker compose exec -T postgres psql -U legal -d legal_doc_ai -c "select indexname from pg_indexes where tablename = 'contract_records' order by indexname;"
git diff --check
```

Kết quả:
- Thêm model `ContractRecord` và import metadata vào `app.db.base`/`app.models`.
- Migration `0011_contract_records` tạo bảng `contract_records` liên kết `documents.id`.
- Bảng có `id` UUID, `created_at`, `updated_at`, `deleted_at` và không dùng hard delete.
- Partial unique index `ux_contract_records_document_active` đảm bảo mỗi document chỉ có một contract metadata active.
- Các index filter MVP đã có cho `contract_number`, `supplier_name`, `status`, `sign_date`, `effective_to` kèm `deleted_at`.
- Alembic current là `0011_contract_records (head)`.

Chọn module nghiệp vụ đầu tiên kiểm tra ngày 2026-06-06:

```bash
git diff --check
```

Kết quả:
- Chọn module `Hợp đồng và phụ lục hợp đồng` cho Phase 4.
- Ghi rõ lý do chọn, ứng viên chưa chọn, scope MVP, boundary backend/frontend/search và hướng dẫn migration tiếp theo trong `docs/DOMAIN_MODULE_DECISION.md`.
- Không thay đổi runtime; đây là mục tiêu quyết định kiến trúc/tài liệu.

RAG answer endpoint kiểm tra ngày 2026-06-06:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/search.py apps/api/app/services/rag_answer_service.py apps/api/app/routers/search.py apps/api/app/services/tests/test_rag_answer_service.py apps/api/app/scripts/smoke_rag_answer.py
docker compose up -d api postgres redis qdrant
docker compose exec -T api python -m unittest app.services.tests.test_rag_answer_service
docker compose exec -T api python -m app.scripts.smoke_rag_answer
git diff --check
```

Kết quả:
- Thêm schema `RagAnswerRequest`, `RagCitation`, `RagAnswerResponse`.
- Thêm `RagAnswerService` tách riêng khỏi `SearchService`, giữ search core là retrieval/ranking.
- Thêm endpoint `POST /api/v1/search/answer` trong search router, vẫn yêu cầu auth như semantic search.
- Endpoint dùng retrieval hiện có, lọc evidence theo score/overlap, trả answer extractive kèm citations và `grounded=true` khi đủ căn cứ.
- Khi không đủ căn cứ, endpoint trả fallback `grounded=false`, `fallback_reason=insufficient_evidence`.
- Thêm unit test cho grounded answer và fallback; thêm smoke HTTP `python -m app.scripts.smoke_rag_answer` seed benchmark fixture, gọi endpoint thật, kiểm tra citation và cleanup mặc định.
- Phase 3 đã đạt tiêu chí hoàn thành: benchmark lặp lại được, search/RAG trả citation truy vết được, RAG không thay thế search MVP.

Đánh giá embedding/rerank local kiểm tra ngày 2026-06-06:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/scripts/benchmark_search_fixtures.py apps/api/app/services/tests/test_search_benchmark_evaluation.py
docker compose up -d api postgres redis qdrant
docker compose exec -T api python -m unittest app.services.tests.test_search_benchmark_evaluation
docker compose exec -T api python -m app.scripts.benchmark_search_fixtures
```

Kết quả:
- Benchmark report có thêm cấu hình embedding đang dùng, `hit_rate`, `mrr`, `mean_rank`, `top1` và khuyến nghị đánh giá.
- Với `.env` local hiện tại: `EMBEDDING_BACKEND=sentence_transformers`, model `/models/embeddings/bkai-vietnamese-bi-encoder`, `EMBEDDING_DIMENSIONS=768`, CPU, không fallback fake.
- Benchmark pass `5/5`, `hit_rate=1.00`, `mrr=1.00`, `mean_rank=1.0`, `top1=5/5`.
- Kết luận: giữ embedding/rerank hiện tại cho MVP; chưa có bằng chứng cần đổi model local hoặc thêm reranker nặng trước khi thiết kế RAG endpoint.
- Unit test metric/evaluation pass trong container API; test trên host không chạy được do môi trường host thiếu dependency backend `pydantic_settings`.

Search benchmark fixtures kiểm tra ngày 2026-06-06:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/services/search_service.py apps/api/app/schemas/search.py apps/api/app/scripts/benchmark_search_fixtures.py
docker compose up -d api postgres redis qdrant
docker compose exec -T api python -m app.scripts.benchmark_search_fixtures
docker compose run --rm --no-deps web npm run build
git diff --check
```

Kết quả:
- Thêm script `python -m app.scripts.benchmark_search_fixtures` seed fixture tối thiểu, index Qdrant, chạy benchmark và cleanup mặc định.
- Benchmark pass `5/5` query: vật tư, phụ lục, điều khoản, ngày ban hành và đơn vị ban hành; mỗi query báo pass/fail, rank kỳ vọng và top-k result.
- Report top-k hiển thị citation metadata gồm title, số văn bản, ngày ban hành, đơn vị ban hành, trang, `section_role` và `section_path`.
- API search response có thêm `issuing_agency`; dashboard semantic search hiển thị đơn vị ban hành trong metadata result.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.

Tách rerank heuristic kiểm tra ngày 2026-06-05:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/services/search_service.py apps/api/app/services/search_rerank_service.py apps/api/app/services/tests/test_search_rerank_service.py
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m unittest apps.api.app.services.tests.test_search_rerank_service
docker compose exec -T api python -m app.scripts.smoke_api_workflows
git diff --check
```

Kết quả:
- `SearchService` không còn chứa các điều kiện rerank hardcoded như `pham vi dieu chinh`, `luat dau thau`; service chỉ orchestration embedding, Qdrant, keyword candidates, dedup và response.
- Thêm `SearchRerankService` và `SearchRerankConfig` để gom term boost, phrase boost, prefix boost, missing phrase penalty, keyword phrase candidates và weak-match logic.
- Các rule mẫu hiện nằm trong cấu trúc config riêng, có thể chỉnh hoặc disable khi có benchmark mà không sửa nhiều lớp search core.
- Unit test search rerank pass, bao phủ normalize tiếng Việt, keyword phrase, prefix boost, config disable rule và weak-match detection.
- Smoke API workflow pass, xác nhận semantic search và filter `section_role=appendix` vẫn hoạt động.

Worker operations smoke và runbook kiểm tra ngày 2026-06-05:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/main.py apps/api/app/repositories/document_repository.py apps/api/app/schemas/ops.py apps/api/app/services/ops_service.py apps/api/app/routers/ops.py apps/api/app/scripts/smoke_worker_operations.py
docker compose stop worker
docker compose exec -T api python -m app.scripts.smoke_worker_operations
git diff --check
```

Kết quả:
- Thêm endpoint admin-only `GET /api/v1/ops/worker-queue` theo kiến trúc `router -> service -> repository`.
- Endpoint trả queue counters tối thiểu và không expose nội dung document/job: `pending_ready`, `pending_delayed`, `running`, `failed`, `completed`, `active`.
- Thêm script `python -m app.scripts.smoke_worker_operations` chạy lại smoke atomic claim, retry policy và kiểm tra endpoint ops.
- Smoke operations pass: atomic claim không trùng job, retry dừng đúng `max_attempts`, endpoint ops trả counters cho admin và request chưa đăng nhập nhận `401`.
- Thêm `docs/WORKER_OPS_RUNBOOK.md` cho restart worker, xem log, xử lý job failed/reprocess, backup/restore PostgreSQL, Qdrant và uploaded source files.
- Phase 2 đã đạt tiêu chí: không xử lý trùng job khi nhiều worker, job lỗi có retry/failed state rõ, có smoke/command kiểm tra worker claim và retry.

Worker retry policy kiểm tra ngày 2026-06-05:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/models/document.py apps/api/app/schemas/document.py apps/api/app/repositories/document_repository.py apps/api/app/workers/ocr_worker.py apps/api/app/scripts/smoke_worker_retry_policy.py apps/api/alembic/versions/0010_ocr_job_retry_fields.py
docker compose stop worker
docker compose exec -T api alembic upgrade head
docker compose exec -T api python -m app.scripts.smoke_worker_retry_policy
docker compose exec -T api python -m app.scripts.smoke_worker_claim_atomic
docker compose run --rm --no-deps web npm run build
git diff --check
```

Kết quả:
- Migration `0010_ocr_job_retry_fields` thêm `ocr_jobs.max_attempts`, `failed_reason`, `next_run_at` và index `ix_ocr_jobs_status_next_run`.
- Repository chỉ claim job `pending` khi `next_run_at` rỗng hoặc đã tới hạn, tránh chạy lại job retry trước thời điểm hẹn.
- Worker phân loại lỗi MVP: `unsupported_document_format`, `empty_document_content`, `empty_chunks`, `uploaded_file_missing`, `document_not_found`, `invalid_configuration` là không retry; lỗi runtime còn lại là `processing_error` và retry khi chưa hết `max_attempts`.
- Khi retry, job quay về `pending`, set `next_run_at`, giữ `error_message/failed_reason`, document quay về `ocr_pending` hoặc `reprocess_pending`, source file chưa completed quay lại `pending`.
- Khi hết lượt hoặc lỗi không retry, job chuyển `failed`, set `completed_at`, clear `next_run_at`, document chuyển `failed` nếu trạng thái trước đó còn là trạng thái xử lý.
- Detail page hiển thị attempts dạng `attempts/max_attempts`, `failed_reason` và `next_run_at` trong card Job audit.
- Smoke retry pass: lần đầu lỗi recoverable được đưa về `pending` và bị skip trước `next_run_at`; lần hai hết `max_attempts` chuyển `failed`.
- Smoke atomic claim vẫn pass sau thay đổi `next_run_at`, đảm bảo hai session song song không claim cùng job.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.

Atomic claim OCR job kiểm tra ngày 2026-06-05:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/repositories/document_repository.py apps/api/app/workers/ocr_worker.py apps/api/app/scripts/smoke_worker_claim_atomic.py
docker compose stop worker
docker compose exec -T api python -m app.scripts.smoke_worker_claim_atomic
git diff --check
```

Kết quả:
- `OCRJobRepository.claim_next_pending_job()` claim job `pending` cũ nhất bằng `FOR UPDATE SKIP LOCKED`.
- Trong cùng transaction claim, job được đổi sang `ocr_running`, tăng `attempts`, set `started_at` và clear `error_message`.
- `OCRWorker.run_once()` dùng claim method, commit claim trước khi xử lý OCR dài, rồi `process_job()` tiếp tục lifecycle success/error hiện có.
- Smoke hai DB session song song pass: session đầu claim được job, session thứ hai nhận `None`, job cuối cùng có `attempts=1` và `started_at`.
- Worker service đã được dừng tạm để tránh ăn job smoke trong lúc kiểm tra; sau task cần start lại worker.
- Retry policy, `max_attempts`, failed reason taxonomy và queue readiness vẫn là mục tiêu tiếp theo.

Worker job lifecycle survey ngày 2026-06-05:

```bash
sed -n '1,320p' apps/api/app/workers/ocr_worker.py
sed -n '730,800p' apps/api/app/repositories/document_repository.py
sed -n '40,125p' apps/api/app/services/document_service.py
sed -n '420,465p' apps/api/app/services/document_service.py
sed -n '670,725p' apps/api/app/services/document_service.py
sed -n '1,180p' apps/api/app/models/document.py
git diff --check
```

Kết quả khảo sát:
- Worker entrypoint `apps/worker/runner.py` gọi `run_forever(SessionLocal)`, mỗi vòng tạo DB session mới, chạy `OCRWorker.run_once()`, nếu không có job thì sleep 5 giây.
- `OCRJobRepository.get_next_pending_job()` hiện chỉ `SELECT` job `status='pending'` cũ nhất, không `FOR UPDATE`, không `SKIP LOCKED`, không đổi status trong cùng transaction.
- `OCRWorker.process_job()` đổi job sang `ocr_running`, tăng `attempts`, set `started_at`, commit; sau đó mới xử lý document. Nếu có hai worker gọi cùng lúc, cả hai có thể lấy cùng một pending job trước khi worker đầu commit trạng thái chạy.
- Upload một file, multi-file và zip đều tạo `ocr_jobs.status='pending'`, `job_type='ocr'`, rồi set document `ocr_pending`.
- Reprocess thủ công và thay đổi source file đều kiểm tra `has_active_job(document_id)` trước, tạo job `job_type='reprocess'`, `reason`, rồi set document `reprocess_pending`.
- `has_active_job()` chỉ tính job status `pending` và `ocr_running`; job `failed`/`completed` không chặn reprocess. Job type không ảnh hưởng active check.
- Khi worker xử lý job OCR thường, document chuyển `ocr_running -> chunking -> searchable`; khi reprocess, document chuyển `reprocess_running -> chunking -> searchable`.
- Khi lỗi, job chuyển `failed`, ghi `error_message`; OCR job thường đưa document về `failed`, reprocess đưa document về trạng thái trước đó nếu có. Các source file chưa `completed` được set `failed`.
- Chưa có retry policy, `max_attempts`, delayed retry, hoặc phân biệt lỗi recoverable/unrecoverable. `attempts` chỉ tăng một lần trong mỗi lần process job, nhưng failed job không được đưa về pending.
- Health hiện chỉ có `/health` trả `{"status":"ok"}`, chưa có worker/queue readiness hoặc metrics về pending/running/failed job.

Review queue UX polish kiểm tra ngày 2026-06-05:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/scripts/smoke_review_queue_pagination.py
docker compose run --rm --no-deps web npm run build
docker compose up -d api postgres redis qdrant
docker compose exec -T api python -m app.scripts.smoke_review_queue_pagination
git diff --check
```

Kết quả:
- Dashboard review queue hiển thị `Trang X/Y` cạnh khoảng item và tổng số item.
- Pager có nút nhảy trang đầu/cuối dạng icon, cùng nút `Trước/Sau` hiện có.
- Offset/limit trong UI được đồng bộ theo response API để chuyển trang và refresh ổn định hơn.
- Action `Đã review` vẫn refresh page hiện tại; nếu page rỗng sau thao tác thì tự lùi page.
- Thêm script `python -m app.scripts.smoke_review_queue_pagination` seed 7 chunk cần review, kiểm tra page 1/page 2 không trùng item, filter phụ lục và filter confidence thấp, rồi cleanup mặc định.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.

Smoke API auth wrapper kiểm tra ngày 2026-06-05:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/scripts/smoke_api_workflows.py
docker compose up -d api postgres redis qdrant
docker compose exec -T api python -m app.scripts.smoke_api_workflows
git diff --check
```

Kết quả:
- Thêm script `python -m app.scripts.smoke_api_workflows` chạy HTTP smoke tái sử dụng được cho auth, review queue, semantic search và review action.
- Script login admin local và user thường tạm bằng API `/api/v1/auth/login`.
- Script seed document/chunk smoke tối thiểu qua DB, index Qdrant payload thật và cleanup mặc định sau khi chạy.
- Admin gọi review queue thành công; user thường gọi review queue nhận `403`.
- Semantic search cơ bản và filter `section_role=appendix` trả dữ liệu smoke đúng filter.
- User thường gọi action review chunk nhận `403`; admin gọi action thành công, DB và Qdrant payload đều cập nhật `requires_review=false`.
- Sau review, queue appendix và search `requires_review=true` không còn trả chunk đã review.

Documents pagination polish kiểm tra ngày 2026-06-05:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/document.py apps/api/app/repositories/document_repository.py apps/api/app/services/document_service.py apps/api/app/routers/documents.py apps/api/app/scripts/smoke_documents_pagination.py
docker compose run --rm --no-deps web npm run build
docker compose up -d api postgres redis qdrant
docker compose exec -T api python -m app.scripts.smoke_documents_pagination
git diff --check
```

Kết quả:
- Backend `GET /api/v1/documents` trả response phân trang `items`, `total`, `limit`, `offset`.
- Repository có count matching cùng filter với list: search text, status, document type và business type.
- Query danh sách có sort ổn định với tie-breaker `Document.id` để hạn chế trùng item giữa các page.
- Frontend `/documents` dùng response phân trang qua service/composable, hiển thị tổng số, khoảng item hiện tại và nút `Trước/Sau`.
- Khi đổi search/filter/sort, UI reset offset về `0`; refresh giữ nguyên page hiện tại.
- Smoke pagination pass với 3 document tạm: page 1/page 2 không trùng item, total đúng, filter/search/sort còn hoạt động và dữ liệu smoke được cleanup mềm.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.

Chuẩn hóa kế hoạch thực thi kiểm tra ngày 2026-06-05:

```bash
sed -n '1,240p' ROADMAP.md
sed -n '1,240p' TASK_NEXT.md
git diff --check
```

Kết quả:
- `TASK_NEXT.md` đã được cập nhật thành kế hoạch tuần tự theo phase, khóa phase sau cho đến khi phase trước hoàn thành.
- Phase 1 được chia nhỏ thành các mục tiêu độc lập: documents pagination, smoke API auth wrapper và review queue UX polish.
- Mỗi mục tiêu/phase đều có yêu cầu đọc lại `ROADMAP.md`, cập nhật trạng thái và chọn bước tiếp theo trước khi tiếp tục.

Review queue pagination polish kiểm tra ngày 2026-06-05:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/document.py apps/api/app/repositories/document_repository.py apps/api/app/services/document_service.py apps/api/app/routers/documents.py apps/api/app/scripts/smoke_appendix_data.py
docker compose run --rm --no-deps web npm run build
docker compose exec -T api python -m app.scripts.smoke_appendix_data
python3 <review queue pagination smoke script>
python3 <review queue user forbidden smoke script>
git diff --check
```

Kết quả:
- Endpoint admin-only `GET /api/v1/documents/chunks/review-queue` trả response phân trang `items`, `total`, `limit`, `offset`.
- Repository có count matching cùng filter `section_role`, `document_id`, `max_confidence`; query list có sort ổn định bằng confidence, `updated_at` và `id` để tránh trùng item giữa các page.
- Frontend Dashboard hiển thị tổng số review queue, khoảng item hiện tại, nút `Trước/Sau`, giữ filter khi chuyển trang và reset về trang đầu khi lọc lại.
- Sau khi admin bấm `Đã review`, queue refresh page hiện tại; nếu page rỗng sau thao tác thì tự lùi về page trước.
- Smoke HTTP pass: `limit=5&offset=0` và `limit=5&offset=5` không trùng item khi total đủ lớn; response có đủ `items/total/limit/offset`; filter appendix vẫn chỉ trả appendix nếu có dữ liệu.
- Smoke phân quyền pass: user thường `queue-page-smoke-1780659295@example.local` gọi review queue nhận `403`.
- Frontend build pass; vẫn có warning chunk PrimeVue lớn như trước, không fail.

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
contracts/dispatches <-> document detail (liên kết hai chiều metadata nghiệp vụ)
```

Phase 8 / Mục tiêu 1 — Khảo sát job kẹt và thiết kế lease recovery (2026-06-06):

```bash
sed -n '29,45p' apps/api/app/workers/ocr_worker.py
sed -n '60,195p' apps/api/app/workers/ocr_worker.py
sed -n '271,315p' apps/api/app/workers/ocr_worker.py
sed -n '415,433p' apps/api/app/workers/ocr_worker.py
sed -n '755,865p' apps/api/app/repositories/document_repository.py
sed -n '106,126p' apps/api/app/models/document.py
sed -n '1,52p' apps/api/app/core/config.py
git diff --check
```

Kiểm tra: khảo sát read-only, không thay đổi runtime; `git diff --check` pass.

Kết quả khảo sát lifecycle job `ocr_running`:

- Worker entrypoint `run_forever()` tạo session mới mỗi vòng, gọi `OCRWorker.run_once()` → `claim_next_pending_job()` → `commit` claim → `process_job()`.
- `OCRJobRepository.claim_next_pending_job()` chọn job `pending` cũ nhất thỏa `next_run_at` rỗng hoặc đã tới hạn, khóa `FOR UPDATE SKIP LOCKED`, rồi trong cùng transaction: `status='ocr_running'`, `attempts += 1`, `started_at=now`, clear `next_run_at`/`failed_reason`/`error_message`.
- Job giữ `ocr_running` suốt `process_job()` cho đến khi thành công (`completed`) hoặc lỗi (`pending` retry hoặc `failed`). Không có lease timeout hay worker id trên bảng `ocr_jobs`.
- `ACTIVE_STATUSES = {pending, ocr_running}`; `has_active_job()` chặn tạo job reprocess mới khi job cũ còn `ocr_running` — đây là nguyên nhân chính document “kẹt” sau worker crash.
- Heartbeat file `/tmp/worker.heartbeat` chỉ ghi timestamp local trong container, không dùng cho lease recovery cross-worker.

Trạng thái document/source file kẹt khi worker crash giữa chừng:

| Giai đoạn trong `process_job()` | Document status | Source file (`document_files`) | Job status |
| --- | --- | --- | --- |
| Ngay sau commit đầu (OCR/reprocess extract) | `ocr_running` / `reprocess_running` | `pending` hoặc đang chuyển `ocr_running` từng file | `ocr_running` |
| Giữa vòng `_extract_document_pages()` | như trên | Một số file `ocr_running`, file trước đó có thể đã `completed` | `ocr_running` |
| Sau extract, trước chunk xong | `chunking` | Thường đã `completed` | `ocr_running` |
| Giữa embed/Qdrant | `chunking` | `completed` | `ocr_running` |

- Retry policy Phase 2 (`_record_job_failure`) chỉ chạy khi worker bắt được exception; process bị kill (SIGKILL, OOM, `docker compose stop`) không gọi nhánh này.
- Lỗi recoverable dùng `failed_reason='processing_error'`; stale recovery nên dùng reason riêng `worker_lease_expired` (vẫn recoverable nếu còn lượt `max_attempts`).

Policy lease timeout MVP đề xuất (triển khai ở Mục tiêu 2):

Config mới trong `apps/api/app/core/config.py`:

- `OCR_JOB_LEASE_TIMEOUT_SECONDS: int = 3600` — env `OCR_JOB_LEASE_TIMEOUT_SECONDS`. Ngưỡng mặc định 1 giờ: đủ cho PDF scan lớn on-prem; ops có thể tăng qua env nếu job OCR thật thường > 1h.
- (Tuỳ chọn MVP) `OCR_JOB_STALE_RECOVERY_ENABLED: bool = True` — tắt recovery mà không đổi timeout khi debug.

Phát hiện stale:

- Điều kiện: `status = 'ocr_running'`, `deleted_at IS NULL`, `started_at IS NOT NULL`, `started_at + lease_timeout < now()`.
- Không dùng heartbeat file; `started_at` tại thời điểm claim là lease marker duy nhất cần cho MVP.

Hành vi recovery (không phá atomic claim và retry policy Phase 2):

1. Chạy trong worker loop **trước** `claim_next_pending_job()` (MVP); mỗi job stale recover trong transaction riêng với `FOR UPDATE SKIP LOCKED` trên row job (tránh hai worker recover cùng lúc).
2. **Không** tăng `attempts` lúc recovery — `attempts` đã tăng lúc claim; lần claim tiếp theo mới tăng thêm (giữ đúng semantics retry hiện có).
3. Clear `started_at` khi đưa job về `pending` để tránh recover lặp ngay.
4. Nếu `attempts < max_attempts` (recoverable stale):
   - Job → `pending`, `next_run_at = now + RETRY_DELAY_SECONDS` (30s, dùng hằng số hiện có), `failed_reason='worker_lease_expired'`, `error_message` mô tả lease timeout.
   - Document → `ocr_pending` (job `ocr`) hoặc `reprocess_pending` (job `reprocess`).
   - Source file chưa `completed` → `pending` (tái sử dụng `_reset_incomplete_files_pending`).
   - Ghi audit/log: `ocr_job.stale_recovered` với `job_id`, `document_id`, `attempts`, `started_at`, `lease_timeout_seconds`.
5. Nếu `attempts >= max_attempts`:
   - Job → `failed`, `failed_reason='worker_lease_expired'`, `completed_at=now`, `next_run_at=NULL`.
   - Document → `failed` (ocr) hoặc fallback trạng thái trước reprocess (giống `_record_job_failure`).
   - Source file chưa completed → `failed`.
6. Thêm `worker_lease_expired` vào tập lỗi **recoverable** (không nằm trong `UNRECOVERABLE_FAILURE_REASONS`) để nhất quán với retry policy.
7. Job đang chạy thật **không** bị recover nhầm miễn là `lease_timeout` lớn hơn thời gian xử lý tối đa kỳ vọng; smoke Mục tiêu 5 cần job “fresh” và job stale tách biệt.

Tương thích atomic claim:

- Recovery chỉ đụng `ocr_running` quá hạn, không đụng `pending`.
- Sau recovery, job về `pending` và được claim lại qua `claim_next_pending_job()` với `SKIP LOCKED` như hiện tại.
- Smoke `smoke_worker_claim_atomic` và `smoke_worker_retry_policy` vẫn hợp lệ nếu recovery không chạy trên job non-stale.

Rủi ro / việc cần làm ở Mục tiêu 2:

- Job `job_type='ocr'` dùng `create_page()` không idempotent: nếu crash sau khi đã tạo một phần pages/chunks, retry có thể duplicate dữ liệu. Job `reprocess` an toàn hơn vì `replace_pages_for_document` / `replace_chunks_for_document`.
- Đề xuất MVP Mục tiêu 2: trước khi đưa job ocr stale về `pending`, xóa pages/chunks (và point Qdrant tương ứng nếu đã upsert) tạo trong attempt bị gián đoạn, **hoặc** chuyển document sang luồng reprocess thay vì retry ocr trực tiếp — cần chọn một hướng trong implementation và bổ sung smoke.
- Ops counter `running` trên `/api/v1/ops/worker-queue` vẫn đếm job `ocr_running` kể cả stale cho đến khi recovery chạy; Mục tiêu 3 có thể thêm counter/list stale.

Chưa thay đổi code runtime trong mục tiêu này (chỉ tài liệu khảo sát).

Phase 8 / Mục tiêu 2 — Stale-job recovery backend (2026-06-06):

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/core/config.py apps/api/app/repositories/document_repository.py apps/api/app/services/ocr_job_recovery_service.py apps/api/app/workers/ocr_worker.py
docker compose stop worker
docker compose exec -T api python -m app.scripts.smoke_worker_claim_atomic
docker compose exec -T api python -m app.scripts.smoke_worker_retry_policy
git diff --check
```

Kết quả:
- Config mới: `OCR_JOB_LEASE_TIMEOUT_SECONDS` (mặc định 3600), `OCR_JOB_STALE_RECOVERY_ENABLED` (mặc định true).
- `OCRJobRepository.lock_next_stale_running_job()` khóa job `ocr_running` có `started_at` quá hạn bằng `FOR UPDATE SKIP LOCKED`; thêm `count_stale_running_jobs()` phục vụ ops sau này.
- `DocumentRepository.soft_delete_all_pages_for_document()` và `soft_delete_all_chunks_for_document()` hỗ trợ cleanup partial state trước retry.
- `OCRJobRecoveryService.recover_stale_jobs()` xử lý stale job: còn lượt → `pending` + `failed_reason=worker_lease_expired` + sync document/file; hết lượt → `failed`; ghi audit `ocr_job.stale_recovered` và log INFO.
- Cleanup có kiểm soát: job `ocr` retry xóa pages/chunks/Qdrant; job `reprocess` retry chỉ xóa chunks khi document đang `chunking`.
- `OCRWorker.run_once()` gọi recovery trước claim; job đang chạy thật không bị recover nhầm vì lease mặc định 3600s.
- Smoke `smoke_worker_claim_atomic` và `smoke_worker_retry_policy` pass sau thay đổi; `git diff --check` pass.

Phase 8 / Mục tiêu 3 — Ops endpoint và runbook job kẹt (2026-06-06):

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/ops.py apps/api/app/repositories/document_repository.py apps/api/app/services/ocr_job_recovery_service.py apps/api/app/services/ops_service.py apps/api/app/routers/ops.py apps/api/app/scripts/smoke_worker_operations.py
docker compose stop worker
docker compose exec -T api python -m app.scripts.smoke_worker_operations
git diff --check
```

Kết quả:
- Mở rộng `GET /api/v1/ops/worker-queue` với `stale_running`, `lease_timeout_seconds`, `stale_recovery_enabled`.
- Thêm admin-only `GET /api/v1/ops/worker-queue/stale-jobs` liệt kê job/document stale (job id, document status, `stale_for_seconds`, attempts).
- Thêm admin-only `POST /api/v1/ops/worker-queue/recover-stale` và `POST /api/v1/ops/worker-queue/stale-jobs/{job_id}/recover` gọi `OCRJobRecoveryService` với audit `source=admin_ops`.
- User thường bị `403` ở endpoint ops (router `require_admin`).
- Cập nhật `docs/WORKER_OPS_RUNBOOK.md`: command curl liệt kê/recover stale, cấu hình lease, hướng dẫn dừng worker khi recover thủ công.
- Smoke `smoke_worker_operations` pass: seed job stale, admin list/recover, user 403; `git diff --check` pass.

Phase 8 / Mục tiêu 4 — Runbook nâng cấp Alembic production (2026-06-06):

```bash
git diff --check
```

Kiểm tra: tài liệu runbook; `git diff --check` pass.

Kết quả:
- Thêm `docs/PRODUCTION_UPGRADE_RUNBOOK.md`: checklist trước upgrade, backup PostgreSQL, thứ tự **dừng worker → migrate → start api/worker/web**, smoke sau upgrade, rollback application và restore DB tối thiểu.
- Liên kết tới `docs/STORAGE_BACKUP_RESTORE_RUNBOOK.md`, `docs/ON_PREM_ENV_RUNBOOK.md`, `docs/WORKER_OPS_RUNBOOK.md`.
- Command copy-paste cho on-prem Docker Compose: `alembic current/heads/upgrade head`, `docker compose stop worker web`, `docker compose up -d api worker web`, `smoke_worker_operations`, health checks.

Phase 8 / Mục tiêu 5 — Smoke worker recovery sau crash mô phỏng (2026-06-06):

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/scripts/smoke_worker_stale_recovery.py
docker compose stop worker
docker compose exec -T api python -m app.scripts.smoke_worker_stale_recovery
docker compose exec -T api python -m app.scripts.smoke_worker_claim_atomic
docker compose exec -T api python -m app.scripts.smoke_worker_retry_policy
git diff --check
```

Kết quả:
- Thêm `python -m app.scripts.smoke_worker_stale_recovery`: seed job `ocr_running` stale + job đang chạy thật, gọi `OCRWorker.run_once()` recovery path, xác nhận stale → `pending`/`ocr_pending`/`worker_lease_expired`, partial pages cleanup, fresh job vẫn `ocr_running`, audit `ocr_job.stale_recovered` source `worker`.
- Smoke pass với worker dừng; `smoke_worker_claim_atomic` và `smoke_worker_retry_policy` không regression.
- Cập nhật `docs/WORKER_OPS_RUNBOOK.md` và `docs/PRODUCTION_UPGRADE_RUNBOOK.md` với command smoke mới.

**Phase 8 hoàn thành ngày 2026-06-06.** Phase tiếp theo: Phase 9 - RAG UX Và Search Nâng Cao (`TASK_NEXT.md`).

Phase 9 / Mục tiêu 1 — Khảo sát RAG API và thiết kế UX dashboard (2026-06-06):

```bash
sed -n '1,190p' apps/api/app/services/rag_answer_service.py
sed -n '1,85p' apps/api/app/schemas/search.py
sed -n '1,55p' apps/api/app/routers/search.py
sed -n '1,75p' apps/api/app/scripts/smoke_rag_answer.py
sed -n '1,35p' apps/web/services/search.service.ts
sed -n '1,36p' apps/web/composables/useSemanticSearch.ts
sed -n '363,441p' apps/web/pages/dashboard.vue
git diff --check
```

Kiểm tra: khảo sát read-only, không thay đổi UI; `git diff --check` pass.

Kết quả khảo sát API `POST /api/v1/search/answer`:

- Router `apps/api/app/routers/search.py`: cùng router `/search`, dependency `get_current_user` (admin/user đã login đều gọi được; chưa login → 401).
- Request `RagAnswerRequest` kế thừa `SemanticSearchRequest` (query, limit, metadata filters giống semantic search) + `min_score` (mặc định 0.35), `max_citations` (mặc định 4, max 8), `limit` retrieval mặc định 6 (max 12).
- Response `RagAnswerResponse`: `query`, `answer`, `grounded` (bool), `confidence` (0–1), `fallback_reason` (`null` hoặc `insufficient_evidence`), `citations[]`.
- Mỗi citation (`RagCitation`): `document_id`, `chunk_id`, `score`, `quote`, `title`, metadata văn bản (`document_number`, `issued_date`, `issuing_agency`, `business_type`), vị trí (`page_from`, `page_to`, `section_role`, `section_path`).
- `RagAnswerService` extractive local-only: gọi `SearchService.semantic_search()` → lọc theo `min_score` và overlap term query → ghép answer dạng “Dựa trên các đoạn đã truy xuất: …” từ `quote` citation; không gọi LLM/cloud.
- Khi không đủ căn cứ: `grounded=false`, `fallback_reason=insufficient_evidence`, `answer` là câu fallback cố định tiếng Việt trong `RagAnswerConfig`, `confidence=0`; citations vẫn có thể trả về nếu retrieval có kết quả nhưng không đạt ngưỡng evidence.
- Smoke `python -m app.scripts.smoke_rag_answer` seed benchmark fixture, kiểm tra grounded + fallback; unit test `test_rag_answer_service.py` cover grounded/fallback.

Hiện trạng frontend dashboard:

- `apps/web/pages/dashboard.vue`: card **Semantic search** với `useSemanticSearch()`, filters `SemanticSearchFilters` (business_type, document_number, issued_date, doc_group, section_role, requires_review, contract_number, supplier_name, contract_status, limit).
- `apps/web/services/search.service.ts`: chỉ `POST /search/semantic`; `normalizeSearchPayload()` đã map đủ filter metadata sang API.
- Chưa có type `RagAnswerResponse`/`RagCitation`, service method `/search/answer`, composable RAG, hay component Q&A.
- Document detail chưa có anchor `#chunk-{id}`; MVP citation link tới `/documents/{document_id}` (có thể bổ sung scroll-to-chunk ở phase sau).

States UI MVP đề xuất (Mục tiêu 2):

| State | Điều kiện | Hiển thị |
| --- | --- | --- |
| Idle | Chưa gửi câu hỏi | Input + gợi ý ngắn; không hiện answer cũ hoặc clear sau “Xóa” |
| Loading | Đang gọi API | Disable submit, text “Đang trả lời…” |
| Grounded | `grounded=true` | Answer + confidence; danh sách citation (quote + metadata + link document) |
| Insufficient evidence | `grounded=false` && `fallback_reason=insufficient_evidence` | `Message` severity warn; hiển thị `answer` fallback như giải thích, **không** trình bày như câu trả lời chắc chắn; citations phụ (nếu có) với nhãn “Tham khảo yếu” |
| Error | HTTP/exception | `Message` severity error (pattern giống semantic search) |
| Empty query | Input rỗng | Validation client “Vui lòng nhập câu hỏi” |

Kiến trúc frontend đề xuất (`page -> composable -> service -> API`):

```text
dashboard.vue
  -> useRagAnswer()
       -> createSearchService().answer()  # mở rộng search.service.ts
            -> POST /api/v1/search/answer
  -> (tùy chọn) component RagAnswerPanel.vue cho input/answer/citations
```

Chi tiết triển khai Mục tiêu 2:

- **Types** (`apps/web/types/document.ts` hoặc `types/search.ts`): `RagCitation`, `RagAnswerResponse`; `RagAnswerFilters extends SemanticSearchFilters` + optional `min_score`, `max_citations`.
- **Service**: thêm `answer(query, filters)` reuse `normalizeSearchPayload()` + default `min_score`/`max_citations` từ API nếu UI không expose.
- **Composable** `useRagAnswer.ts`: state `question`, `answer`, `citations`, `grounded`, `confidence`, `fallbackReason`, `loading`, `error`, `hasAsked`; method `ask(question, filters)`.
- **Dashboard layout**: thêm Card **Hỏi đáp (RAG)** phía trên hoặc dưới Semantic search; **tái sử dụng cùng object `filters`** cho metadata lọc retrieval (MVP không thêm bộ lọc riêng); input câu hỏi riêng `ragQuestion` để tách UX search vs Q&A.
- **Citation row**: blockquote `quote`; meta dòng (title/link, số VB, trang, section_role/path, score); nút/link “Mở văn bản” → `/documents/{document_id}`.
- **Không** thêm LLM/cloud; giữ extractive backend hiện có; không đổi contract API trừ khi phát sinh bug.

Rủi ro / ghi chú:

- Answer extractive có thể lặp quote khi nhiều citation — chấp nhận MVP; không paraphrase.
- User có thể hiểu nhầm fallback text là câu trả lời — UI phải phân biệt rõ bằng label/warn state.
- Semantic search và RAG dùng chung filters: sau khi đổi filter, nên clear RAG answer cũ hoặc hiện hint “Bấm Hỏi lại sau khi đổi lọc”.

Chưa thay đổi code runtime/UI trong mục tiêu này (chỉ tài liệu khảo sát).

Phase 9 / Mục tiêu 2 — RAG Q&A UI trên dashboard (2026-06-06):

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

Kiểm tra: `npm run build` pass (cần `WEB_MEMORY_LIMIT=4g` vì container `web` mặc định 512M bị OOM khi build SSR); `git diff --check` pass.

Đã triển khai:

- **Types** (`apps/web/types/document.ts`): `RagCitation`, `RagAnswerResponse`, `RagAnswerFilters`.
- **Service** (`apps/web/services/search.service.ts`): `answer()` gọi `POST /search/answer`, tái dùng `normalizeSearchPayload()` với `defaultLimit=6`.
- **Composable** (`apps/web/composables/useRagAnswer.ts`): state loading/grounded/citations/fallback; methods `ask`, `clear`, `resetQuestion`.
- **Component** (`apps/web/components/RagAnswerPanel.vue`): input câu hỏi, grounded answer + confidence, warn `insufficient_evidence` (không trình bày như câu trả lời chắc chắn), citation quote + metadata + link `/documents/{id}`.
- **Dashboard** (`apps/web/pages/dashboard.vue`): Card **Hỏi đáp (RAG)** dưới Semantic search; dùng chung `filters` metadata; watch filter → clear answer + hint “Hỏi lại”.

**Phase 9 hoàn thành ngày 2026-06-06.** Phase tiếp theo: Phase 10 - Module Quyết Định Và Thông Báo (`TASK_NEXT.md`).

Phase 9 / Mục tiêu 3 — Smoke và runbook RAG answer trên web (2026-06-06):

```bash
docker compose exec -T api python -m app.scripts.smoke_rag_answer
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

Kiểm tra: `smoke_rag_answer` pass; `npm run build` pass với `WEB_MEMORY_LIMIT=4g`; `git diff --check` pass.

Đã bổ sung:

- **Runbook** `docs/RAG_ANSWER_RUNBOOK.md`: smoke API, `--keep-data` cho UI manual, checklist dashboard (grounded / `insufficient_evidence` / citation / regression semantic search), lệnh build frontend.
- **README**: link runbook, hướng dẫn `--keep-data` và checklist UI.
- **Smoke** `smoke_rag_answer.py`: in gợi ý runbook khi `--keep-data`.

Chi tiết phase và mục tiêu tiếp theo nằm trong `TASK_NEXT.md` và `ROADMAP.md`.

Phase 10 / Mục tiêu 1 — Khảo sát và thiết kế module quyết định/thông báo (2026-06-07):

```bash
git diff --check
```

Kiểm tra: `git diff --check` pass.

Kết quả khảo sát:

- Đọc pattern `contract_records`, `dispatch_records`: metadata 1-1 `documents`, partial unique index active, audit soft delete admin-only, API `by-document`, frontend drill-down từ document detail.
- Catalog hiện có `business_type=decision`; `document_type` OCR có `QĐ` và `TB`; chunking nhóm A đã hỗ trợ quyết định theo `Điều`.
- Quyết định scope MVP trong `docs/DOMAIN_MODULE_DECISION.md` (module thứ ba Phase 10):
  - Bảng `decision_records`, model `DecisionRecord`, API `/api/v1/decisions`, UI `/decisions`, audit entity `decision`.
  - Trường MVP: `decision_kind` (`decision` | `notification`), số/ký hiệu, ngày ban hành, đơn vị ban hành, trích yếu, `effective_from`/`effective_to`, trạng thái, ghi chú.
  - Mapping: cả quyết định và thông báo dùng `business_type=decision`; phân biệt bằng `decision_kind` và/hoặc `document_type` OCR — không thêm catalog `notification` ở MVP.
  - Status: `draft`, `registered`, `effective`, `expired`, `revoked`, `archived`.
  - Quyền/audit giống contracts/dispatches; search filter metadata decision để sau MVP.
- Không thay đổi runtime (không schema/API/UI); không cloud/LLM.

Phase 10 / Mục tiêu 2 — Schema và migration `decision_records` (2026-06-07):

```bash
docker compose exec -T api alembic upgrade head
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/models/decision.py apps/api/app/models/document.py apps/api/alembic/versions/0014_decision_records.py
git diff --check
```

Kiểm tra: Alembic upgrade `0013_dispatch_records` → `0014_decision_records` pass; `py_compile` pass; `git diff --check` pass.

Đã bổ sung:

- Model `DecisionRecord` (`apps/api/app/models/decision.py`) và relationship `Document.decision_record`.
- Migration `0014_decision_records`: `decision_kind`, số/ký hiệu, ngày ban hành, đơn vị ban hành, trích yếu, `effective_from`/`effective_to`, trạng thái, ghi chú; audit fields và soft delete.
- Partial unique index `ux_decision_records_document_active` và index filter MVP theo thiết kế mục tiêu 1.
- Alembic current là `0014_decision_records (head)`; bảng không lưu OCR text/chunk.

Phase 10 / Mục tiêu 3 — Backend API `/api/v1/decisions` và smoke (2026-06-07):

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/decision.py apps/api/app/repositories/decision_repository.py apps/api/app/services/decision_service.py apps/api/app/routers/decisions.py apps/api/app/scripts/smoke_decision_api.py apps/api/app/main.py
docker compose exec -T api python -m app.scripts.smoke_decision_api
git diff --check
```

Kiểm tra: `py_compile` pass; `smoke_decision_api` pass; `git diff --check` pass.

Đã bổ sung:

- Router `decisions`, `DecisionService`, `DecisionRepository`, schema Pydantic theo `router -> service -> repository`.
- Endpoint: list/get/create/update/delete + `GET /decisions/by-document/{document_id}`; filter `decision_kind`, hiệu lực, số văn bản, trạng thái.
- Audit `decision.created/updated/deleted`; user create/update; admin soft delete (`403` user).
- Smoke `smoke_decision_api` tái chạy được với cleanup mặc định.

Phase 10 / Mục tiêu 4 — Frontend `/decisions` và liên kết document detail (2026-06-07):

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
docker compose build web && docker run --rm --memory=4g -e NODE_OPTIONS=--max-old-space-size=3072 app-qlvb-phongvattu-web:latest npm run build
docker compose exec -T api python -m app.scripts.smoke_decision_api
git diff --check
```

Kiểm tra:
- `docker compose run ... npm run build`: client + server compile OK; Nitro báo `EBUSY` khi `rmdir /app/.output` do anonymous volume trong `docker-compose.yml` — build production pass qua `docker compose build web` + `docker run ... npm run build`.
- `smoke_decision_api` pass; `git diff --check` pass.

Đã bổ sung:

- Types `apps/web/types/decision.ts`, service `decision.service.ts`, composable `useDecisions.ts`, page `/decisions` (list/filter/form CRUD).
- Nav item **Quyết định** trong `app.vue`.
- Document detail: card Quyết định & thông báo, liên kết hai chiều (`document_id`/`create=1`, nút Mở Quyết định).
- Dashboard search preset từ decisions (`business_type=decision`).

**Phase 10 hoàn thành ngày 2026-06-07.**

---

## Phase 11 — Search Filter Metadata Dispatch Và Decision

### Mục tiêu 1 — Khảo sát contract filter và thiết kế tham số dispatch/decision (2026-06-07)

Kiểm tra bắt buộc:

```bash
git diff --check
```

Kết quả: pass.

#### Khảo sát pattern contract filter hiện có

| Thành phần | Hành vi hiện tại |
|------------|------------------|
| `SemanticSearchRequest` | Filter document core (`business_type`, `document_number`, `issued_date`, `doc_group`, `section_role`, `requires_review`) + filter module hợp đồng (`contract_number`, `supplier_name`, `contract_status`). **Chưa có** `issuing_agency` ở request (chỉ trả trong result từ Qdrant payload). |
| `SearchService._resolve_contract_document_ids()` | Kích hoạt khi **bất kỳ** `contract_number` / `supplier_name` / `contract_status` có giá trị. Trả `None` nếu không có filter hợp đồng; trả `set()` rỗng → `semantic_search()` trả `[]` sớm. |
| `ContractRepository.list_document_ids_by_metadata()` | Query `contract_records` active (`deleted_at IS NULL`), join `documents` active; `contract_number`/`supplier_name` dùng `ilike`, `status` exact match. |
| Luồng search | Pre-resolve `document_id` → truyền `document_ids` vào Qdrant post-filter, `_matching_chunk_ids`, `_keyword_candidates`. **Không** sửa Qdrant payload. |
| `SearchService._attach_contract_metadata()` | Sau ranking, batch `map_active_by_document_ids()` → enrich `contract_id`, `contract_number`, `supplier_name`, `contract_status` trên `SemanticSearchResult`. |
| `RagAnswerService` | Kế thừa toàn bộ filter qua `SearchBackend` protocol; không logic filter riêng. |
| `dashboard.vue` | Filter hợp đồng luôn hiển thị (chưa conditional theo `business_type`). Preset route: `q`, `document_number`, `contract_number`, `supplier_name`. |
| `/contracts` preset | `dashboardSearchLink()` truyền `q` + `document_number` (chưa truyền `contract_number`). |
| `/dispatches` preset | `q` + `document_number` (chưa `dispatch_type` / `dispatch_status`). |
| `/decisions` preset | `q` + `document_number` + `business_type=decision` (chưa `decision_kind` / `decision_status`). |

#### Quyết định thiết kế tham số API/UI (draft triển khai mục tiêu 2–5)

**Nguyên tắc:** Không sửa Qdrant payload / không re-index. Pre-resolve `document_id` từ PostgreSQL (`dispatch_records`, `decision_records`) giống `contract_records`. Prefix tên field cho trường chỉ thuộc module (mirror `contract_status`); tái dùng field document core khi semantics trùng list API module.

**Bảng tham số filter mới trên `SemanticSearchRequest` / `RagAnswerRequest`:**

| Tham số API | Kiểu | Dispatch | Decision | Ghi chú |
|-------------|------|:--------:|:--------:|---------|
| `dispatch_type` | `incoming` \| `outgoing` | ✓ | — | Kích hoạt nhóm pre-resolve dispatch khi có giá trị |
| `dispatch_status` | enum MVP dispatch | ✓ | — | Tên API `dispatch_status` (không dùng `status` chung) |
| `decision_kind` | `decision` \| `notification` | — | ✓ | Kích hoạt nhóm pre-resolve decision khi có giá trị |
| `decision_status` | enum MVP decision | — | ✓ | Tên API `decision_status` |
| `effective_from` | `date` | — | ✓ (opt) | Chỉ decision; `>=` trên `decision_records.effective_from` |
| `effective_to` | `date` | — | ✓ (opt) | Chỉ decision; `<=` trên `decision_records.effective_to` |
| `document_number` | `string` | ✓ (kèm) | ✓ (kèm) | **Tái dùng** field hiện có — filter Qdrant/document **và** truyền vào repo module khi nhóm tương ứng active |
| `issuing_agency` | `string` | ✓ (kèm) | ✓ (kèm) | **Thêm mới** ở request — filter document layer (mục tiêu 3) **và** repo module khi nhóm active; `ilike` như list API |

**Không thêm** `dispatch_document_number` / `decision_document_number` — trùng semantics với `document_number` đã có; contract đã tách `contract_number` vì khác cột DB.

**Giá trị enum status (đồng bộ module list API):**

- `dispatch_status`: `draft`, `registered`, `processing`, `completed`, `archived`
- `decision_status`: `draft`, `registered`, `effective`, `expired`, `revoked`, `archived`

**Điều kiện kích hoạt pre-resolve theo nhóm module:**

| Nhóm | Kích hoạt khi có bất kỳ | Tham số bổ sung truyền vào repo (nếu client gửi) |
|------|-------------------------|---------------------------------------------------|
| Contract (giữ nguyên) | `contract_number`, `supplier_name`, `contract_status` | — |
| Dispatch | `dispatch_type`, `dispatch_status` | `document_number`, `issuing_agency` |
| Decision | `decision_kind`, `decision_status`, `effective_from`, `effective_to` | `document_number`, `issuing_agency` |

`document_number` / `issuing_agency` **một mình** không kích hoạt pre-resolve module (giống `document_number` không kích hoạt contract pre-resolve hôm nay).

**Giao `document_id` khi nhiều nhóm filter module cùng lúc:**

```text
contract_ids  = _resolve_contract_document_ids()   # None | set
dispatch_ids  = _resolve_dispatch_document_ids()   # None | set
decision_ids  = _resolve_decision_document_ids()   # None | set

active_sets = [s for s in (contract_ids, dispatch_ids, decision_ids) if s is not None]
if any(s == set() for s in active_sets): return []   # sớm
module_document_ids = intersection(active_sets) if active_sets else None
```

Intersection áp dụng **chỉ** giữa các nhóm module đã kích hoạt; filter document core (`business_type`, `doc_group`, …) vẫn chạy song song như hiện tại.

**Enrich kết quả search (mục tiêu 3):** `_attach_dispatch_metadata()` / `_attach_decision_metadata()` mirror `_attach_contract_metadata()` — batch theo `document_id`, chỉ bản ghi active.

| Trường response (`SemanticSearchResult`) | Nguồn |
|------------------------------------------|-------|
| `dispatch_id`, `dispatch_type`, `dispatch_status` | `dispatch_records` |
| `decision_id`, `decision_kind`, `decision_status`, `effective_from`, `effective_to` | `decision_records` |

**Frontend (mục tiêu 4–5):** Mở rộng `SemanticSearchFilters`, `normalizeSearchPayload()`. UI conditional: nhóm dispatch khi `business_type` ∈ `{incoming_dispatch, outgoing_dispatch, ''}`; nhóm decision khi `business_type` ∈ `{decision, ''}`. Preset route query:

- `/dispatches` → `q`, `document_number`, `dispatch_type`, `dispatch_status`, `business_type` (map `incoming`→`incoming_dispatch`, `outgoing`→`outgoing_dispatch`)
- `/decisions` → `q`, `document_number`, `business_type=decision`, `decision_kind`, `decision_status`

Chi tiết draft: `docs/DOMAIN_MODULE_DECISION.md` mục **Thiết kế search filter dispatch/decision (draft)**.

### Mục tiêu 2 — Repository `list_document_ids_by_metadata` dispatch và decision (2026-06-07)

Kiểm tra bắt buộc:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile \
  apps/api/app/repositories/dispatch_repository.py \
  apps/api/app/repositories/decision_repository.py
git diff --check
```

Kết quả: `py_compile` pass; `git diff --check` pass.

Đã bổ sung:

- `DispatchRepository.list_document_ids_by_metadata(dispatch_type?, document_number?, issuing_agency?, status?)` — mirror `ContractRepository`, tái dùng `_conditions()` (active record + join `documents` active).
- `DecisionRepository.list_document_ids_by_metadata(decision_kind?, document_number?, issuing_agency?, status?, effective_from?, effective_to?)` — logic filter khớp list API module (`ilike` số/đơn vị, exact kind/status, range hiệu lực).
- Filter rỗng → không thêm điều kiện (caller quyết định kích hoạt pre-resolve ở `SearchService` mục tiêu 3).

### Mục tiêu 3 — SearchService, schema, router và smoke backend (2026-06-07)

Kiểm tra bắt buộc:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile \
  apps/api/app/schemas/search.py \
  apps/api/app/services/search_service.py \
  apps/api/app/services/rag_answer_service.py \
  apps/api/app/routers/search.py
docker compose exec -T api python -m app.scripts.smoke_dispatch_api
docker compose exec -T api python -m app.scripts.smoke_decision_api
docker compose exec -T api python -m app.scripts.smoke_search_module_filters
git diff --check
```

Kết quả: `py_compile` pass; `smoke_dispatch_api`, `smoke_decision_api`, `smoke_search_module_filters` pass; `git diff --check` pass.

Đã bổ sung:

- `SemanticSearchRequest` / `RagAnswerRequest`: `issuing_agency`, `dispatch_type`, `dispatch_status`, `decision_kind`, `decision_status`, `effective_from`, `effective_to`.
- `SemanticSearchResult`: enrich `dispatch_id`/`dispatch_type`/`dispatch_status`, `decision_id`/`decision_kind`/`decision_status`/`effective_from`/`effective_to`.
- `SearchService`: `_resolve_module_document_ids()` (intersection contract/dispatch/decision), `_resolve_dispatch_document_ids()`, `_resolve_decision_document_ids()`, `_attach_dispatch_metadata()`, `_attach_decision_metadata()`.
- `DocumentRepository`: filter `issuing_agency` trên chunk search post-filter.
- `DispatchRepository` / `DecisionRepository`: `map_active_by_document_ids()` cho enrich.
- Router `search.py` và `RagAnswerService` / `SearchBackend` protocol truyền đủ filter mới.
- Smoke `smoke_search_module_filters`: seed dispatch/decision + Qdrant, assert filter metadata và regression contract `supplier_name`; RAG `/search/answer` với filter decision.

### Mục tiêu 4 — Frontend dashboard filter và RAG (2026-06-07)

Kiểm tra bắt buộc:

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

Kết quả: client + server compile OK qua `docker compose run`; Nitro `EBUSY` khi `rmdir .output` (anonymous volume) — build production pass qua `docker compose build web` + `docker run ... npm run build`; `git diff --check` pass.

Đã bổ sung:

- `SemanticSearchFilters` / `SearchResult`: field dispatch/decision + `issuing_agency`; `normalizeSearchPayload()` map `dispatch_status`, `decision_status`, hiệu lực.
- `dashboard.vue`: filter `issuing_agency`; nhóm công văn (conditional `incoming_dispatch`/`outgoing_dispatch`/tất cả); nhóm quyết định (conditional `decision`/tất cả); hiển thị metadata module trên kết quả; filter hợp đồng giữ nguyên.
- `RagAnswerPanel` / `useRagAnswer`: dùng chung object `filters` từ dashboard; giữ `ragFilterChangedHint`.

### Mục tiêu 5 — Preset module pages, smoke end-to-end và hoàn tất Phase 11 (2026-06-07)

Kiểm tra bắt buộc:

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.smoke_search_module_filters
git diff --check
```

Kết quả:
- `docker compose run ... npm run build`: client + server compile OK; Nitro `EBUSY` trên volume — build pass qua `docker compose build web` + `docker run`.
- `smoke_rag_answer` pass; `smoke_search_module_filters` pass; `git diff --check` pass.

Đã bổ sung:

- `/dispatches`, `/decisions`: `dashboardSearchLink()` truyền filter module (`dispatch_type`, `dispatch_status`, `business_type`, `decision_kind`, `decision_status`, hiệu lực, `issuing_agency`).
- `dashboard.vue`: `applyRouteSearchPresets()` đọc route query khi mount; auto search nếu có `q`.
- `docs/DOMAIN_MODULE_DECISION.md`: mục **Search filter đã triển khai**.
- `ROADMAP.md` Phase 11 hoàn thành; `TASK_NEXT.md` thay bằng checklist Phase 12.

**Phase 11 hoàn thành ngày 2026-06-07.**

---

## Phase 12 — RAG Citation UX Và Search Enrichment

### Mục tiêu 1 — Thiết kế anchor/scroll chunk trên document detail (2026-06-07)

Kiểm tra bắt buộc:

```bash
git diff --check
```

Kết quả: pass.

#### Khảo sát hiện trạng

| Thành phần | Hành vi hiện tại |
|------------|------------------|
| Route | `pages/documents/[...id].vue`; `documentId` từ `route.params.id` (join nếu array). Hash client-side qua `route.hash` (Nuxt 3 SPA). |
| Load lifecycle | `onMounted` + `watch(documentId)` gọi `fetchDocument()`; chunks có sau API trả về. Có polling khi status OCR (`shouldPoll`). |
| Chunk list DOM | Card **Chunks** ở cuối trang (sau metadata module, source files, OCR jobs, audit, OCR text). `<article v-for="chunk in filteredChunks">` — **chưa có** `id` DOM. |
| Chunk filter | `chunkFilter` ∈ `{all, review, appendix, appendix_review}` — chunk target có thể **bị ẩn** nếu filter không khớp. |
| Chunk identity | `DocumentChunk.id` (UUID string) — trùng `SearchResult.chunk_id`, `RagCitation.chunk_id` từ API search/RAG. |
| Link hiện tại | `RagAnswerPanel`, `dashboard.vue` search results: `/documents/{document_id}` **không** có hash chunk. |
| Layout scroll | Nav không sticky; `scrollIntoView` đủ, thêm `scroll-margin-top: 1rem` trên anchor để tránh sát mép viewport. |

#### Quyết định thiết kế (draft triển khai mục tiêu 2–4)

**Hash contract**

```text
/documents/{document_id}#chunk-{chunk_id}
```

- Prefix cố định: `#chunk-`.
- `{chunk_id}`: full UUID từ API (`chunk.id` / `chunk_id`); parser: `route.hash.startsWith('#chunk-')` → slice(7) hoặc regex `^#chunk-(.+)$`.
- Hash không hợp lệ / rỗng → bỏ qua, không throw.

**DOM anchor**

```html
<article :id="`chunk-${chunk.id}`" ...>
```

- Selector runtime: `document.getElementById('chunk-' + chunkId)`.
- Chỉ gắn trên chunk card trong list (không đổi backend).

**Luồng focus chunk (`focusChunkFromHash`)**

1. Parse `chunkId` từ `route.hash`.
2. Nếu `chunkId` không nằm trong `allChunks` → **fallback**: không scroll; set flag `chunkAnchorMiss=true` (hiển thị Message nhẹ trong card Chunks: "Không tìm thấy đoạn đã liên kết").
3. Nếu chunk có trong `allChunks` nhưng không trong `filteredChunks` → **reset** `chunkFilter = 'all'`, `await nextTick()`, rồi scroll.
4. `element.scrollIntoView({ block: 'start', behavior: 'auto' })` — không animation phức tạp.
5. Set `highlightedChunkId = chunkId`; clear sau **2500ms** (`setTimeout`, cleanup `onBeforeUnmount`).

**Highlight class (Tailwind trên `<article>`)**

```text
ring-2 ring-sky-400 ring-offset-2 bg-sky-50/50 rounded-md scroll-mt-4
```

- Bind khi `highlightedChunkId === chunk.id`.
- Không transition/animation dài.

**Điểm kích hoạt**

| Sự kiện | Hành động |
|---------|-----------|
| Sau `fetchDocument` xong (onMounted / đổi `documentId`) | Gọi `focusChunkFromHash()` nếu có hash |
| `watch(() => route.hash)` | Hash đổi trong cùng page → focus lại |
| `watch(allChunks)` khi có hash và lần trước miss | Retry focus (polling/reprocess làm chunks xuất hiện sau) |

**Tổ chức code (mục tiêu 2)**

- Composable `useDocumentChunkAnchor()` tại `apps/web/composables/useDocumentChunkAnchor.ts`:
  - Input: `allChunks`, `chunkFilter` (writable ref), `route`.
  - Output: `highlightedChunkId`, `chunkAnchorMiss`, `focusChunkFromHash()`.
- Page `documents/[...id].vue` gọi composable; **không** gọi API trong composable (giữ `page -> composable`).

**Link helper (mục tiêu 3–4)**

```typescript
// apps/web/utils/documentLinks.ts
buildDocumentChunkUrl(documentId: string, chunkId?: string | null): string
```

- Có `chunkId` → `/documents/{id}#chunk-{chunkId}`.
- Không có → `/documents/{id}` (fallback an toàn citation khi thiếu id).

**RAG citation & search result (mục tiêu 3–4)**

- `RagAnswerPanel`: `NuxtLink` title + "Mở văn bản" dùng `buildDocumentChunkUrl(citation.document_id, citation.chunk_id)`.
- `dashboard.vue`: nút "Mở đoạn" (mục tiêu 4) cùng helper; title link giữ document root hoặc cùng deep link — ưu tiên deep link khi có `chunk_id`.

**Không làm**

- Không scroll PDF viewer theo page.
- Không đổi chunking/OCR/backend.
- Không hash query param thay `#` (giữ browser-native anchor).

**Manual/smoke checklist (mục tiêu 2+)**

1. Lấy `document_id` + `chunk_id` từ `smoke_rag_answer` citation.
2. Mở `/documents/{id}#chunk-{chunk_id}` → scroll tới đúng article, highlight ~2.5s.
3. Đổi filter Chunks sang "Cần review" rồi mở lại URL chunk không thuộc filter → auto reset "Tất cả" và scroll đúng.
4. Hash chunk UUID không tồn tại → message miss, không crash.

### Mục tiêu 2 — Implement `#chunk-{id}` document detail + highlight (2026-06-07)

Kiểm tra bắt buộc:

```bash
docker compose build web && docker run --rm --memory=4g -e NODE_OPTIONS=--max-old-space-size=3072 app-qlvb-phongvattu-web:latest npm run build
git diff --check
```

Kết quả: frontend build pass; `git diff --check` pass.

**Đã triển khai**

- `apps/web/composables/useDocumentChunkAnchor.ts`: `parseChunkIdFromHash`, `chunkDomId`, `useDocumentChunkAnchor` — parse `#chunk-{uuid}`, reset filter `all` khi chunk bị ẩn, `scrollIntoView`, highlight 2500ms, watch `route.hash` và `allChunks` retry khi miss/polling.
- `apps/web/utils/documentLinks.ts`: `buildDocumentChunkUrl` (dùng ở mục tiêu 3–4).
- `apps/web/pages/documents/[...id].vue`: gắn `id="chunk-{id}"`, class highlight `ring-2 ring-sky-400 ring-offset-2 bg-sky-50/50 scroll-mt-4`, `Message` khi `chunkAnchorMiss`, gọi `focusChunkFromHash()` sau fetch và khi đổi `documentId`.

**Manual checklist (chưa smoke tự động)**

- Mở `/documents/{id}#chunk-{chunk_id}` với fixture smoke → scroll + highlight theo spec mục tiêu 1.
- Filter Chunks khác `all` + hash chunk ngoài filter → auto reset và scroll.
- Hash chunk không tồn tại → warning, không crash.

### Mục tiêu 3 — Cập nhật RAG citation URL và panel (2026-06-07)

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose build web && docker run --rm --memory=4g -e NODE_OPTIONS=--max-old-space-size=3072 app-qlvb-phongvattu-web:latest npm run build
git diff --check
```

Kết quả: smoke RAG pass (3 citations, `citation_deep_links` chứa `#chunk-`); frontend build pass; `git diff --check` pass.

**Đã triển khai**

- `RagAnswerPanel.vue`: title link và "Mở văn bản" dùng `buildDocumentChunkUrl(document_id, chunk_id)` → `/documents/{id}#chunk-{chunk_id}`; fallback về `/documents/{id}` khi thiếu `chunk_id`.
- `smoke_rag_answer.py`: assert deep link format, trả `citation_deep_links` trong output để manual UI checklist.

### Mục tiêu 4 — Search result badges và nút "Mở đoạn" (2026-06-07)

Kiểm tra bắt buộc:

```bash
docker compose build web && docker run --rm --memory=4g -e NODE_OPTIONS=--max-old-space-size=3072 app-qlvb-phongvattu-web:latest npm run build
git diff --check
```

Kết quả: frontend build pass; `git diff --check` pass.

**Đã triển khai**

- `dashboard.vue` kết quả semantic search: title và nút "Mở đoạn" dùng `buildDocumentChunkUrl(document_id, chunk_id)`; badge `Tag` HĐ/công văn/quyết định khi có metadata module enrich.

### Mục tiêu 5 — Smoke regression, tinh chỉnh extractive và hoàn tất phase (2026-06-07)

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.smoke_search_module_filters
docker compose exec -T api python -m app.scripts.smoke_api_workflows
docker compose build web && docker run --rm --memory=4g -e NODE_OPTIONS=--max-old-space-size=3072 app-qlvb-phongvattu-web:latest npm run build
git diff --check
```

Kết quả: cả 3 smoke pass; frontend build pass; `git diff --check` pass.

**Tinh chỉnh extractive (tùy chọn)**

- `RagAnswerService._compose_answer`: ghép tối đa 2 citation quote đầu (đã xếp theo score) thay vì toàn bộ danh sách — câu trả lời ngắn hơn, vẫn grounded.

**Đóng phase**

- `ROADMAP.md` Phase 12 hoàn thành; `TASK_NEXT.md` thay bằng checklist Phase 13.

**Phase 12 hoàn thành ngày 2026-06-07.**

---

## Phase 13 — Module Đề Xuất / Kế Hoạch Mua Sắm MVP

### Mục tiêu 1 — Thiết kế module procurement trong DOMAIN_MODULE_DECISION.md (2026-06-07)

Kiểm tra bắt buộc:

```bash
git diff --check
```

Kết quả: pass.

**Khảo sát pattern module hiện có**

| Module | Bảng | API | Route | Quan hệ document |
|--------|------|-----|-------|------------------|
| Hợp đồng | `contract_records` | `/api/v1/contracts` | `/contracts` | 1-1 partial unique `document_id` |
| Công văn | `dispatch_records` | `/api/v1/dispatches` | `/dispatches` | 1-1 |
| Quyết định | `decision_records` | `/api/v1/decisions` | `/decisions` | 1-1 |

Catalog `business_type` hiện có: `incoming_dispatch`, `outgoing_dispatch`, `contract`, `decision` (migration `0012_admin_catalogs`). Benchmark fixture `procurement_plan` tạm dùng `business_type=incoming_dispatch` — sẽ chuẩn hóa `procurement` khi có seed catalog.

**Quyết định thiết kế (ghi trong `docs/DOMAIN_MODULE_DECISION.md`)**

- Module thứ tư: `procurement_records`, API `/api/v1/procurements`, route `/procurements`, audit `procurement`.
- `procurement_kind`: `proposal` | `plan` | `acceptance` (≤3 giá trị MVP).
- `business_type=procurement` (một mã catalog; phân biệt bằng `procurement_kind` — giống `decision` + `decision_kind`).
- Metadata: `reference_number`, `title_summary`, `requesting_unit`, `estimated_value`, `currency` (default VND), `requested_date`, `status`, `notes`.
- Status: `draft`, `submitted`, `approved`, `rejected`, `completed`, `archived` — PATCH trực tiếp, không rule engine.
- Quyền/audit giống module trước; search filter procurement draft cho mục tiêu 6 tùy chọn.

### Mục tiêu 2 — Migration và model procurement_records (2026-06-07)

Kiểm tra bắt buộc:

```bash
docker compose exec -T api alembic upgrade head
git diff --check
```

Kết quả: `alembic current` = `0015_procurement_records (head)`; `git diff --check` pass.

**Đã triển khai**

- Migration `0015_procurement_records`: bảng `procurement_records` với cột theo thiết kế mục tiêu 1; partial unique `ux_procurement_records_document_active`; index filter `procurement_kind`, `reference_number`, `requesting_unit`, `status`, `requested_date`.
- Seed catalog `business_type=procurement` (nhãn "Đề xuất / kế hoạch mua sắm", `sort_order=50`).
- Model `ProcurementRecord` tại `apps/api/app/models/procurement.py`; quan hệ `Document.procurement_record` 1-1.

### Mục tiêu 3 — API CRUD và smoke backend procurement (2026-06-07)

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_procurement_api
git diff --check
```

Kết quả: smoke procurement API pass (create/list/filter/update/soft-delete, audit, 403 user delete); `git diff --check` pass.

**Đã triển khai**

- `ProcurementRepository`, `ProcurementService`, router `/api/v1/procurements` + `by-document/{document_id}`.
- Schemas `procurement.py`; audit `procurement.created|updated|deleted`; RBAC giống module trước.
- `list_document_ids_by_metadata` sẵn sàng cho search filter mục tiêu 6.
- Smoke: `python -m app.scripts.smoke_procurement_api`.

### Mục tiêu 4 — Frontend `/procurements` (2026-06-07)

Kiểm tra bắt buộc:

```bash
docker compose build web && docker run --rm --memory=4g -e NODE_OPTIONS=--max-old-space-size=3072 app-qlvb-phongvattu-web:latest npm run build
git diff --check
```

Kết quả: frontend build pass; `git diff --check` pass.

**Đã triển khai**

- `types/procurement.ts`, `procurement.service.ts`, `useProcurements.ts`, page `/procurements` (list/filter/form CRUD, pagination).
- Nav `Mua sắm` trong app shell; preset search dashboard `business_type=procurement`.
- Query `document_id` / `create=1` sẵn sàng cho liên kết document detail mục tiêu 5.

### Mục tiêu 5 — Liên kết document detail hai chiều (2026-06-07)

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_procurement_api
docker compose build web && docker run --rm --memory=4g -e NODE_OPTIONS=--max-old-space-size=3072 app-qlvb-phongvattu-web:latest npm run build
git diff --check
```

Kết quả: smoke procurement API pass; frontend build pass; `git diff --check` pass.

**Đã triển khai**

- `documents/[...id].vue`: card **Mua sắm** — hiển thị metadata procurement, nút "Mở Mua sắm", "Search trong văn bản", "Tạo metadata mua sắm" khi chưa có; fetch `by-document` on mount/đổi `documentId`.
- `/procurements` → document detail (link cột Document) và preset dashboard `business_type=procurement` (đã có mục tiêu 4).

### Mục tiêu 6 — Search filter procurement và hoàn tất Phase 13 (2026-06-07)

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_procurement_api
docker compose exec -T api python -m app.scripts.smoke_search_module_filters
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.smoke_api_workflows
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

**Đã triển khai**

- Backend: `SearchService` pre-resolve `document_id` từ `ProcurementRepository.list_document_ids_by_metadata`; enrich `procurement_id`, `procurement_kind`, `procurement_status`, `reference_number`, `requesting_unit`; router search/answer + `RagAnswerService` params.
- Schemas `search.py`: `ProcurementKind`, `ProcurementStatus`, filter và result fields.
- Smoke `smoke_search_module_filters.py`: seed procurement + semantic/RAG filter regression.
- Benchmark fixture `procurement_plan`: `business_type=procurement`.
- Frontend: `SemanticSearchFilters` + dashboard filter UI (`showProcurementFilters`), badges; preset từ `/procurements` và document detail card.
- `DOMAIN_MODULE_DECISION.md`: search filter procurement chuyển draft → đã triển khai.
- Phase 13 đóng.

Kết quả: smoke procurement API, search module filters (gồm procurement), RAG answer, API workflows pass; frontend build pass qua `docker compose build web && docker run ... npm run build` (compose volume EBUSY trên `.output`); `git diff --check` pass.

## Phase 14 — Gợi Ý Metadata Module Và Onboarding Sau OCR

Trạng thái: hoàn thành (2026-06-07).

Mục tiêu phase: nối classifier OCR rule-based với 4 module nghiệp vụ — gợi ý `business_type`, loại module và pre-fill form tạo metadata; không auto-create module record im lặng.

### Mục tiêu 1 — Thiết kế mapping classifier → business_type/module (2026-06-07)

Kiểm tra bắt buộc:

```bash
git diff --check
```

Kết quả: `git diff --check` pass.

**Đã ghi trong `docs/DOMAIN_MODULE_DECISION.md` (mục Module Onboarding Sau OCR)**

- Bảng mapping `document_type` → `target_module` + `business_type` + sub-kind (`dispatch_type`, `decision_kind`, `procurement_kind`).
- Heuristic `CV`/`CĐ` incoming vs outgoing; ngưỡng confidence high/medium/low (0.85 / 0.70).
- Guard manual review (`metadata_reviewed_at`, `metadata_source` manual/mixed); upload đã chọn `business_type` không bị worker đổi.
- Map field classifier/document → form từng module; shape API `OnboardingSuggestionResponse`.
- Worker audit-only mặc định (`document.onboarding_suggested`); filter list `missing_module_metadata`.

### Khảo sát / bối cảnh (trước mục tiêu 1)

| Hạng mục | Hiện trạng |
|----------|------------|
| Worker OCR | `DocumentClassifierService.classify()` trích `document_type`, số văn bản, cơ quan, trích yếu, người nhận, v.v.; lưu qua `update_metadata()` |
| `business_type` | Worker **giữ nguyên** giá trị từ upload (`ocr_worker.py`); không gợi ý từ classifier |
| Manual review guard | Không ghi đè khi `metadata_reviewed_at` hoặc `metadata_source` ∈ `{manual, mixed}` |
| Module UI | Document detail có card từng module; form pre-fill một phần từ metadata document; **chưa** có banner/CTA gợi ý thống nhất |
| Classifier tests | `check_document_classifier.py` và unit tests classifier đã có |
| API onboarding | Chưa có `GET /documents/{id}/onboarding-suggestions` |
| Document list | Chưa có filter/badge “thiếu metadata module” |

Phạm vi đã chốt trong `ROADMAP.md`: mapping `document_type` → `business_type` + module target; API read-only gợi ý; UI document detail + list filter; smoke `smoke_module_onboarding`; không LLM, không `document_relations`, không inventory.

Checklist thực thi: `TASK_NEXT.md`.

### Mục tiêu 2 — ModuleOnboardingService và API onboarding-suggestions (2026-06-07)

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.check_document_classifier
docker compose exec -T api python -m unittest app.services.tests.test_module_onboarding_service
git diff --check
```

Kết quả: classifier check pass; 9 unit tests pass; `git diff --check` pass.

**Đã triển khai**

- `ModuleOnboardingService`: mapping `document_type` → module, heuristic CV incoming/outgoing, pre-fill fields, guard manual review / not searchable / module exists / low confidence.
- Schema `OnboardingSuggestionResponse`; `GET /api/v1/documents/{document_id}/onboarding-suggestions`.
- Unit tests `test_module_onboarding_service.py` (contract, decision, dispatch, guards).

### Mục tiêu 3 — Worker/audit gợi ý business_type có kiểm soát (2026-06-07)

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_api_workflows
docker compose exec -T api python -m unittest app.services.tests.test_module_onboarding_service
git diff --check
```

Kết quả: smoke API workflows pass; 12 unit tests pass; `git diff --check` pass.

**Đã triển khai**

- Worker `_extract_and_store_metadata`: sau auto-extract, audit `document.onboarding_suggested` khi upload **chưa** chọn `business_type`; **không** auto-apply `business_type` (audit-only).
- `build_worker_onboarding_audit_metadata()` + `require_searchable=False` cho ngữ cảnh worker (document chưa searchable).
- Bỏ qua audit onboarding khi user đã chọn `business_type` lúc upload hoặc metadata manual/mixed.

### Mục tiêu 4 — Document detail banner gợi ý và CTA tạo metadata (2026-06-07)

Kiểm tra bắt buộc:

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

Kết quả: client + server compile OK; Nitro `EBUSY` khi `rmdir .output` (anonymous volume compose) — build production pass qua `docker compose build web` + `docker run --rm --memory=4g ... npm run build`; `git diff --check` pass.

**Đã triển khai**

- Types `onboarding.ts`; `document.service.getOnboardingSuggestions()`; composable `useDocumentOnboarding`.
- `DocumentOnboardingBanner.vue` trên `/documents/[id]`: hiện khi searchable, có `target_module`, chưa có module active; low-confidence hiển thị cảnh báo, không chặn workflow.
- Nút **Áp dụng loại nghiệp vụ** (PATCH metadata `business_type`); nút **Tạo metadata {module}** deep link `?document_id=&create=1` + query pre-fill.
- `utils/moduleOnboarding.ts`: `buildModuleCreateLink`, `applyRoutePrefill`; 4 trang module hydrate form từ query khi `create=1`.

### Mục tiêu 5 — Document list badge/filter thiếu metadata module (2026-06-07)

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_api_workflows
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

Kết quả: smoke API workflows pass; `smoke_documents_pagination` assert filter `missing_module_metadata`; 13 unit tests pass; web build pass qua `docker compose build web` + `docker run` (EBUSY `.output`); `git diff --check` pass.

**Đã triển khai**

- API list documents: query `missing_module_metadata=true`; response `DocumentListItemRead.missing_module_metadata`.
- Repository SQL filter: `searchable` + `business_type` module catalog + không có bản ghi active tương ứng.
- `batch_missing_module_metadata_flags()` enrich flag trên mọi trang list.
- Frontend `/documents`: filter “Chưa có metadata module”; `BaseDataTable` badge warn.

### Mục tiêu 6 — Smoke onboarding và đóng phase (2026-06-07)

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_module_onboarding
docker compose exec -T api python -m app.scripts.smoke_api_workflows
docker compose exec -T api python -m app.scripts.smoke_procurement_api
docker compose exec -T api python -m app.scripts.smoke_search_module_filters
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.check_document_classifier
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

Kết quả: tất cả smoke/regression pass; web build pass qua `docker compose build web` + `docker run`; `git diff --check` pass.

**Đã triển khai**

- `smoke_module_onboarding.py`: 5 fixture (`HĐ`, `CV` incoming/outgoing, `QĐ`, `KH`) → onboarding-suggestions → PATCH `business_type` → filter `missing_module_metadata` → POST module pre-fill → verify by-document + filter sau tạo.
- Phase 14 đóng; `ROADMAP.md` và `TASK_NEXT.md` cập nhật (chưa lập Phase 15).

## Phase 15 — Liên Kết Chéo Document (`document_relations`)

Trạng thái: **hoàn thành** (2026-06-07).

Mục tiêu phase: quan hệ có hướng giữa hai document độc lập; tra cứu incoming/outgoing từ document detail; tạo/xóa thủ công.

### Khảo sát / bối cảnh (trước mục tiêu 2)

| Hạng mục | Hiện trạng |
|----------|------------|
| Nhiều tệp một document | `document_files` + reorder — cùng văn bản nguồn |
| Phụ lục trong document | Chunk `section_role=appendix`, review queue filter |
| Liên kết chéo document | **Chưa có** bảng/API `document_relations` |
| Document detail | Card module 4 loại + onboarding banner; **chưa** card văn bản liên quan |
| OCR/worker | Không trích quan hệ chéo document |

Phạm vi đã chốt trong `ROADMAP.md` và `docs/DOMAIN_MODULE_DECISION.md` (mục Document Relations): bảng `document_relations`, 4 `relation_type`, API GET/POST/DELETE, UI card detail, smoke `smoke_document_relations`; không LLM auto-link, không Qdrant re-index.

Checklist thực thi: `TASK_NEXT.md` (mục tiêu 6 đóng phase).

### Mục tiêu 1 — Thiết kế `document_relations` (2026-06-07)

Kiểm tra bắt buộc:

```bash
git diff --check
```

Kết quả: `git diff --check` pass (khi lập phase).

**Đã ghi trong `docs/DOMAIN_MODULE_DECISION.md`**

- Schema `document_relations`, catalog `relation_type`, ràng buộc unique/self-link.
- API shape incoming/outgoing; UX card document detail; phân biệt chunk appendix.
- Smoke plan `smoke_document_relations`; hướng dẫn mục tiêu 2–6.

### Mục tiêu 2 — Migration, model và repository (2026-06-07)

Kiểm tra bắt buộc:

```bash
docker compose exec -T api alembic upgrade head
docker compose exec -T api python -m app.scripts.smoke_document_relations_repo
git diff --check
```

Kết quả: migration `0016_document_relations` pass; `smoke_document_relations_repo` pass; `git diff --check` pass.

**Đã triển khai**

- Alembic `0016_document_relations`: bảng `document_relations`, check constraint no self-link, partial unique active `(source, target, relation_type)`, index source/target/type.
- Model `DocumentRelation` + `RELATION_TYPES`; relationship trên `Document` (outgoing/incoming).
- `DocumentRelationRepository`: list outgoing/incoming, find_active, create (guard self-link + relation_type), soft_delete, count_active_for_document.
- Smoke repo `smoke_document_relations_repo.py`: tạo/đọc/xóa + guard self-link.

### Mục tiêu 3 — DocumentRelationService, API và smoke backend (2026-06-07)

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_document_relations
docker compose exec -T api python -m app.scripts.smoke_api_workflows
git diff --check
```

Kết quả: `smoke_document_relations` pass; `smoke_api_workflows` regression pass; `git diff --check` pass.

**Đã triển khai**

- `DocumentRelationService`: list/create/delete, audit `document_relation.created/deleted`, RBAC xóa creator hoặc admin.
- API `GET/POST /documents/{id}/relations`, `DELETE /document-relations/{id}`.
- Schemas `document_relation.py`; router `document_relations.py`.
- Smoke `smoke_document_relations.py`: tạo B→A `references`, outgoing/incoming, 409 trùng, 403 non-creator, xóa + audit.

### Mục tiêu 4 — Frontend card liên kết document detail (2026-06-07)

Kiểm tra bắt buộc:

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

Kết quả: client + SSR compile pass; Nitro bước cuối `EBUSY rmdir .output` do bind mount Docker (không lỗi TypeScript); `git diff --check` pass.

**Đã triển khai**

- `types/document-relation.ts`, `services/document-relation.service.ts`, `composables/useDocumentRelations.ts`.
- `components/documents/DocumentRelationsCard.vue`: card **Văn bản liên quan**, liên kết đi/đến, form thêm (tìm + chọn document, loại, ghi chú), xóa có confirm.
- Tích hợp `/documents/[id]`: card dưới onboarding banner, trên card module; link mở document đích ≤3 thao tác (tìm/chọn → thêm → click link).

### Mục tiêu 5 — Document list badge/filter liên kết (2026-06-07)

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_documents_pagination
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

Kết quả: `smoke_documents_pagination` pass (has_relations + relation_count); web build pass; `git diff --check` pass.

**Đã triển khai**

- List API: `relation_count` trên `DocumentListItemRead`, filter `has_relations=true`.
- Repository/service: batch count relations, exists filter; không regression pagination.
- Frontend `/documents`: filter **Có liên kết văn bản**, badge **N liên kết** trên `BaseDataTable`.

### Mục tiêu 6 — Smoke end-to-end và đóng Phase 15 (2026-06-07)

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_document_relations
docker compose exec -T api python -m app.scripts.smoke_module_onboarding
docker compose exec -T api python -m app.scripts.smoke_api_workflows
docker compose exec -T api python -m app.scripts.smoke_search_module_filters
docker compose exec -T api python -m app.scripts.smoke_rag_answer
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

Kết quả: tất cả smoke API pass; web client + SSR compile pass (Nitro `EBUSY rmdir .output` do bind mount Docker); `git diff --check` pass.

**Đóng phase**

- Tiêu chí hoàn thành Phase 15 trong `ROADMAP.md` đạt.
- Phase 15 đóng; `ROADMAP.md` và `TASK_NEXT.md` cập nhật (chưa lập Phase 16).

## Phase 16 — Gợi Ý Liên Kết Document Từ Nội Dung (Rule-Based)

Trạng thái: hoàn thành (2026-06-07).

**Khảo sát mã nguồn**

- `DocumentClassifierService._extract_document_number_and_symbol()`: regex `\bSố\s*:\s*([^\n]+)`, tách symbol sau `/`, cắt phần date/place — dùng làm mirror cho pattern phụ và `normalize_document_number`.
- `ocr_chunking/anchors.py`: `GROUP_B_ANCHORS` chứa `Căn cứ`, `V/v`, `Thực hiện` — phù hợp chunk công văn tham chiếu QĐ; `APPENDIX_RE` đã có cho phụ lục trong cùng document (khác `document_relations` cross-document).
- `DocumentRepository.list_chunks_for_document`: đủ để lọc trang 1–2 và `section_role`; lookup `document_number` hiện exact match (`==`) trong filter chunk search.
- Phase 15: `RELATION_TYPES` = `references`, `appendix_of`, `implements`, `related`; unique triple active; smoke seed QĐ `01/QD-REL-{suffix}` + CV `01/CV-REL-{suffix}` — fixture Phase 16 mở rộng CV chunk text chứa số QĐ.

**Kết quả thiết kế**

- Ghi mục **Relation Suggestions** trong `docs/DOMAIN_MODULE_DECISION.md`: regex 3 tầng, anchor → `relation_type`, normalize số văn bản, DTO `RelationSuggestionRead` / `RelationSuggestionsResponse`, ngưỡng `high` (≥0.80) / `review` (≥0.50), loại trừ self-link / triple trùng / target không searchable.

**Kiểm tra**

```bash
git diff --check
```

Kết quả: pass.

### Mục tiêu 2 — DocumentRelationSuggestionService và lookup document (2026-06-07)

**Triển khai**

- `app/utils/document_number.py`: `normalize_document_number`, `infer_document_type_from_symbol` (mirror classifier, fix OCR `QD`→`QĐ`).
- `DocumentRepository.find_searchable_by_document_number()`: so khớp hai phía sau normalize.
- `DocumentRelationSuggestionService.suggest_relations()`: lọc chunk trang 1–2, trích reference, anchor→`relation_type`, confidence/dedupe/cap 8, loại trừ self-link và triple active.

**Kiểm tra**

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile \
  apps/api/app/services/document_relation_suggestion_service.py
docker compose exec -T api python -m unittest app.services.tests.test_document_relation_suggestion_service -v
docker compose exec -T api python -m app.scripts.smoke_document_relation_suggestions_repo
git diff --check
```

Kết quả: 7 unit tests pass; smoke repo CV→QĐ `references` pass; `git diff --check` pass.

### Mục tiêu 3 — API `relation-suggestions` và schema response (2026-06-07)

**Triển khai**

- Schema `RelationSuggestionRead`, `RelationSuggestionsResponse` trong `document_relation.py`.
- `GET /api/v1/documents/{document_id}/relation-suggestions` trên router documents; auth user; `404` khi document không tồn tại hoặc chưa searchable; read-only, không tạo relation.

**Kiểm tra**

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile \
  apps/api/app/schemas/document_relation.py apps/api/app/routers/documents.py
docker compose exec -T api python -m app.scripts.smoke_document_relations
git diff --check
```

Kết quả: py_compile pass; regression `smoke_document_relations` pass; `git diff --check` pass.

### Mục tiêu 4 — Frontend gợi ý trong DocumentRelationsCard (2026-06-07)

**Triển khai**

- Types `RelationSuggestion`, `RelationSuggestionsResponse` trong `document-relation.ts`.
- `document-relation.service.getRelationSuggestions()`; composable `useDocumentRelationSuggestions`.
- Subsection **Gợi ý liên kết** trong `DocumentRelationsCard`: nhãn quan hệ, document đích, trích đoạn chunk; style `high` (sky) vs `review` (amber + badge).
- Document detail load gợi ý khi `searchable`; form thêm liên kết thủ công giữ nguyên.

**Kiểm tra**

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

Kết quả: client + SSR compile pass; Nitro `EBUSY rmdir .output` do bind mount Docker; `git diff --check` pass.

### Mục tiêu 5 — Apply/dismiss UX và refresh relations (2026-06-07)

**Triển khai**

- Nút **Tạo liên kết** trên mỗi gợi ý → `createRelation` (POST relations); sau thành công refresh relations + gợi ý, ẩn gợi ý đã dùng.
- Nút **Bỏ qua** → dismiss client-side (`Set` key `target_document_id:relation_type`); không gọi API.
- Lỗi 409 hiển thị qua `relationsError` (“Liên kết này đã tồn tại”).

**Kiểm tra**

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

Kết quả: client + SSR compile pass; Nitro `EBUSY rmdir .output` do bind mount Docker; `git diff --check` pass.

### Mục tiêu 6 — Smoke end-to-end, regression và hoàn tất phase (2026-06-07)

**Triển khai**

- Script `app/scripts/smoke_relation_suggestions.py`: seed QĐ + CV (CV chunk chứa số QĐ) → GET suggestions → POST relation → assert gợi ý biến mất và outgoing có 1.

**Kiểm tra**

```bash
docker compose exec -T api python -m app.scripts.smoke_relation_suggestions
docker compose exec -T api python -m app.scripts.smoke_document_relations
docker compose exec -T api python -m app.scripts.smoke_module_onboarding
docker compose exec -T api python -m app.scripts.smoke_search_module_filters
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.check_document_classifier
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

Kết quả: tất cả smoke API pass; web client + SSR compile pass; `git diff --check` pass.

**Đóng phase**

- Tiêu chí hoàn thành Phase 16 trong `ROADMAP.md` đạt.
- Phase 16 đóng; `ROADMAP.md` và `TASK_NEXT.md` cập nhật (Phase 17 chưa lập checklist).

## Phase 17 — RAG Generative Local LLM (Ollama On-Prem)

Trạng thái: **hoàn thành** (2026-06-07).

### Mục tiêu 1 — Thiết kế generative RAG, prompt và env contract (2026-06-07)

**Khảo sát mã nguồn**

- `RagAnswerService`: retrieval qua `SearchService`, evidence filter `min_score` + query overlap; extractive `_compose_answer()` nối top 2 quote; `fallback_reason=insufficient_evidence` khi thiếu căn cứ.
- Schema `RagAnswerResponse`: `query`, `answer`, `grounded`, `confidence`, `fallback_reason`, `citations[]`; `RagCitation` có `chunk_id`, metadata document/chunk — chưa có `generation_mode`.
- Router `POST /search/answer` thin — delegate `RagAnswerService(db).answer()`.
- Frontend: `useRagAnswer`, `RagAnswerPanel` — xử lý `insufficient_evidence`; chưa có UI `llm_unavailable` / generative badge.
- `/health/ready`: postgres/redis/qdrant/uploads — không có hook LLM (phù hợp thiết kế).

**Kết quả thiết kế**

- Ghi mục **RAG Generative (Phase 17)** trong `docs/DOMAIN_MODULE_DECISION.md`: Ollama, luồng retrieval → context → LLM → validator → fallback; prompt system/user; `CitationValidator`; env contract; default `extractive`; worker không gọi LLM.

**Kiểm tra**

```bash
git diff --check
```

Kết quả: pass.

### Mục tiêu 2 — LocalLLMService và settings (2026-06-07)

**Triển khai**

- Settings `config.py`: `rag_generation_backend`, `ollama_base_url`, `rag_llm_model`, timeout, max context/output tokens, temperature; validator backend `extractive|ollama`.
- `LocalLLMService`: `is_generative_enabled()`, `is_available()` (GET `/api/tags`), `generate(system, user)` (POST `/api/chat`); exception có cấu trúc; backend `extractive` không gọi HTTP.

**Kiểm tra**

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile \
  apps/api/app/services/local_llm_service.py apps/api/app/core/config.py
docker compose exec -T api python -m unittest app.services.tests.test_local_llm_service -v
git diff --check
```

Kết quả: py_compile pass; 6 unit tests pass; `git diff --check` pass.

### Mục tiêu 3 — Docker Compose profile `llm` và Ollama service (2026-06-07)

**Triển khai**

- Service `ollama` (`ollama/ollama`), `profiles: [llm]`, volume `ollama_data`, healthcheck `ollama list`, limits `OLLAMA_CPU_LIMIT` / `OLLAMA_MEMORY_LIMIT`.
- `api` nhận env RAG/LLM; **không** `depends_on` ollama — readiness api không phụ thuộc LLM.
- `docker-compose.llm-gpu.yml` override NVIDIA (tùy chọn).
- Cập nhật `.env.example`, `docs/COMPOSE_RESOURCE_UPLOAD_RUNBOOK.md`.

**Kiểm tra**

```bash
docker compose config
docker compose --profile llm config
git diff --check
```

Kết quả: config pass; profile `llm` render service ollama + volume; `git diff --check` pass.

### Mục tiêu 4 — RagAnswerService generative, context builder và fallback (2026-06-07)

**Triển khai**

- `RagContextBuilder`: format context numbered `[1]..[n]`, cap `RAG_LLM_MAX_CONTEXT_CHARS`, ưu tiên chunk không `requires_review`.
- `CitationValidator`: parse marker `[n]`, whitelist chunk index, phát hiện câu insufficient.
- `RagAnswerService`: nhánh generative qua `LocalLLMService`; fallback extractive với `llm_unavailable` / `validation_failed`; response thêm `generation_mode`, `model_name`, `latency_ms`.

**Kiểm tra**

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile \
  apps/api/app/services/rag_answer_service.py apps/api/app/services/rag_context_builder.py
docker compose exec -T api python -m unittest app.services.tests.test_rag_answer_service -v
docker compose exec -T api python -m app.scripts.smoke_rag_answer
git diff --check
```

Kết quả: 7 unit tests pass; smoke `smoke_rag_answer` pass; `git diff --check` pass.

### Mục tiêu 5 — API schema, router và ops LLM status (2026-06-07)

**Triển khai**

- `RagAnswerResponse`: `generation_mode`, `model_name`, `latency_ms`; `fallback_reason` typed (`insufficient_evidence`, `llm_unavailable`, `validation_failed`).
- `SystemStatusRead.llm` + `OpsService._get_llm_status()` (backend, model, reachable, model_loaded).
- `LocalLLMService.is_model_loaded()`; smoke health kiểm tra component `llm`.

**Kiểm tra**

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile \
  apps/api/app/schemas/search.py apps/api/app/routers/search.py apps/api/app/services/ops_service.py
docker compose exec -T api python -m unittest app.services.tests.test_ops_service_llm -v
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.smoke_health_checks
git diff --check
```

Kết quả: unit + smoke pass; `system_status_llm.generation_backend=extractive`; `git diff --check` pass.

### Mục tiêu 6 — Frontend dashboard và trang `/status` (2026-06-07)

**Triển khai**

- Types `RagAnswerResponse`: `generation_mode`, `model_name`, `latency_ms`, `fallback_reason` typed.
- `useRagAnswer`: expose `generationMode`, `modelName`, `latencyMs` từ API.
- `RagAnswerPanel`: badge **Extractive** / **Generative (local)**; message fallback `llm_unavailable`, `validation_failed`; loading “Đang tổng hợp câu trả lời…”; disable nút Hỏi khi pending.
- `dashboard.vue`: truyền props mới từ composable.
- `SystemStatus.llm` + card LLM trên `/status` (backend, model, reachable).

**Kiểm tra**

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

Kết quả: web build pass; `git diff --check` pass.

### Mục tiêu 7 — Runbook dev/deploy và env documentation (2026-06-07)

**Triển khai**

- `docs/RAG_LLM_RUNBOOK.md`: profile dev/prod, pull model, GPU override, sizing RAM/GPU, prod checklist (firewall 11434 nội bộ, backup volume), fallback behavior, smoke commands, troubleshoot OOM/timeout.
- Cập nhật `docs/RAG_ANSWER_RUNBOOK.md`: phân nhánh extractive/generative, checklist UI badge và `/status`.
- Cập nhật `docs/COMPOSE_RESOURCE_UPLOAD_RUNBOOK.md`: bảng sizing Ollama, pointer backup `ollama_data`, troubleshoot LLM.
- Cập nhật `docs/STORAGE_BACKUP_RESTORE_RUNBOOK.md`: volume `ollama_data` optional + backup/restore.
```bash
git diff --check
```

Kết quả: pass.

### Mục tiêu 8 — Smoke generative, regression và hoàn tất phase (2026-06-07)

**Triển khai**

- Script `apps/api/app/scripts/smoke_rag_generative.py`: preflight Ollama + model loaded; seed fixture → POST answer → assert `generation_mode=generative`, citations hợp lệ; flag `--verify-fallback` chạy unit test `llm_unavailable`.
- `smoke_rag_answer._request_json`: tham số `timeout` (generative smoke dùng `RAG_LLM_TIMEOUT_SECONDS + 30`).

**Kiểm tra**

```bash
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.smoke_relation_suggestions
docker compose exec -T api python -m unittest app.services.tests.test_rag_answer_service -v
docker compose --profile llm exec -T api python -m app.scripts.smoke_rag_generative --verify-fallback
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

Kết quả: extractive + relation smokes pass; 7 unit tests pass; generative smoke pass (`latency_ms` ~13.8s CPU 3B); web build pass; `git diff --check` pass.

**Đóng phase**

- Phase 17 hoàn thành; `ROADMAP.md`, `docs/DOMAIN_MODULE_DECISION.md`, `TASK_NEXT.md` cập nhật placeholder Phase 18.

## Phase 18 — Dòng Hàng Mua Sắm Và Danh Mục Vật Tư MVP

Trạng thái: **đang thực hiện** — mục tiêu 1 hoàn thành (2026-06-08).

### Mục tiêu 1 — Thiết kế scope (2026-06-08)

- Thêm mục **Procurement Line Items (Phase 18)** trong `docs/DOMAIN_MODULE_DECISION.md`: schema `procurement_line_items` + `materials_catalog`, API contract, quyền/audit, filter search, ranh giới không làm.
- Chốt unique catalog: `lower(trim(code))` khi code non-empty; `lower(trim(name))` trên bản ghi active.
- Chốt `amount`: server tính `round(quantity * unit_price, 2)` khi đủ cả hai; cho phép `amount` explicit khi không có `unit_price`.
- Chốt search: `procurement_item_name` / `procurement_item_code` pre-resolve `document_id` (pattern Phase 11); không đổi Qdrant/chunk core.
- Phụ thuộc Phase 13 ghi rõ; không sửa `documents` / `document_chunks`.

Kiểm tra baseline Phase 17 (trước khi bắt đầu):

- `smoke_procurement_api`: pass.
- `smoke_health_checks`: pass.
- `smoke_rag_answer`: timeout (~28s) trên stack hiện tại — không chặn mục tiêu thiết kế docs; ghi nhận cho regression mục tiêu 8.
- `git diff --check`: pass.

### Mục tiêu 2 — Migration, model, repository (2026-06-08)

- Migration `0017_procurement_line_items`: bảng `procurement_line_items` (FK `procurement_id`, `line_number`, `item_name`, `item_code`, `unit`, `quantity`, `unit_price`, `amount`, `notes`, audit fields).
- Model `ProcurementLineItem`; quan hệ `ProcurementRecord.line_items`.
- `ProcurementLineItemRepository`: list/create/update/soft delete theo `procurement_id`; `get_max_line_number`, `sum_amount_by_procurement_id`.
- Index: `(procurement_id, line_number)` unique active; `(procurement_id, deleted_at)`; `(item_name, deleted_at)`; `(item_code, deleted_at)`.
- `catalog_item_id` deferred tới mục tiêu 4 (khi có `materials_catalog`).

Kiểm tra:

- `docker compose exec -T api alembic upgrade head`: pass.
- `py_compile` model + repository (trong container api): pass.
- `git diff --check`: pass.

### Lý do ưu tiên Phase 18

- Phòng vật tư cần tra cứu hồ sơ mua sắm theo **mặt hàng** (tên, mã, số lượng, đơn giá) — metadata cấp hồ sơ Phase 13 chưa đủ.
- OCR/chunk thường chứa bảng vật tư nhưng chưa cấu trúc hóa; line items là bước bridge trước inventory (Phase 19+).
- Giữ MVP: không tồn kho, không workflow phê duyệt nhiều bước, không LLM mới.

### Phạm vi đã chốt (tóm tắt — chi tiết `ROADMAP.md`)

| Hạng mục | Quyết định |
|----------|------------|
| Bảng dòng hàng | `procurement_line_items` — FK `procurement_id`, soft delete |
| Danh mục vật tư | `materials_catalog` — autocomplete; admin CRUD |
| API | Nested line items + flat PATCH/DELETE; catalog admin |
| Search/list | Filter `procurement_item_name`, `procurement_item_code` |
| Pre-fill OCR | Rule-based tùy chọn (mục tiêu 6 TASK_NEXT) — user xác nhận |
| Không làm | Stock, phiếu xuất/nhập, approval workflow, re-index Qdrant |

### Mục tiêu thực thi

Checklist 8 mục tiêu trong `TASK_NEXT.md`. Mục tiêu 1–2 ✅; tiếp theo mục tiêu 3 (service + API + smoke).

### Phase 19+ (dự kiến, chưa lập chi tiết)

- Inventory/tồn kho MVP (phụ thuộc line items).
- Workflow phê duyệt nhiều bước tối thiểu.
- LLM production ops / HA Ollama.
