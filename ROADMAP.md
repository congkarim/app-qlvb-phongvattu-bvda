# Roadmap Phát Triển

Cập nhật lần cuối: 2026-06-07

## Nguyên Tắc

- Local/on-prem first, không dùng cloud service.
- Docker Compose first cho mọi workflow dev và smoke.
- MVP first, chỉ mở rộng khi giải quyết rõ workflow nghiệp vụ.
- Backend giữ luồng `router -> service -> repository`.
- Frontend giữ luồng `page -> composable -> service -> API`.
- Không tự đổi stack: FastAPI, PostgreSQL, Redis, Qdrant, PaddleOCR, OpenCV, Nuxt 3, TypeScript, PrimeVue, TailwindCSS, Pinia.

## Trạng Thái Hiện Tại

**Lộ trình Phase 0–12 đã hoàn thành.** Hệ thống có thể chạy on-prem bằng Docker Compose với các service `api`, `worker`, `web`, `postgres`, `redis`, `qdrant`.

**Phase 13 đã được lập kế hoạch** (chi tiết bên dưới). Bắt đầu thực thi khi cập nhật `TASK_NEXT.md` checklist Phase 13.

Đã hoàn thành:
- Auth local, seed admin, cookie token frontend và RBAC nhẹ cho admin/user.
- Upload một file, nhiều file cùng văn bản, zip cùng văn bản; upload policy và giới hạn kích thước có thể cấu hình.
- Quản lý metadata nghiệp vụ, metadata OCR tự động và metadata manual review.
- OCR/extract cho text, markdown, docx, xlsx, PDF có text nhúng, PDF/image scan bằng PaddleOCR/OpenCV và VietOCR.
- Chunking văn bản hành chính tiếng Việt theo metadata pháp lý, phụ lục, confidence và flag `requires_review`.
- Semantic search có filter metadata nghiệp vụ, filter chunk như `section_role`, `requires_review`, filter metadata hợp đồng (`contract_number`, `supplier_name`, `contract_status`) và filter metadata công văn/quyết định (`dispatch_type`, `dispatch_status`, `decision_kind`, `decision_status`, `issuing_agency`).
- RAG foundation local-only: endpoint `POST /api/v1/search/answer` trả lời extractive kèm citation.
- Document detail có preview source, OCR job audit, chunks filter và action đánh dấu chunk đã review.
- Dashboard có semantic search, RAG Q&A extractive kèm citation, admin review queue có pagination/filter.
- Module hợp đồng MVP: backend `contract_records`, API CRUD, frontend `/contracts`; liên kết hai chiều với document detail.
- Module công văn đến/đi MVP: backend `dispatch_records`, API CRUD, frontend `/dispatches`; liên kết hai chiều với document detail.
- Module quyết định/thông báo MVP: backend `decision_records`, API CRUD, frontend `/decisions`; liên kết hai chiều với document detail.
- RAG UX dashboard: panel Hỏi đáp (RAG) trên `/dashboard`, runbook và smoke `smoke_rag_answer`.
- RAG citation UX: deep link `#chunk-{id}` trên document detail, citation/search result "Mở đoạn", badge metadata module trên dashboard.
- Admin catalog MVP: departments, business_type, document_type qua Catalog API; trang `/status` cho OCR/model/Qdrant/worker queue.
- Worker claim atomic, retry policy, queue status endpoint và smoke worker operations.
- On-prem hardening: env/secret/CORS guard, backup/restore runbook, health/readiness, log policy, compose resource limits.
- Worker lease timeout, stale-job recovery, ops endpoint job kẹt, runbook upgrade Alembic production, smoke worker stale recovery.

Giới hạn còn lại (đã gán vào Phase 13):
- Chưa có module sổ đề xuất/kế hoạch mua sắm vật tư (metadata layer, không workflow nhiều bước) → **Phase 13**.
- LLM/generator nội bộ nâng cao: **ngoài scope** Phase 11–13; RAG vẫn extractive local-only.

## Lộ Trình Ưu Tiên

### Phase 0 - MVP Foundation

Trạng thái: hoàn thành.

Mục tiêu: đưa hệ thống từ skeleton đến workflow web end-to-end có thể dùng để upload, OCR, chunk, search, review và audit.

Tiêu chí hoàn thành: workflow admin local có thể upload tài liệu, đợi đến searchable, search, mở document nguồn, review chunk và xem audit log.

### Phase 1 - Stabilize Core Workflows

Trạng thái: hoàn thành ngày 2026-06-05.

