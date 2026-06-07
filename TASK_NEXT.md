# Kế Hoạch Task Tiếp Theo

Cập nhật lần cuối: 2026-06-07

Tài liệu này là **checklist thực thi của phase đang làm**, bám theo `ROADMAP.md`. Khi người dùng nói `thực hiện TASK_NEXT.md`, agent phải bắt đầu từ mục đầu tiên có trạng thái `chưa làm` hoặc `đang làm`.

Lịch sử phase đã hoàn thành, kết quả khảo sát và log kiểm tra nằm trong `PROJECT_STATUS.md` và `ROADMAP.md` (không lưu lại trong file này).

## Quy Tắc Thực Thi Bắt Buộc

- Trước khi bắt đầu bất kỳ mục tiêu nào: đọc lại `ROADMAP.md`, `PROJECT_STATUS.md` và `TASK_NEXT.md`.
- Chỉ làm một mục tiêu nhỏ tại một thời điểm.
- Xong mục tiêu nào phải kiểm tra tiêu chí chấp nhận, cập nhật `PROJECT_STATUS.md` và `TASK_NEXT.md` (trạng thái mục tiêu, kết quả khảo sát nếu có).
- **Auto commit:** sau khi mục tiêu pass tiêu chí chấp nhận và kiểm tra bắt buộc đã chạy (hoặc lý do chưa chạy được đã ghi rõ), bắt buộc commit bằng skill `project-git-manager`; không chờ user yêu cầu riêng.
- Sau khi xong từng mục tiêu: đọc lại `ROADMAP.md` để xác nhận ưu tiên còn đúng.
- Sau khi xong một phase: đọc lại `ROADMAP.md`, ghi nhận phase hoàn thành trong `PROJECT_STATUS.md`, **thay nội dung `TASK_NEXT.md` bằng checklist phase kế tiếp**, commit, rồi mới mở khóa phase sau.
- Giữ đúng stack cố định và kiến trúc:
  - Backend: `router -> service -> repository`.
  - Frontend: `page -> composable -> service -> API`.
- Trước mỗi mục tiêu: đọc skill kỹ thuật ghi trong mục tiêu (nếu có) và `AGENTS.md`.

## Con Trỏ Hiện Tại

Phase trước: Phase 10 hoàn thành ngày 2026-06-07.

Phase hiện tại: Phase 11 - Search Filter Metadata Dispatch Và Decision.

Mục tiêu tiếp theo: Phase 11 / Mục Tiêu 3 - SearchService, Schema, Router Và Smoke Backend.

Điều kiện chuyển sang mục tiêu kế tiếp:
- Mục tiêu hiện tại pass tiêu chí chấp nhận.
- Kiểm tra bắt buộc đã chạy hoặc lý do chưa chạy được đã ghi trong `PROJECT_STATUS.md`.
- `ROADMAP.md` đã được đọc lại sau khi hoàn thành mục tiêu.
- Đã auto commit thay đổi liên quan.

---

## Phase 11 - Search Filter Metadata Dispatch Và Decision

Trạng thái: đang làm (bắt đầu 2026-06-07).

Mục tiêu phase: hoàn thiện semantic search và RAG trên dashboard theo metadata module công văn và quyết định/thông báo, đồng bộ pattern filter hợp đồng (Phase 7).

Điều kiện hoàn thành phase:
- Dashboard search lọc được theo `dispatch_type` + `dispatch_status` và `decision_kind` + `decision_status` (cùng ít nhất một trong `document_number` / `issuing_agency`).
- RAG dashboard dùng chung bộ filter; smoke/benchmark tái chạy được trên Docker Compose.
- Preset search từ `/dispatches` và `/decisions` truyền filter module qua route query.
- Không regression search/RAG contract filter và upload/OCR/review workflow.

Không làm trong phase này:
- Không sửa Qdrant payload hay re-index chunk.
- Không LLM/generator; RAG vẫn extractive.
- Không deep-link citation `#chunk-{id}` (Phase 12).
- Không module procurement mới.

### Mục Tiêu 1 - Khảo Sát Contract Filter Và Thiết Kế Tham Số Dispatch/Decision

Trạng thái: hoàn thành (2026-06-07).

Skill bắt buộc: `solution-architect`, `semantic-search-rag`.

Mục tiêu:
- Khảo sát pattern contract filter hiện có (`SearchService`, `ContractRepository`, dashboard) và chốt danh sách tham số API/UI cho dispatch và decision trước khi code.

Phạm vi:
- Đọc `SearchService._resolve_contract_document_ids()`, `SemanticSearchRequest`, `RagAnswerService`, `dashboard.vue`, preset search từ `/contracts`.
- Đề xuất tên field API (dispatch/decision prefix vs tái dùng `document_number` khi `business_type` khớp), quy tắc giao `document_id` khi nhiều nhóm filter module cùng lúc.
- Ghi khảo sát và quyết định tham số trong `PROJECT_STATUS.md`; cập nhật `docs/DOMAIN_MODULE_DECISION.md` mục thiết kế search filter (draft).
- Không code backend/frontend trong mục tiêu này.

Tiêu chí chấp nhận:
- Có bảng tham số filter dispatch/decision đủ rõ để triển khai repository ở mục tiêu 2.
- Ghi rõ không sửa Qdrant payload; pre-resolve `document_id` từ PostgreSQL như contract.

Kiểm tra bắt buộc:

```bash
git diff --check
```

