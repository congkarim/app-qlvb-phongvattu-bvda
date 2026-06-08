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

**Lộ trình Phase 0–17 đã hoàn thành.** Phase 18 đã lập kế hoạch (chưa bắt đầu code). Hệ thống có thể chạy on-prem bằng Docker Compose với các service `api`, `worker`, `web`, `postgres`, `redis`, `qdrant` (và `ollama` optional profile `llm`).

**Phase 13 đã hoàn thành** (2026-06-07): module đề xuất/kế hoạch mua sắm vật tư MVP.

**Phase 14 đã hoàn thành** (2026-06-07): gợi ý metadata module và onboarding sau OCR (API `onboarding-suggestions`, banner document detail, filter list `missing_module_metadata`, smoke `smoke_module_onboarding`).

**Phase 15 đã hoàn thành** (2026-06-07): liên kết chéo document (`document_relations`) — API GET/POST/DELETE, card document detail, filter/badge list, smoke `smoke_document_relations`.

**Phase 16 đã hoàn thành** (2026-06-07): gợi ý liên kết document rule-based từ OCR/chunk — `DocumentRelationSuggestionService`, API `relation-suggestions`, subsection **Gợi ý liên kết** trên document detail, apply/dismiss UX, smoke `smoke_relation_suggestions`.

**Phase 17 đã hoàn thành** (2026-06-07): RAG generative Ollama on-prem — `LocalLLMService`, profile Compose `llm`, fallback extractive, ops/dashboard UX, runbook `docs/RAG_LLM_RUNBOOK.md`, smoke `smoke_rag_generative`.

**Phase 18 đã lập kế hoạch** (2026-06-07): dòng hàng mua sắm (`procurement_line_items`) + danh mục vật tư (`materials_catalog`) — chưa bắt đầu code; checklist `TASK_NEXT.md`.

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
- Module mua sắm MVP: backend `procurement_records`, API CRUD, frontend `/procurements`; liên kết hai chiều với document detail; filter search/RAG theo metadata procurement.
- RAG UX dashboard: panel Hỏi đáp (RAG) trên `/dashboard`, runbook và smoke `smoke_rag_answer`.
- RAG citation UX: deep link `#chunk-{id}` trên document detail, citation/search result "Mở đoạn", badge metadata module trên dashboard.
- Admin catalog MVP: departments, business_type, document_type qua Catalog API; trang `/status` cho OCR/model/Qdrant/worker queue.
- Worker claim atomic, retry policy, queue status endpoint và smoke worker operations.
- On-prem hardening: env/secret/CORS guard, backup/restore runbook, health/readiness, log policy, compose resource limits.
- Worker lease timeout, stale-job recovery, ops endpoint job kẹt, runbook upgrade Alembic production, smoke worker stale recovery.
- Onboarding metadata module sau OCR: `ModuleOnboardingService`, `GET /documents/{id}/onboarding-suggestions`, audit worker `document.onboarding_suggested`, banner/CTA document detail, filter/badge list `missing_module_metadata`.
- Liên kết chéo document: bảng `document_relations`, API relations, card **Văn bản liên quan** trên document detail, filter/badge `has_relations`/`relation_count` trên list, smoke `smoke_document_relations`.
- Gợi ý liên kết document rule-based: `DocumentRelationSuggestionService`, API `GET /documents/{id}/relation-suggestions`, subsection **Gợi ý liên kết** trên document detail (apply/dismiss), smoke `smoke_relation_suggestions`.
- RAG generative local LLM (Ollama): `LocalLLMService`, profile Compose `llm`, `RagContextBuilder`/`CitationValidator`, fallback extractive, ops LLM status, dashboard badge generative/extractive, runbook `docs/RAG_LLM_RUNBOOK.md`, smoke `smoke_rag_generative`.

Giới hạn còn lại (đã gán / ngoài scope Phase 18):
- Inventory/tồn kho, phiếu xuất/nhập, tồn tối thiểu → **Phase 19+** (chưa lập kế hoạch).
- Workflow phê duyệt nhiều bước, SLA, assignee → **Phase 19+**.
- HA Ollama / scale horizontal LLM / tách LLM host production → **Phase 19+** (ops, không chặn Phase 18).

**Phase 18 đã lập kế hoạch** (2026-06-07): dòng hàng mua sắm (`procurement_line_items`) + danh mục vật tư nhẹ (`materials_catalog`) — xem checklist `TASK_NEXT.md`.

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

Trạng thái: hoàn thành (2026-06-07).

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

Trạng thái: hoàn thành (2026-06-07).

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

---

### Phase 14 - Gợi Ý Metadata Module Và Onboarding Sau OCR

Trạng thái: hoàn thành (2026-06-07).

Mục tiêu: rút ngắn khoảng cách giữa classifier OCR rule-based hiện có (`DocumentClassifierService`) và 4 module nghiệp vụ — gợi ý `business_type`, loại module (`dispatch_type`, `decision_kind`, `procurement_kind`) và pre-fill form tạo metadata; **không** tự tạo bản ghi module mà không có xác nhận người dùng.

Phụ thuộc: Phase 5 (catalog `business_type` qua API); Phase 7–13 (4 module + liên kết document detail); worker OCR đã gọi classifier và lưu metadata document.

Bối cảnh hiện tại:
- Worker classify trích `document_type`, số văn bản, cơ quan ban hành, trích yếu, người nhận, v.v. nhưng **giữ nguyên** `business_type` từ lúc upload.
- Document detail có card module từng loại nhưng user phải tự nhận diện và mở form thủ công.
- Form module đã pre-fill một phần từ metadata document; chưa có luồng “gợi ý tạo metadata” thống nhất sau OCR.

Phạm vi đề xuất:

**Thiết kế (`docs/DOMAIN_MODULE_DECISION.md` — mục tiêu 1)**