Mục tiêu: làm các workflow MVP ổn định hơn khi dữ liệu tăng lên và biến smoke thành kiểm tra có thể chạy lại.

Tiêu chí hoàn thành:
- Các list lớn có pagination ổn định, có total và không trùng item giữa các page.
- Smoke workflow login admin/user có thể chạy lại bằng command rõ ràng.
- User/admin permission smoke bao phủ các endpoint nhạy cảm.

### Phase 2 - Worker Reliability Và Operations

Trạng thái: hoàn thành ngày 2026-06-05.

Mục tiêu: giảm rủi ro khi chạy worker lâu dài hoặc nhiều worker trong môi trường on-prem.

Tiêu chí hoàn thành:
- Hai worker chạy song song không xử lý trùng một job.
- Job lỗi được retry/có failed state rõ ràng.
- Có smoke/command kiểm tra worker claim và retry.

### Phase 3 - Search Quality Và RAG Foundation

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu: tăng chất lượng retrieval và tạo nền tảng RAG local có citation mà không phụ thuộc cloud.

Tiêu chí hoàn thành:
- Có bộ benchmark search lặp lại được.
- Search result giải thích được bằng metadata/chunk citation.
- RAG endpoint trả lời kèm citation, không thay thế search MVP.

### Phase 4 - Domain Modules

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu: mở rộng từ kho văn bản chung sang module nghiệp vụ thực tế của phòng vật tư.

Đã thực hiện:
- Module đầu tiên: **Hợp đồng và phụ lục hợp đồng** (`contract_records`, API, `/contracts`).

Tiêu chí hoàn thành:
- Module có metadata riêng, filter riêng và không phá document/search core.
- UI giữ tái sử dụng component và service/composable hiện có.
- Migration có audit fields và soft delete theo quy tắc dự án.

### Phase 5 - Admin Configuration Và Governance

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu: để admin cấu hình hệ thống thay vì sửa code cho các danh mục và rule cơ bản.

Tiêu chí hoàn thành:
- Admin thay đổi danh mục có audit log.
- Frontend lấy option từ API thay vì hardcode.
- Admin xem được trạng thái OCR/model/Qdrant tối thiểu.

### Phase 6 - On-Prem Production Hardening

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu: chuẩn bị vận hành nội bộ on-prem một cách có kiểm soát.

Tiêu chí hoàn thành:
- Có runbook cài đặt, backup, restore, troubleshoot, log policy và upload/resource limits.
- Cấu hình production nội bộ không dùng default secret/admin password.
- Health/readiness và observability tối thiểu đủ cho vận hành on-prem.

### Phase 7 - Domain Integration Và Module Mở Rộng

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu: tăng giá trị nghiệp vụ thực tế sau khi nền tảng on-prem đã sẵn sàng, bắt đầu từ module hợp đồng hiện có và mở module nghiệp vụ thứ hai.

Phạm vi đề xuất:
- **Liên kết hợp đồng ↔ document core**: từ `/documents/[id]` mở metadata hợp đồng nếu có; từ `/contracts` drill-down sang document/chunks/search liên quan.
- **Search filter theo metadata hợp đồng**: filter dashboard/search theo nhà cung cấp, trạng thái, số hợp đồng khi phù hợp MVP.
- **Module nghiệp vụ thứ hai**: chọn **công văn đến/đi** làm ứng viên ưu tiên (metadata riêng, CRUD, list/filter UI theo pattern `contracts`).
- Thiết kế quyết định module mới trong `docs/DOMAIN_MODULE_DECISION.md` trước khi code.

Không làm trong phase này:
- Inventory/procurement workflow nhiều bước.
- LLM/generator nội bộ nâng cao.
- Thay đổi stack hoặc thêm cloud service.

Tiêu chí hoàn thành:
- Document detail và contract module liên kết hai chiều rõ ràng.
- Có ít nhất một filter search/dashboard dùng metadata hợp đồng.
- Module công văn đến/đi có schema, API, UI MVP và smoke script tái chạy được.
- Không phá upload/OCR/search/review workflow hiện có.

### Phase 8 - Worker Resilience Và Production Upgrade

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu: giảm rủi ro vận hành lâu dài khi worker crash hoặc khi nâng cấp phiên bản trên môi trường nội bộ.

Tiêu chí hoàn thành:
- Job `ocr_running` bị kẹt có cơ chế phát hiện và recovery có kiểm soát.
- Có runbook upgrade/migration có thể làm theo trên on-prem.
- Smoke worker recovery pass trên Docker Compose.