### Mục Tiêu 2 - Repository `list_document_ids_by_metadata` Dispatch Và Decision

Trạng thái: hoàn thành (2026-06-07).

Skill bắt buộc: `backend-fastapi`, `database-designer`.

Mục tiêu:
- Thêm helper repository mirror `ContractRepository.list_document_ids_by_metadata()` cho `dispatch_records` và `decision_records`.

Phạm vi:
- `DispatchRepository.list_document_ids_by_metadata()`: filter `dispatch_type`, `document_number`, `issuing_agency`, `status`.
- `DecisionRepository.list_document_ids_by_metadata()`: filter `decision_kind`, `document_number`, `issuing_agency`, `status`, `effective_from`, `effective_to`.
- Chỉ query bản ghi active (`deleted_at IS NULL`); trả list `document_id` string.

Tiêu chí chấp nhận:
- Method hoạt động độc lập; filter rỗng → không giới hạn (caller quyết định).
- Logic filter khớp list API module tương ứng.

Kiểm tra bắt buộc:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile \
  apps/api/app/repositories/dispatch_repository.py \
  apps/api/app/repositories/decision_repository.py
git diff --check
```

### Mục Tiêu 3 - SearchService, Schema, Router Và Smoke Backend

Trạng thái: chưa làm (tiếp theo).

Skill bắt buộc: `backend-fastapi`, `semantic-search-rag`, `project-git-manager`.

Mục tiêu:
- Mở rộng semantic search và RAG answer nhận filter dispatch/decision; enrich kết quả metadata module.

Phạm vi:
- `SemanticSearchRequest`, `RagAnswerRequest`, `SemanticSearchResult`: thêm field dispatch/decision theo thiết kế mục tiêu 1.
- `SearchService`: `_resolve_dispatch_document_ids()`, `_resolve_decision_document_ids()`, intersection khi nhiều nhóm filter; `_attach_dispatch_metadata()`, `_attach_decision_metadata()`.
- Cập nhật `search.py` router và `RagAnswerService` / `SearchBackend` protocol.
- Smoke script mới hoặc mở rộng benchmark: seed dispatch/decision + assert filter `document_id` đúng; contract filter không regression.

Tiêu chí chấp nhận:
- `POST /search/semantic` và `POST /search/answer` lọc theo metadata dispatch/decision.
- Kết quả enrich `dispatch_id` / `decision_id` và trường hiển thị tối thiểu khi có bản ghi active.
- Smoke backend pass trên Docker Compose.

Kiểm tra bắt buộc:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile \
  apps/api/app/schemas/search.py \
  apps/api/app/services/search_service.py \
  apps/api/app/services/rag_answer_service.py \
  apps/api/app/routers/search.py
docker compose exec -T api python -m app.scripts.smoke_dispatch_api
docker compose exec -T api python -m app.scripts.smoke_decision_api
# smoke search filter dispatch/decision (script mới hoặc benchmark mở rộng)
git diff --check
```

### Mục Tiêu 4 - Frontend Dashboard Filter Và RAG

Trạng thái: chưa làm.

Skill bắt buộc: `frontend-nuxt`, `project-git-manager`.

Mục tiêu:
- Dashboard semantic search và RAG panel hỗ trợ filter dispatch/decision; UI có điều kiện theo `business_type`.

Phạm vi:
- Mở rộng `SemanticSearchFilters`, `RagAnswerFilters`, `normalizeSearchPayload()` trong `search.service.ts`.
- `dashboard.vue`: nhóm filter dispatch khi `business_type` là `incoming_dispatch`/`outgoing_dispatch`; nhóm decision khi `business_type` là `decision`.
- `RagAnswerPanel` / `useRagAnswer` truyền filter mới; giữ `ragFilterChangedHint`.
- Không gọi API trực tiếp trong component.

Tiêu chí chấp nhận:
- User chọn business type dispatch/decision và lọc search/RAG theo metadata module.
- Contract filter UI vẫn hoạt động như trước.

Kiểm tra bắt buộc:

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

### Mục Tiêu 5 - Preset Module Pages, Smoke End-to-End Và Hoàn Tất Phase

Trạng thái: chưa làm.

Skill bắt buộc: `frontend-nuxt`, `semantic-search-rag`, `project-git-manager`.

Mục tiêu:
- Preset search từ `/dispatches` và `/decisions`; hoàn tất Phase 11 và cập nhật tài liệu trạng thái.

Phạm vi:
- Nút "Search trong văn bản" trên `/dispatches`, `/decisions` truyền query + filter module qua route dashboard (pattern `/contracts`).
- `dashboard.vue` đọc route query preset filter dispatch/decision khi mount.
- Cập nhật `docs/DOMAIN_MODULE_DECISION.md` mục "Search filter đã triển khai".
- Cập nhật `ROADMAP.md` (Phase 11 hoàn thành), `PROJECT_STATUS.md`, thay `TASK_NEXT.md` bằng checklist Phase 12.
- Smoke end-to-end: dispatch/decision filter → semantic search + RAG không regression contract.

Tiêu chí chấp nhận:
- Drill-down từ module page mở dashboard với filter preset đúng.
- Phase 11 đạt tiêu chí hoàn thành trong `ROADMAP.md`.
- Auto commit sau khi pass kiểm tra.

Kiểm tra bắt buộc:

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
docker compose exec -T api python -m app.scripts.smoke_rag_answer
# smoke/benchmark search filter dispatch/decision
git diff --check
```