- Bảng mapping `document_type` (classifier) → `business_type` catalog + module target (`contract` | `dispatch` | `decision` | `procurement`).
- Heuristic bổ sung khi cần:
  - `CV` → `incoming_dispatch` hoặc `outgoing_dispatch` (dựa `recipient` / pattern “V/v” / hướng công văn nếu trích được).
  - `QĐ` / `TB` → `decision` + `decision_kind`.
  - `HĐ` → `contract`.
  - `KH` / `TTr` / `BB` / `ĐX` (và tương đương) → `procurement` + `procurement_kind` (`plan` | `proposal` | `acceptance`).
- Ngưỡng `classification_confidence` để phân biệt gợi ý “chắc” vs “cần review”; ghi rõ không ghi đè metadata đã `metadata_reviewed_at` / `metadata_source=manual|mixed`.
- Payload gợi ý module: map field classifier → field form module (mirror pre-fill hiện có trên từng page).

**Backend (mục tiêu 2–3)**

- `ModuleOnboardingService` (hoặc mở rộng `DocumentClassifierService`): `suggest_business_type()`, `suggest_module_record(document)` trả DTO gồm `target_module`, `suggested_fields`, `confidence`, `reasons[]`.
- API read-only: `GET /api/v1/documents/{document_id}/onboarding-suggestions` — trả gợi ý business_type + module pre-fill nếu document searchable và chưa có bản ghi module active.
- Worker (tùy chọn có kiểm soát): khi upload **chưa** chọn `business_type` (hoặc giá trị mặc định rỗng) và confidence ≥ ngưỡng, **đề xuất** lưu `business_type` gợi ý kèm `metadata_source=mixed` hoặc chỉ audit `document.business_type_suggested` — **không** auto-apply nếu user đã chọn business_type lúc upload.
- Audit: `document.onboarding_suggested`, `document.business_type_applied` (metadata JSON gọn).

**Frontend (mục tiêu 4–5)**

- Document detail `/documents/[id]`:
  - Banner/card **Gợi ý metadata** khi có suggestion và chưa có module record: hiển thị `business_type` + module đích, nút “Áp dụng loại nghiệp vụ” và “Tạo metadata {module}” mở form pre-fill (reuse composable/service module hiện có).
  - Trạng thái low-confidence: nhắc review metadata document (không chặn workflow).
- Trang danh sách document (hoặc filter trên list hiện có):
  - Badge/cột “Chưa có metadata module” khi `business_type` khớp module nhưng thiếu bản ghi active.
  - Filter nhanh: `missing_module_metadata=true` (query API list documents).

**Kiểm tra (mục tiêu 6)**

- Smoke mới `smoke_module_onboarding.py`: seed document qua OCR/classifier fixture → assert suggestion mapping → apply business_type → tạo module record pre-fill.
- Regression: `smoke_api_workflows`, `smoke_procurement_api`, `smoke_search_module_filters`, `smoke_rag_answer`, `check_document_classifier`.
- Frontend build pass.

Không làm trong phase này:

- Không LLM / model inference mới (Ollama, vLLM, v.v.).
- Không auto-create module record im lặng; mọi tạo metadata vẫn qua form + API CRUD hiện có.
- Không bảng `document_relations` / liên kết chéo document.
- Không inventory, line items procurement, workflow phê duyệt nhiều bước.
- Không thay đổi chunking/Qdrant payload hay re-index hàng loạt.
- Không thêm service ngoài PostgreSQL/Redis/Qdrant.

Tiêu chí hoàn thành:

- Sau OCR searchable, document detail hiển thị gợi ý module hợp lệ cho ≥1 fixture mỗi loại (`contract`, `dispatch`, `decision`, `procurement`).
- User có thể áp dụng `business_type` gợi ý và mở form tạo metadata module với field pre-fill từ classifier trong ≤2 thao tác UI.
- List/filter “thiếu metadata module” hoạt động cho admin/user có quyền list document.
- Smoke onboarding + regression hiện có pass trên Docker Compose.
- Quyết định mapping ghi trong `docs/DOMAIN_MODULE_DECISION.md`.

Mục tiêu gợi ý cho `TASK_NEXT.md`:

1. Thiết kế mapping classifier → business_type/module trong `DOMAIN_MODULE_DECISION.md` (`solution-architect`, `vn-admin-doc-ocr-classifier`).
2. `ModuleOnboardingService` + schema response + API `onboarding-suggestions`.
3. Worker/audit gợi ý `business_type` có kiểm soát (nếu scope mục tiêu 2 chưa đủ).
4. Document detail: banner gợi ý + CTA tạo metadata pre-fill (`frontend-nuxt`).
5. Document list: badge/filter thiếu metadata module.
6. Smoke `smoke_module_onboarding` + regression; hoàn tất `PROJECT_STATUS.md`.

---

### Phase 15 - Liên Kết Chéo Document (`document_relations`)

Trạng thái: hoàn thành ngày 2026-06-07.

Mục tiêu: cho phép gắn quan hệ có hướng giữa hai văn bản độc lập (khác `document_files` nhiều tệp cùng một document) — ví dụ công văn **tham chiếu** quyết định, phụ lục upload riêng **thuộc** hợp đồng — để tra cứu hai chiều từ document detail mà không đổi pipeline OCR/chunk hiện có.

Phụ thuộc: Phase 0–14 (document core, 4 module metadata, audit, RBAC user/admin).

Bối cảnh hiện tại:
- Một `documents` có thể có nhiều `document_files` (cùng văn bản gốc); chunk `section_role=appendix` mô tả phụ lục **trong** cùng document.
- Chưa có bảng/API liên kết **document A → document B** khi upload tách file hoặc văn bản tham chiếu văn bản khác.
- Document detail có card module (hợp đồng/công văn/QĐ/mua sắm) nhưng không có danh sách văn bản liên quan chéo.

Phạm vi đề xuất:

**Thiết kế (`docs/DOMAIN_MODULE_DECISION.md` — mục tiêu 1)**

- Bảng `document_relations`: quan hệ **có hướng** `source_document_id` → `target_document_id`.
- `relation_type` MVP (≤4): `references` (tham chiếu/căn cứ), `appendix_of` (phụ lục của), `implements` (triển khai/thực hiện), `related` (liên quan chung).
- Trường: `notes` (tùy chọn), `created_by_user_id` (audit), UUID PK, `created_at`/`updated_at`/`deleted_at`.
- Ràng buộc: không self-link; unique partial active `(source_document_id, target_document_id, relation_type)`; index tra cứu incoming/outgoing.
- API đọc/ghi thủ công — **không** auto-tạo relation từ OCR trong MVP.

**Backend (mục tiêu 2–3)**

- Migration Alembic `0016_document_relations`.
- `DocumentRelationRepository`, `DocumentRelationService`, router:
  - `GET /api/v1/documents/{document_id}/relations` — `{ outgoing[], incoming[] }` kèm metadata tóm tắt target/source.
  - `POST /api/v1/documents/{document_id}/relations` — body `{ target_document_id, relation_type, notes? }`.
  - `DELETE /api/v1/document-relations/{relation_id}` — soft delete (admin hoặc creator tùy quyết định mục tiêu 1).
- Audit: `document_relation.created`, `document_relation.deleted`.
- Smoke `python -m app.scripts.smoke_document_relations`.

**Frontend (mục tiêu 4–5)**

- Document detail `/documents/[id]`: card **Văn bản liên quan** — hai nhóm outgoing/incoming, form thêm liên kết (chọn document đích + loại quan hệ), nút xóa.
- Composable `useDocumentRelations` + service typed; không gọi API trong component.
- (Mục tiêu 5) Badge/số lượng liên kết trên document list hoặc filter `has_relations=true` — chỉ khi API list mở rộng nhẹ, không regression pagination.

**Kiểm tra (mục tiêu 6)**

- Smoke `smoke_document_relations`: tạo 2–3 document → POST relation → GET hai chiều → DELETE → regression `smoke_api_workflows`, `smoke_module_onboarding`, search/RAG smokes.
- Frontend build pass.

Không làm trong phase này:

- Không LLM/rule engine tự trích quan hệ từ nội dung chunk (có thể phase sau).
- Không đồ thị visualization, không workflow phê duyệt chuỗi văn bản.
- Không đổi Qdrant payload, không re-index hàng loạt.
- Không inventory, line items, module nghiệp vụ mới.
- Không merge/split document.

Tiêu chí hoàn thành:

- Quyết định scope trong `docs/DOMAIN_MODULE_DECISION.md`.
- User tạo/xem/xóa liên kết giữa hai document searchable từ document detail trong ≤3 thao tác UI.
- Tra cứu incoming/outgoing chính xác; soft delete không làm hỏng pagination list documents.
- Smoke relations + regression hiện có pass trên Docker Compose.

Mục tiêu gợi ý cho `TASK_NEXT.md`:

1. Thiết kế `document_relations` trong `DOMAIN_MODULE_DECISION.md` (`solution-architect`, `database-designer`).
2. Migration + model + repository.
3. Service + API + audit + smoke backend.
4. Frontend card liên kết trên document detail (`frontend-nuxt`).
5. Badge/filter list (tùy chọn nhẹ) hoặc enrich list item `relation_count`.
6. Smoke end-to-end + regression; đóng Phase 15 trong `PROJECT_STATUS.md`.

---

### Phase 16 - Gợi Ý Liên Kết Document Từ Nội Dung (Rule-Based)

Trạng thái: hoàn thành ngày 2026-06-07.

Mục tiêu: gợi ý quan hệ giữa hai document searchable bằng heuristic trên OCR/chunk (số văn bản, cụm “Căn cứ”, “Phụ lục”, “Thực hiện”) — user **xác nhận** trước khi tạo bản ghi `document_relations`; không auto-link im lặng.

Phụ thuộc: Phase 15 (`document_relations`, `DocumentRelationsCard`); Phase 14 (pattern banner gợi ý + CTA xác nhận); classifier/chunk metadata hiện có (`document_number`, `document_type`, `section_role`).

Bối cảnh hiện tại:
- Phase 15 chỉ tạo liên kết **thủ công** — user phải biết document đích và nhập UUID/tìm list.
- Chunk nhóm B/C thường chứa tham chiếu số văn bản khác (“Căn cứ Quyết định số 02/QĐ-VT”, “Hợp đồng số …”, “kèm theo Phụ lục …”).
- `DocumentClassifierService` đã trích `document_number` từ trang đầu; chưa có bước **đối chiếu** số đó với kho document khác.

Phạm vi đề xuất:

**Thiết kế (`docs/DOMAIN_MODULE_DECISION.md` — mục tiêu 1)**

- Heuristic trích **reference candidates** từ text chunk (ưu tiên chunk đầu, `section_role` `article`/`unknown`, trang 1–2):
  - Regex số/ký hiệu hành chính VN (mirror classifier): `\d+/[A-ZĐ]+-…`, “số …/QĐ”, “số …/CV”, “HĐ số …”.
  - Anchor phrase → `relation_type` gợi ý: `Căn cứ`/`căn cứ` → `references`; `Phụ lục`/`kèm theo` + ngữ cảnh HĐ → `appendix_of`; `Thực hiện`/`triển khai` → `implements`; mặc định khớp số mơ hồ → `related`.
- Chiến lược match document đích:
  1. Exact/normalized `document_number` trên `documents` active searchable.
  2. (Tùy chọn) khớp `document_symbol` + năm nếu số không đủ.
  3. Loại trừ self, document đã có relation active cùng triple, target không searchable.