### Phase 9 - RAG UX Và Search Nâng Cao

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu: đưa RAG foundation từ API backend lên workflow người dùng và cải thiện search theo dữ liệu thật.

Đã thực hiện:
- Panel **Hỏi đáp (RAG)** trên `/dashboard` (`useRagAnswer`, `RagAnswerPanel`, `POST /search/answer`).
- Fallback `insufficient_evidence` phân biệt rõ trên UI; citation quote + link document.
- Runbook `docs/RAG_ANSWER_RUNBOOK.md` và smoke `smoke_rag_answer` tái chạy được.

Tiêu chí hoàn thành:
- User có thể hỏi–đáp trên web với citation rõ ràng.
- Fallback `insufficient_evidence` hiển thị đúng trên UI.
- Benchmark hoặc smoke RAG answer có thể chạy lại.

### Phase 10 - Module Quyết Định Và Thông Báo

Trạng thái: hoàn thành ngày 2026-06-07.

Mục tiêu: mở module nghiệp vụ thứ ba cho quyết định/thông báo nội bộ theo pattern hợp đồng và công văn.

Đã thực hiện:
- Thiết kế scope trong `docs/DOMAIN_MODULE_DECISION.md`.
- Schema `decision_records`, API CRUD `/api/v1/decisions`, UI `/decisions`, smoke `smoke_decision_api`.
- Liên kết hai chiều document detail ↔ module decision; search/RAG dashboard không regression.

Tiêu chí hoàn thành: đạt (xem `PROJECT_STATUS.md`).

### Phase 11 - Search Filter Metadata Dispatch Và Decision

Trạng thái: hoàn thành ngày 2026-06-07.

Mục tiêu: hoàn thiện semantic search và RAG trên dashboard theo metadata module công văn và quyết định/thông báo, đồng bộ pattern đã có với hợp đồng (Phase 7).

Phụ thuộc: Phase 10 (`decision_records`, `/decisions`); Phase 7 (`dispatch_records`, `/dispatches`); contract filter hiện có trong `SearchService`.

Phạm vi đề xuất:

**Backend — filter pre-resolve `document_id`**

- Mở rộng `SemanticSearchRequest`, `RagAnswerRequest` và `SearchService.semantic_search()`:
  - Dispatch: `dispatch_type`, `dispatch_document_number` (hoặc tái dùng `document_number` khi `business_type` là dispatch), `dispatch_issuing_agency`, `dispatch_status`.
  - Decision: `decision_kind`, `decision_document_number`, `decision_issuing_agency`, `decision_status`, `effective_from`, `effective_to` (date, optional).
- Thêm `DispatchRepository.list_document_ids_by_metadata()` và `DecisionRepository.list_document_ids_by_metadata()` — mirror `ContractRepository.list_document_ids_by_metadata()`.
- Khi có nhiều nhóm filter module cùng lúc: giao `document_id` (intersection); không có kết quả → trả `[]` sớm như contract filter.
- Cập nhật `search.py` router truyền đủ tham số; `RagAnswerService` kế thừa filter mới qua `SearchBackend` protocol.

**Backend — enrich kết quả (tùy chọn trong phase, ưu tiên mục tiêu 4)**

- `_attach_dispatch_metadata()` / `_attach_decision_metadata()` trên search result — pattern `_attach_contract_metadata()`.
- Trả thêm `dispatch_id`, `decision_id` và các trường hiển thị tối thiểu trên `SemanticSearchResult`.

**Frontend — dashboard**

- Mở rộng `SemanticSearchFilters` / `RagAnswerFilters` và `normalizeSearchPayload()`.
- UI filter có điều kiện: khi `business_type` là `incoming_dispatch`/`outgoing_dispatch` hiện nhóm dispatch; khi `decision` hiện nhóm decision (tránh form quá dài khi không liên quan).
- Preset query từ `/dispatches` và `/decisions` (nút "Search trong văn bản") truyền filter module tương ứng qua route query — đồng bộ với contract preset hiện có.
- `RagAnswerPanel` nhận filter mới; giữ hint `ragFilterChangedHint` khi đổi filter sau câu hỏi.

**Kiểm tra và tài liệu**

- Smoke mới hoặc mở rộng benchmark: seed dispatch/decision + search filter → assert `document_id` đúng, RAG `/search/answer` không regression.
- Cập nhật `docs/DOMAIN_MODULE_DECISION.md` mục "Search filter đã triển khai" khi xong.

Không làm trong phase này:

- Không sửa Qdrant payload hay re-index chunk.
- Không thêm LLM/generator; RAG vẫn extractive.
- Không deep-link citation `#chunk-{id}` (để Phase 12).
- Không module procurement mới.

Tiêu chí hoàn thành:

- Dashboard search lọc được theo ít nhất: `dispatch_type` + `dispatch_status`; `decision_kind` + `decision_status` (+ một trong `document_number` / `issuing_agency`).
- RAG dashboard dùng chung bộ filter; smoke/benchmark tái chạy được trên Docker Compose.
- Không regression search/RAG contract filter và upload/OCR/review workflow.

Mục tiêu gợi ý cho `TASK_NEXT.md` (khi mở phase):

1. Khảo sát contract filter + thiết kế tham số dispatch/decision (`solution-architect`, `semantic-search-rag`).
2. Repository `list_document_ids_by_metadata` dispatch + decision.
3. `SearchService` + schema + router + unit/smoke backend.
4. Frontend types/service/composable + dashboard UI filter.
5. Preset từ `/dispatches`, `/decisions`; smoke end-to-end; cập nhật `PROJECT_STATUS.md`.

---

### Phase 12 - RAG Citation UX Và Search Enrichment

Trạng thái: đang làm (bắt đầu 2026-06-07; mục tiêu 1 hoàn thành).

Mục tiêu: cải thiện truy vết nguồn từ search/RAG tới đúng đoạn văn bản trên document detail; làm giàu kết quả tìm kiếm với metadata module đầy đủ hơn.

Phụ thuộc: Phase 11 (filter dispatch/decision ổn định); document detail và chunk list hiện có.

Phạm vi đề xuất:

**Document detail — deep link chunk**

- Anchor `#chunk-{chunk_id}` trên `/documents/[id]`: khi mount hoặc hash change, scroll tới chunk card và highlight ngắn (class ring/border, không animation phức tạp).
- Chunk list giữ `id` ổn định trên DOM (`id="chunk-{id}"`).

**RAG citation**

- `RagCitation` và UI `RagAnswerPanel`: link dạng `/documents/{document_id}#chunk-{chunk_id}` thay vì chỉ document root.
- Fallback an toàn: nếu chunk không còn (đã xóa/ẩn), link về document detail không hash.

**Search result UX**

- Hiển thị badge/metadata module trên kết quả dashboard khi có `contract_*`, `dispatch_*`, `decision_*` từ enrich Phase 11.
- Tùy chọn: nút "Mở đoạn" trên mỗi result → cùng deep link.

**Extractive RAG nhẹ (không LLM)**

- Cải thiện ghép câu trả lời: ưu tiên 1–2 câu có overlap term cao nhất; giữ `grounded` / `insufficient_evidence` logic hiện có.
- Không thêm model inference mới; không service ngoài stack.

**Kiểm tra**

- Smoke hoặc mở rộng `smoke_rag_answer`: citation URL chứa `chunk_id`; manual checklist scroll-to-chunk.
- Benchmark search: case dispatch/decision filter + deep link fixture.

Không làm trong phase này:

- Không LLM local (Ollama, vLLM, v.v.).
- Không PDF viewer page-level scroll (chỉ chunk list text).
- Không thay đổi chunking/OCR pipeline.

Tiêu chí hoàn thành:

- Từ dashboard RAG, click citation mở document detail và scroll tới đúng chunk trong ≥1 fixture smoke.
- Search result hiển thị metadata module (contract/dispatch/decision) khi document có bản ghi active.
- Regression smoke RAG + semantic search pass.

Mục tiêu gợi ý cho `TASK_NEXT.md`:

1. Thiết kế anchor/scroll contract (`frontend-nuxt`).
2. Implement `#chunk-{id}` document detail + highlight.
3. Cập nhật RAG citation URL và panel.
4. Search result badges + optional "Mở đoạn".
5. Tin chỉnh extractive answer (nếu cần) + smoke/benchmark; cập nhật runbook RAG.

---

### Phase 13 - Module Đề Xuất / Kế Hoạch Mua Sắm MVP

Trạng thái: chưa bắt đầu (kế hoạch sẵn sàng; checklist trong `TASK_NEXT.md`).

Mục tiêu: mở module nghiệp vụ thứ tư — sổ đề xuất mua sắm và kế hoạch vật tư — theo pattern metadata 1-1 với document core; **không** mở workflow inventory/phê duyệt nhiều bước.