- DTO gợi ý: `target_document_id`, `relation_type`, `confidence` (0–1), `matched_reference` (chuỗi trích), `source_chunk_id`, `reasons[]`.
- Ngưỡng hiển thị UI: ≥1 candidate match; phân `high` / `review` theo confidence (không chặn workflow).

**Backend (mục tiêu 2–3)**

- `DocumentRelationSuggestionService` (hoặc mở rộng `DocumentRelationService`):
  - `suggest_relations(document_id) -> list[RelationSuggestion]`.
  - Đọc chunk qua `DocumentRepository`; lookup đích qua query indexed `document_number` (và symbol nếu có).
- API read-only: `GET /api/v1/documents/{document_id}/relation-suggestions` — chỉ khi document searchable; trả tối đa N gợi ý (ví dụ 8), dedupe theo `(target_document_id, relation_type)`.
- **Không** POST tự động; tạo liên kết vẫn qua `POST /documents/{id}/relations` hiện có.
- Audit tùy chọn (mục tiêu 3): `document.relation_suggested` khi user mở panel gợi ý hoặc worker ghi nhận lần quét — metadata JSON gọn (`candidate_count`); không ghi DB relation.

**Frontend (mục tiêu 4–5)**

- Mở rộng `DocumentRelationsCard` (hoặc subsection **Gợi ý liên kết**):
  - Gọi `useDocumentRelationSuggestions` + service typed.
  - Mỗi gợi ý: nhãn quan hệ, title/number document đích, quote ngắn từ chunk, nút **Tạo liên kết** (gọi POST relations có sẵn) và **Bỏ qua** (client-side dismiss session).
  - Low-confidence: style nhắc review, không auto-apply.
- Sau khi tạo thành công: refresh outgoing/incoming + ẩn gợi ý đã apply.

**Kiểm tra (mục tiêu 6)**

- Smoke `smoke_relation_suggestions.py`: seed QĐ A + CV B (B text chứa “Căn cứ Quyết định số …” khớp A) → GET suggestions → POST relation → assert biến mất khỏi gợi ý.
- Regression: `smoke_document_relations`, `smoke_module_onboarding`, `smoke_search_module_filters`, `smoke_rag_answer`, `check_document_classifier`.
- Frontend build pass.

Không làm trong phase này:

- Không LLM / embedding similarity cross-document (Phase 17+).
- Không auto-create `document_relations` từ worker mà không qua UI xác nhận.
- Không đồ thị visualization, merge/split document.
- Không đổi Qdrant payload, không re-index hàng loạt.
- Không inventory, line items, workflow phê duyệt, module nghiệp vụ mới.

Tiêu chí hoàn thành:

- Quyết định heuristic + mapping ghi trong `docs/DOMAIN_MODULE_DECISION.md`.
- Với fixture smoke (CV → QĐ), document detail hiển thị ≥1 gợi ý đúng `target_document_id` và `relation_type` hợp lý.
- User tạo liên kết từ gợi ý trong ≤2 thao tác (Tạo liên kết → thấy trong outgoing).
- Smoke suggestions + regression Phase 15 pass trên Docker Compose.

Mục tiêu gợi ý cho `TASK_NEXT.md`:

1. Thiết kế heuristic + DTO trong `DOMAIN_MODULE_DECISION.md` (`solution-architect`, `vn-admin-doc-ocr-classifier`).
2. `DocumentRelationSuggestionService` + lookup `document_number`.
3. API `relation-suggestions` + schema response.
4. Frontend gợi ý trong `DocumentRelationsCard` (`frontend-nuxt`).
5. Dismiss/apply UX + refresh relations list.
6. Smoke `smoke_relation_suggestions` + regression; hoàn tất `PROJECT_STATUS.md`.

---

### Phase 17 - RAG Generative Local LLM (Ollama On-Prem)

Trạng thái: **hoàn thành** (2026-06-07).

Mục tiêu: nâng `POST /api/v1/search/answer` từ **extractive** (ghép câu từ chunk) sang **generative local-only** qua **Ollama**, vẫn **bắt buộc citation** truy vết chunk/document; tự **fallback extractive** khi LLM không sẵn sàng, timeout hoặc không đủ căn cứ.

Phụ thuộc: Phase 3/9/12 (RAG extractive, dashboard Q&A, citation deep-link `#chunk-{id}`); Phase 6 (on-prem hardening, resource limits); embedding/Qdrant hiện có **không đổi**.

Bối cảnh hiện tại:
- `RagAnswerService` chỉ `_compose_answer()` bằng cách nối quote từ top citation — đủ MVP, không tổng hợp đa chunk.
- Retrieval, filter metadata module, rerank và schema `RagCitation` đã ổn — Phase 17 chỉ thêm **lớp generation** sau retrieval.
- Stack on-prem hiện ~**10 GB RAM limit** tổng (compose defaults); worker OCR là consumer nặng nhất (4 GB). LLM phải **tách service** và **profile Compose** để dev không bắt buộc chạy model.

#### Quyết Định Kiến Trúc (Đề Xuất Chốt Ở Mục Tiêu 1)

| Hạng mục | Quyết định MVP | Lý do |
|----------|----------------|-------|
| LLM runtime | **Ollama** (HTTP OpenAI-compatible `/api/chat`) | Cài model offline, một container, dev/prod giống nhau; không thêm Python binding nặng vào `api` |
| vLLM / llama.cpp server | **Không** trong MVP | vLLM cần GPU + ops phức tạp; llama.cpp tự host kém nhất quán với Docker Compose first |
| Generation backend | `RAG_GENERATION_BACKEND=extractive \| ollama` | Mặc định `extractive` — CI/smoke/dev máy yếu không cần LLM |
| Retrieval | Giữ nguyên `SearchService` + Qdrant | Không re-index, không đổi payload |
| Citation | Bắt buộc; post-validate quote ⊆ chunk retrieved | Tránh hallucination; không citation hợp lệ → fallback |
| Worker | **Không** gọi LLM | Generation chỉ sync trên request RAG (tránh queue OCR + LLM tranh RAM) |