Phụ thuộc: Phase 11–12 (search/RAG đã hỗ trợ đủ 3 module trước; có thể thêm filter procurement ở cuối phase nếu còn slot).

Phạm vi đề xuất:

**Thiết kế (`docs/DOMAIN_MODULE_DECISION.md` — mục tiêu 1)**

- Chọn tên kỹ thuật: ví dụ bảng `procurement_records`, API `/api/v1/procurements`, route `/procurements`, audit entity `procurement`.
- `procurement_kind`: `proposal` (đề xuất mua sắm), `plan` (kế hoạch/dự toán), `acceptance` (biên bản nghiệm thu đơn giản) — giữ ≤3 giá trị cho MVP.
- Map `business_type` catalog hiện có (ví dụ mở rộng seed `procurement` / `purchase_plan` trong admin catalog nếu chưa có; ghi rõ trong thiết kế, không hardcode UI).
- Metadata tối thiểu: `document_id`, `procurement_kind`, `reference_number`, `title_summary`, `requesting_unit`, `estimated_value`, `currency` (default `VND`), `status`, `requested_date`, `notes`; join read-only `document_title`, `document_status` từ `documents`.
- Status MVP: `draft`, `submitted`, `approved`, `rejected`, `completed`, `archived` — cập nhật trực tiếp qua PATCH, không rule engine.

**Backend (mục tiêu 2–3)**

- Migration Alembic: UUID PK, audit fields, `deleted_at`, partial unique `document_id` active, index filter (`procurement_kind`, `reference_number`, `requesting_unit`, `status`, `requested_date`).
- `ProcurementRepository`, `ProcurementService`, router CRUD + `GET /procurements/by-document/{document_id}`.
- Quyền/audit giống contract/dispatch/decision: user CRUD; admin soft delete; audit `procurement.created|updated|deleted`.
- Smoke `python -m app.scripts.smoke_procurement_api`.

**Frontend (mục tiêu 4–5)**

- `procurement.ts`, `procurement.service.ts`, `useProcurements.ts`, page `/procurements` (list/filter/form).
- Nav item app shell; card liên kết hai chiều trên `/documents/[id]`.
- Nút preset search dashboard (sau khi có filter procurement hoặc dùng `business_type` + `reference_number` tạm thời).

**Search (mục tiêu 6 — có thể tách nhỏ)**

- Filter procurement trên search/RAG theo pattern Phase 11 (`procurement_kind`, `reference_number`, `status`, `requesting_unit`).
- Benchmark fixture `procurement_plan` đã có trong `benchmark_search_fixtures.py` — nối vào smoke.

Không làm trong MVP phase này:

- Không quản lý tồn kho, phiếu xuất/nhập kho, tồn tối thiểu.
- Không workflow trình ký nhiều bước, SLA, assignee, comment thread.
- Không bảng dòng hàng vật tư chi tiết (line items) trừ khi có yêu cầu rõ sau MVP.
- Không LLM trích xuất metadata; pre-fill từ document metadata/OCR đã có.
- Không thêm service ngoài PostgreSQL/Redis/Qdrant.

Tiêu chí hoàn thành:

- Có quyết định scope trong `docs/DOMAIN_MODULE_DECISION.md`.
- Schema + API + UI `/procurements` + liên kết document detail hai chiều + smoke tái chạy được.
- Ít nhất một luồng: upload document procurement → tạo metadata → list/filter → search/RAG không regression các module khác.

Mục tiêu gợi ý cho `TASK_NEXT.md`:

1. Thiết kế module procurement trong `DOMAIN_MODULE_DECISION.md`.
2. Migration + model `procurement_records`.
3. API + smoke backend.
4. Frontend `/procurements`.
5. Liên kết document detail + nav.
6. (Tùy chọn) Search filter procurement + benchmark; hoàn tất `PROJECT_STATUS.md`.

## Ghi Chú Lập Kế Hoạch

- `TASK_NEXT.md` chỉ chứa checklist phase đang làm; khi bắt đầu Phase 12, thay nội dung file bằng checklist mục tiêu Phase 12 ở trên.
- Con trỏ thực thi: `TASK_NEXT.md` → `PROJECT_STATUS.md` → commit sau mỗi mục tiêu (skill `project-git-manager`).
- Ưu tiên MVP và maintainability; mỗi module nghiệp vụ mới phải có quyết định scope trong `docs/DOMAIN_MODULE_DECISION.md`.
- Mỗi mục tiêu phase khi hoàn thành phải auto commit theo quy tắc trong `TASK_NEXT.md`.