Luồng đề xuất:

```text
query + filters
  -> SearchService.semantic_search (top-k)
  -> RagContextBuilder (format chunk + metadata cho prompt)
  -> LocalLLMService.generate (Ollama)  [nếu backend=ollama và healthy]
  -> CitationValidator (quote khớp chunk, chunk_id ∈ retrieval set)
  -> response { answer, grounded, generation_mode, citations, fallback_reason? }
  -> nếu fail bất kỳ bước LLM: RagAnswerService extractive hiện tại
```

Model đề xuất (tiếng Việt + instruction-following, có trên Ollama library):

| Profile | Model Ollama | Quant | RAM/VRAM ước tính | Ghi chú |
|---------|--------------|-------|-------------------|---------|
| Dev / smoke | `qwen2.5:3b-instruct` | Q4_K_M | ~3–4 GB | Đủ cho smoke generative trên CPU; chậm chấp nhận được |
| Prod CPU | `qwen2.5:7b-instruct` | Q4_K_M | ~6–8 GB | Chất lượng tốt hơn; cần máy ≥32 GB RAM tổng |
| Prod GPU | `qwen2.5:7b-instruct` | Q4_K_M | ~6 GB VRAM | Latency mục tiêu 3–15 s/câu; khuyến nghị cho phòng ban dùng thật |

Fine-tune / LoRA / model riêng: **ngoài scope** Phase 17 MVP.

#### Tính Toán Tài Nguyên — Baseline Hiện Tại

Giới hạn Compose mặc định (`docs/COMPOSE_RESOURCE_UPLOAD_RUNBOOK.md`):

| Service | CPU limit | RAM limit | Ghi chú |
|---------|-----------|-----------|---------|
| postgres | 1 | 1 G | Metadata |
| redis | 0.5 | 512 M | Queue/cache |
| qdrant | 1 | 2 G | Vector |
| api | 1 | 2 G | FastAPI + upload |
| worker | 2 | 4 G | OCR peak |
| web | 0.5 | 512 M | Nuxt |
| **Tổng limit** | **6 CPU** | **~10 G** | Limit ≠ usage thực; worker thường peak 2.5–3.5 G khi OCR |

Embedding (BKAI 384-d, CPU): ~200–400 MB thêm trong worker/api khi load model thật (dev thường `EMBEDDING_BACKEND=fake`).

#### Tính Toán Tài Nguyên — Thêm Ollama

| Profile Compose | Service thêm | RAM thêm (limit) | CPU thêm | GPU | Tổng RAM host khuyến nghị |
|-----------------|--------------|------------------|----------|-----|---------------------------|
| **core** (mặc định) | — | 0 | — | — | **8 GB** tối thiểu dev extractive-only |
| **llm-dev** | `ollama` + model 3B Q4 | **+6 G** | +2 | Không | **16 GB** (core ~8G working + 6G ollama headroom) |
| **llm-prod-cpu** | `ollama` + model 7B Q4 | **+10 G** | +4 | Không | **32 GB** (core peak + LLM không swap) |
| **llm-prod-gpu** | `ollama` + model 7B Q4 | **+4 G** | +2 | **≥8 GB VRAM** | **16 GB RAM** host + GPU; OCR worker vẫn CPU |

**Lưu ý vận hành:**
- Không chạy OCR job lớn và RAG generative **đồng thời** trên máy 16 GB — queue worker hoặc giới hạn `OLLAMA_NUM_PARALLEL=1`.
- Model file lưu volume `ollama_data` (~2 GB cho 3B, ~5 GB cho 7B Q4) — backup riêng, không vào git.
- Latency CPU (3B, câu hỏi + 6 chunk context): **15–45 s**; GPU 7B: **3–15 s**. UI phải có loading rõ và timeout backend (`RAG_LLM_TIMEOUT_SECONDS`, đề xuất 120 dev / 90 prod GPU).

#### Cấu Hình Dev

**Mục tiêu:** developer clone repo chạy được ngay **không cần LLM**; bật LLM tùy chọn khi máy đủ RAM.

1. **Mặc định (không profile `llm`):**

```env
RAG_GENERATION_BACKEND=extractive
# Ollama service không start
```

- `docker compose up` như hiện tại — smoke `smoke_rag_answer` pass (extractive).
- Máy **8 GB RAM** vẫn dev được OCR + search + RAG extractive.

2. **Dev có LLM (`--profile llm`):**

```env
RAG_GENERATION_BACKEND=ollama
OLLAMA_BASE_URL=http://ollama:11434
RAG_LLM_MODEL=qwen2.5:3b-instruct
RAG_LLM_TIMEOUT_SECONDS=120
RAG_LLM_MAX_CONTEXT_CHARS=8000
RAG_LLM_MAX_OUTPUT_TOKENS=512
RAG_LLM_TEMPERATURE=0.1
OLLAMA_CPU_LIMIT=2
OLLAMA_MEMORY_LIMIT=6G
```

```bash
# Pull model một lần (trong container ollama)
docker compose --profile llm up -d
docker compose exec ollama ollama pull qwen2.5:3b-instruct
```

- File đề xuất: `docker-compose.yml` thêm service `ollama` với `profiles: [llm]`; `docker-compose.override.example.yml` hoặc `.env.example` ghi biến trên.
- Readiness: `api` `/health/ready` **không fail** khi Ollama down — chỉ RAG generative fallback; `/ops/system-status` báo `llm: degraded`.

3. **Dev GPU (tùy chọn):** `docker-compose.llm-gpu.yml` override:

```yaml
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

Chỉ dùng khi host có NVIDIA Container Toolkit; không bắt buộc cho MVP.

#### Cấu Hình Deploy Production On-Prem

**Khuyến nghị topology:**

| Quy mô | Topology | Ghi chú |
|--------|----------|---------|
| Phòng ban nhỏ (≤10 user) | **All-in-one** — core + ollama trên 1 server 32 GB RAM, GPU nếu có | Đơn giản vận hành |
| Phòng lớn / OCR nhiều | **Tách LLM** — `OLLAMA_BASE_URL=http://llm-host:11434` trên server GPU riêng | Worker OCR không tranh RAM với 7B |
| HA | **Không** trong MVP | Một instance Ollama; scale horizontal Phase 18+ nếu cần |

**Production env (ví dụ CPU-only 32 GB):**

```env
APP_ENV=production
RAG_GENERATION_BACKEND=ollama
OLLAMA_BASE_URL=http://ollama:11434
RAG_LLM_MODEL=qwen2.5:7b-instruct
RAG_LLM_TIMEOUT_SECONDS=90
RAG_LLM_MAX_CONTEXT_CHARS=12000
RAG_LLM_MAX_OUTPUT_TOKENS=768
RAG_LLM_TEMPERATURE=0.1
OLLAMA_CPU_LIMIT=4
OLLAMA_MEMORY_LIMIT=10G
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_NUM_PARALLEL=1
# Production guard hiện có vẫn áp dụng: JWT, ADMIN_PASSWORD, CORS, DATABASE_URL
```

**Production env (GPU 8 GB VRAM):**

```env
RAG_LLM_MODEL=qwen2.5:7b-instruct
OLLAMA_MEMORY_LIMIT=4G
OLLAMA_CPU_LIMIT=2
# compose -f docker-compose.yml -f docker-compose.llm-gpu.yml --profile llm up -d
```

**Checklist deploy mới (mục tiêu 7 — runbook):**
- Pull/load model offline trước go-live (`ollama pull` trên máy có internet, export volume hoặc copy `~/.ollama/models`).
- Mở firewall **chỉ nội bộ** cho port 11434 nếu LLM tách host; không expose public.
- Giám sát: `/status` hiển thị model loaded, `generation_backend`, latency P95 (log metric đơn giản).
- Backup: thêm `ollama_data` vào runbook storage (cùng `docs/STORAGE_BACKUP_RESTORE_RUNBOOK.md`).

#### Phạm Vi Kỹ Thuật

**Backend (mục tiêu 2–4)**
- `LocalLLMService` (Ollama HTTP client): health, chat completion, timeout, structured errors.
- Settings mới trong `config.py` (mirror pattern `embedding_backend`).
- `RagGenerativeService` hoặc mở rộng `RagAnswerService`: nhánh `ollama` + fallback extractive.
- `RagContextBuilder`: format top-k chunk (index, chunk_id, title, số VB, quote snippet) cho prompt tiếng Việt.
- `CitationValidator`: mọi `[n]` / chunk_id trong answer phải map citation đã retrieve; quote overlap tối thiểu.
- Schema response mở rộng: `generation_mode: extractive | generative`, `model_name?`, `latency_ms?`, giữ nguyên `citations[]`.

**Prompt MVP (mục tiêu 1 — ghi `DOMAIN_MODULE_DECISION.md`):**
- System: trả lời tiếng Việt, chỉ dựa context, không bịa, trích `[1]..[n]` mapping chunk index.
- User: câu hỏi + block context numbered.
- Post-process: parse citation markers → build `citations[]` giống schema hiện tại.

**Docker Compose (mục tiêu 3)**
- Service `ollama` (`ollama/ollama` image), profile `llm`, volume `ollama_data`, healthcheck `GET /api/tags`.
- `api` depends_on `ollama` **chỉ khi** profile active (compose `depends_on` + condition service_started).
- Override GPU file tách riêng; cập nhật `docs/COMPOSE_RESOURCE_UPLOAD_RUNBOOK.md`.

**Frontend (mục tiêu 5)**
- Dashboard RAG panel: badge **Extractive** / **Generative (local)**; hiển thị khi fallback (`fallback_reason`, `generation_mode`).
- Loading state timeout-aware (disable nút Hỏi, message “Đang tổng hợp câu trả lời…”).
- `/status`: card LLM (model, backend, reachable).

**Ops (mục tiêu 6–7)**
- `OpsService._get_llm_status()` tương tự embedding.
- Runbook `docs/RAG_LLM_RUNBOOK.md`: pull model, profile dev/prod, troubleshoot OOM, fallback.

Không làm trong phase này:
- Cloud LLM / OpenAI API.
- Fine-tune, RAG agent multi-step, tool calling.
- Streaming SSE (có thể stretch sau MVP nếu UX cần).
- Thay embedding model, re-index Qdrant, đổi chunking.
- LLM trong worker OCR pipeline.
- vLLM production path (chỉ ghi chú future).

#### Tiêu Chí Hoàn Thành Phase

- Quyết định generation + prompt + validation ghi trong `docs/DOMAIN_MODULE_DECISION.md`.
- `RAG_GENERATION_BACKEND=extractive` (default): hành vi **identical** Phase 12 — regression `smoke_rag_answer` pass không cần Ollama.
- `RAG_GENERATION_BACKEND=ollama` + profile `llm`: smoke generative trả lời tổng hợp tiếng Việt, ≥1 citation hợp lệ, `generation_mode=generative`.
- Ollama down / timeout: API trả extractive + `fallback_reason=llm_unavailable` (hoặc tương đương), không 500.
- Admin `/status` hiển thị trạng thái LLM.
- Runbook dev + deploy production (RAM/GPU sizing) trong repo.
- Frontend build pass; regression Phase 16 smokes pass.

#### Kiểm Tra Bắt Buộc (Mục Tiêu 8)

```bash
# Không LLM (default CI/dev)
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.smoke_relation_suggestions

# Có LLM (profile llm, sau khi pull model)
docker compose --profile llm exec -T api python -m app.scripts.smoke_rag_generative

WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

#### Mục Tiêu Gợi Ý Cho `TASK_NEXT.md`

1. **Thiết kế generative RAG** — prompt, citation validation, env contract (`solution-architect`, `semantic-search-rag`) → `DOMAIN_MODULE_DECISION.md`.
2. **`LocalLLMService` + settings** — Ollama client, health (`backend-fastapi`).
3. **Docker Compose profile `llm`** — service ollama, volume, resource limits, GPU override optional (`solution-architect`).
4. **`RagAnswerService` generative + fallback** — context builder, validator (`semantic-search-rag`).
5. **API schema + ops LLM status** — mở rộng response `/search/answer`, `/ops/system-status`.
6. **Frontend dashboard** — generation mode badge, fallback UX, loading (`frontend-nuxt`).
7. **Runbook** — `RAG_LLM_RUNBOOK.md`, cập nhật `COMPOSE_RESOURCE_UPLOAD_RUNBOOK.md`, `.env.example`.
8. **Smoke `smoke_rag_generative` + regression + đóng phase** (`project-git-manager`).

---

### Phase 18 - Dòng Hàng Mua Sắm Và Danh Mục Vật Tư MVP

Trạng thái: **đã lập kế hoạch** — chưa bắt đầu (2026-06-07).

Mục tiêu: mở rộng module procurement (Phase 13) với **dòng hàng vật tư** gắn từng `procurement_record` và **danh mục vật tư nhẹ** để autocomplete — phục vụ tra cứu đề xuất/kế hoạch/nghiệm thu theo mặt hàng mà **không** mở tồn kho, phiếu xuất/nhập hay workflow phê duyệt nhiều bước.

Phụ thuộc: Phase 13 (`procurement_records`, `/procurements`, search filter procurement); Phase 14 (onboarding gợi ý procurement); audit/RBAC pattern module hiện có.

Bối cảnh hiện tại:
- `procurement_records` chỉ có metadata cấp hồ sơ (`reference_number`, `estimated_value`, `requesting_unit`, …) — không có bảng con cho từng mặt hàng.
- Phase 13 ghi rõ **không** line items trong MVP; benchmark fixture `procurement_plan` và OCR chunk thường chứa bảng vật tư (tên, đơn vị, số lượng, đơn giá) nhưng chưa được cấu trúc hóa.
- Phòng vật tư cần tra cứu "hồ sơ nào có mặt hàng X" và tổng giá trị theo dòng — chưa cần quản lý tồn thực tế.

#### Quyết Định Kiến Trúc (Chốt Ở Mục Tiêu 1)

| Hạng mục | Quyết định MVP | Lý do |
|----------|----------------|-------|
| Bảng dòng hàng | `procurement_line_items` — FK `procurement_id`, soft delete | Tách khỏi document core; 1 procurement có N dòng |
| Danh mục vật tư | `materials_catalog` — read/write admin, autocomplete user | Tránh nhập trùng tên đơn vị; **không** có `stock_quantity` |
| Liên kết document | Giữ qua `procurement_records.document_id` | Không copy OCR text sang bảng line item |
| Pre-fill OCR | Rule-based tùy chọn (mục tiêu 6) — parse bảng từ chunk | Không LLM; user xác nhận trước khi lưu |
| Search | Filter procurement theo `item_name` / `item_code` (pre-resolve `procurement_id`) | Mirror pattern filter module Phase 11; không đổi Qdrant payload |
| Tồn kho | **Không** | Phase 19+ nếu có nhu cầu thật |

Luồng nghiệp vụ đề xuất:

```text
document searchable + procurement_record
  -> user thêm/sửa/xóa line items (form hoặc import gợi ý OCR)
  -> tổng amount dòng (optional) đối chiếu estimated_value (cảnh báo UI, không rule engine)
  -> list/filter procurement theo mặt hàng
  -> search/RAG vẫn qua document/chunk core (filter procurement_id qua metadata module)
```

#### Phạm Vi Kỹ Thuật

**Thiết kế (`docs/DOMAIN_MODULE_DECISION.md` — mục tiêu 1)**

- Bảng `procurement_line_items`:
  - `procurement_id` (FK, required), `line_number` (int, thứ tự hiển thị).
  - `item_name` (required), `item_code` (optional), `unit` (optional, ví dụ cái/bộ/kg).
  - `quantity` (`Numeric`, default 1), `unit_price` (optional), `amount` (optional — tính `quantity * unit_price` server-side nếu thiếu).
  - `notes` (optional); UUID PK; `created_at`, `updated_at`, `deleted_at`.
  - Index: `(procurement_id, line_number)`, `(item_name)` trigram hoặc `ILIKE` tùy pattern repo hiện có.
- Bảng `materials_catalog` (admin catalog nhẹ):
  - `code`, `name`, `default_unit`, `category` (optional), `is_active`; audit fields + soft delete.
  - Partial unique active trên `code` hoặc `name` — chốt ở mục tiêu 1.
- API contract nested + flat:
  - `GET/POST /api/v1/procurements/{procurement_id}/line-items`
  - `PATCH/DELETE /api/v1/procurement-line-items/{line_item_id}`
  - `GET/POST/PATCH/DELETE /api/v1/materials-catalog` (admin CRUD; user read list active cho autocomplete).
- Audit: `procurement_line_item.created|updated|deleted`, `materials_catalog.*`.
- Quyền: mirror procurement — user CRUD line item trên procurement mình có quyền; admin soft delete catalog.

**Backend (mục tiêu 2–4)**

- Migration Alembic (ví dụ `0017_procurement_line_items`, `0018_materials_catalog` hoặc gộp một file nếu nhỏ).
- `ProcurementLineItemRepository`, `ProcurementLineItemService`, mở rộng `ProcurementService` (validate procurement tồn tại trước khi thêm dòng).
- `MaterialsCatalogRepository`, `MaterialsCatalogService`, router admin.
- Mở rộng `ProcurementRepository.list_procurements()` / `list_document_ids_by_metadata()`: filter `item_name`, `item_code` (join line items active).
- Mở rộng `SearchService` + schema search/RAG: tham số `procurement_item_name`, `procurement_item_code` — pre-resolve `document_id` qua procurement + line items (intersection với filter procurement hiện có).
- Smoke `python -m app.scripts.smoke_procurement_line_items`.

**Frontend (mục tiêu 5)**

- Types `procurement-line-item.ts`, `materials-catalog.ts`; service + composable (`useProcurementLineItems`, `useMaterialsCatalog`).
- Trang/modal chi tiết procurement: DataTable dòng hàng — thêm/sửa/xóa inline hoặc dialog; hiển thị **Tổng cộng** (`sum amount`).
- Autocomplete `item_name` / `unit` từ catalog active (PrimeVue AutoComplete).
- Trang admin `/materials-catalog` hoặc subsection trong `/status`/admin nav — list CRUD catalog (admin only).
- Cảnh báo nhẹ khi `sum(amount)` lệch `estimated_value` > ngưỡng (ví dụ 1%) — Message warn, không chặn lưu.

**Pre-fill rule-based từ OCR (mục tiêu 6 — có kiểm soát)**

- `ProcurementLineItemSuggestionService`: đọc chunk document (ưu tiên `section_role=appendix` hoặc chunk có `is_table`/pattern bảng).
- Heuristic: dòng có ≥3 cột số (STT, tên, SL, ĐVT, đơn giá, thành tiền) — mirror pattern table trong chunk metadata nếu có.
- API read-only: `GET /api/v1/procurements/{procurement_id}/line-item-suggestions` — trả danh sách gợi ý; **không** auto-insert.
- UI: nút **Gợi ý từ OCR** trên form line items → preview → user chọn áp dụng từng dòng hoặc tất cả.

**Kiểm tra (mục tiêu 7–8)**

- Smoke line items: tạo procurement → POST 2–3 dòng → PATCH → DELETE → filter list theo `item_name`.
- Smoke search filter: seed procurement + line item → semantic search với `procurement_item_name` → assert `document_id` đúng.
- Regression: `smoke_procurement_api`, `smoke_search_module_filters`, `smoke_module_onboarding`, `smoke_rag_answer`, `smoke_relation_suggestions`.
- Frontend build pass.

Không làm trong phase này:

- Không `stock_quantity`, phiếu xuất/nhập, tồn tối thiểu, kho vật lý.
- Không workflow trình ký/ phê duyệt nhiều bước, assignee, SLA.
- Không LLM trích xuất bảng; không đổi chunking/Qdrant payload hay re-index hàng loạt.
- Không module nghiệp vụ mới ngoài mở rộng procurement + catalog.
- Không HA Ollama / streaming RAG.

Tiêu chí hoàn thành:

- Quyết định scope ghi trong `docs/DOMAIN_MODULE_DECISION.md` (mục Phase 18).
- User thêm/sửa/xóa ≥3 dòng hàng trên một procurement từ UI trong ≤5 thao tác.
- Admin quản lý catalog vật tư; autocomplete hoạt động khi thêm dòng.
- Filter list procurement và dashboard search theo `item_name` hoạt động với ≥1 fixture smoke.
- (Tùy chọn đạt mục tiêu 6) Gợi ý OCR trả ≥1 dòng hợp lệ trên fixture bảng vật tư; user xác nhận trước khi lưu.
- Smoke line items + regression pass trên Docker Compose.

Mục tiêu gợi ý cho `TASK_NEXT.md`:

1. Thiết kế `procurement_line_items` + `materials_catalog` trong `DOMAIN_MODULE_DECISION.md` (`solution-architect`, `database-designer`).
2. Migration + model + repository line items.
3. Service + API line items + audit + smoke backend cơ bản.
4. Materials catalog — migration, API admin, seed mẫu.
5. Frontend line items UI + tổng cộng + autocomplete catalog (`frontend-nuxt`).
6. (Tùy chọn) `ProcurementLineItemSuggestionService` + API/UI gợi ý OCR (`ocr-pipeline`, `vn-admin-doc-ocr-classifier`).
7. Search/list filter theo mặt hàng + smoke search (`semantic-search-rag`).
8. Regression, frontend build, đóng phase (`project-git-manager`).

---

### Phase 19+ (Dự Kiến, Chưa Lập Chi Tiết)

Hướng ưu tiên sau Phase 18 (chưa chốt thứ tự):

| Hướng | Giá trị | Ghi chú |
|-------|---------|---------|
| Inventory/tồn kho MVP | Cao cho phòng vật tư | Cần nhu cầu nghiệp vụ rõ; phụ thuộc line items Phase 18 |
| Workflow phê duyệt nhiều bước | Trung bình | Rule engine tối thiểu; tránh over-engineering |
| LLM production ops | Trung bình | Tách `OLLAMA_BASE_URL` host riêng, backup model, giám sát latency |
| HA / scale Ollama | Thấp cho MVP on-prem nhỏ | Chỉ khi quy mô user tăng |

---

## Ghi Chú Lập Kế Hoạch

- `TASK_NEXT.md` chỉ chứa checklist phase đang làm; Phase 18 đã mở — thực thi theo 8 mục tiêu ở trên.
- Con trỏ thực thi: `TASK_NEXT.md` → `PROJECT_STATUS.md` → commit sau mỗi mục tiêu (skill `project-git-manager`).
- Ưu tiên MVP và maintainability; mỗi mở rộng module phải có quyết định scope trong `docs/DOMAIN_MODULE_DECISION.md`.
- Mỗi mục tiêu phase khi hoàn thành phải auto commit theo quy tắc trong `TASK_NEXT.md`.
