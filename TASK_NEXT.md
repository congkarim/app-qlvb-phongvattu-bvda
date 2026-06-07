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

Phase trước: Phase 15 hoàn thành ngày 2026-06-07.

Phase hiện tại: Phase 16 - Gợi Ý Liên Kết Document Từ Nội Dung (Rule-Based).

Mục tiêu tiếp theo: Phase 16 / Mục Tiêu 3 - API `relation-suggestions` Và Schema Response.

Điều kiện chuyển sang mục tiêu kế tiếp:
- Mục tiêu hiện tại pass tiêu chí chấp nhận.
- Kiểm tra bắt buộc đã chạy hoặc lý do chưa chạy được đã ghi trong `PROJECT_STATUS.md`.
- `ROADMAP.md` đã được đọc lại sau khi hoàn thành mục tiêu.
- Đã auto commit thay đổi liên quan.

---

## Phase 16 - Gợi Ý Liên Kết Document Từ Nội Dung (Rule-Based)

Trạng thái: đang làm (bắt đầu 2026-06-07).

Mục tiêu phase: gợi ý quan hệ giữa hai document searchable bằng heuristic OCR/chunk; user xác nhận trước khi tạo `document_relations`.

Điều kiện hoàn thành phase:
- Heuristic + mapping ghi trong `docs/DOMAIN_MODULE_DECISION.md`.
- Fixture smoke (CV tham chiếu QĐ): ≥1 gợi ý đúng `target_document_id` và `relation_type` hợp lý.
- User tạo liên kết từ gợi ý trong ≤2 thao tác UI.
- Smoke `smoke_relation_suggestions` + regression Phase 15 pass trên Docker Compose.

Không làm trong phase này:
- Không LLM / embedding cross-document.
- Không auto-create relation im lặng (worker hoặc API).
- Không đổi Qdrant payload, re-index, inventory, workflow phê duyệt.

### Mục Tiêu 1 - Thiết Kế Heuristic Và DTO Gợi Ý Liên Kết

Trạng thái: hoàn thành (2026-06-07).

Skill bắt buộc: `solution-architect`, `vn-admin-doc-ocr-classifier`.

Mục tiêu:
- Chốt heuristic trích tham chiếu từ chunk và chiến lược match document đích trước khi code.

Phạm vi:
- Đọc `DocumentClassifierService._extract_document_number_and_symbol()`, chunk anchors (`ocr_chunking/anchors.py`), `docs/DOMAIN_MODULE_DECISION.md` mục Document Relations (Phase 15).
- Ghi mục mới **Relation Suggestions** trong `DOMAIN_MODULE_DECISION.md`: regex, anchor phrase → `relation_type`, normalize `document_number`, DTO (`target_document_id`, `relation_type`, `confidence`, `matched_reference`, `source_chunk_id`, `reasons[]`), ngưỡng `high`/`review`.
- Ghi khảo sát trong `PROJECT_STATUS.md`.
- Không code backend/frontend trong mục tiêu này.

Tiêu chí chấp nhận:
- Tài liệu đủ rõ để implement service ở mục tiêu 2.
- Ghi rõ loại trừ: self-link, relation active trùng triple, target không searchable.

Kiểm tra bắt buộc:

```bash
git diff --check
```

### Mục Tiêu 2 - DocumentRelationSuggestionService Và Lookup Document

Trạng thái: hoàn thành (2026-06-07).

Skill bắt buộc: `backend-fastapi`, `vn-admin-doc-ocr-classifier`.

Mục tiêu:
- Service rule-based đọc chunk nguồn, trích reference candidates, match `documents` theo `document_number`.

Phạm vi:
- `DocumentRelationSuggestionService.suggest_relations(document_id)` theo thiết kế mục tiêu 1.
- Đọc chunk qua `DocumentRepository` (ưu tiên trang 1–2, `section_role` article/unknown).
- Lookup đích: query indexed `document_number` (normalize giống classifier); dedupe `(target_document_id, relation_type)`; cap tối đa 8 gợi ý.
- Loại trừ relations đã tồn tại active; không ghi `document_relations`.
- (Tùy chọn) helper normalize số văn bản tái dùng logic classifier nếu có thể extract shared.

Tiêu chí chấp nhận:
- Unit hoặc smoke repo-level: CV chunk chứa số QĐ → trả đúng `target_document_id`.
- Document không searchable → service trả rỗng hoặc 404 ở layer API (mục tiêu 3).

Kiểm tra bắt buộc:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile \
  apps/api/app/services/document_relation_suggestion_service.py
git diff --check
```

### Mục Tiêu 3 - API `relation-suggestions` Và Schema Response

Trạng thái: chưa làm (tiếp theo).

Skill bắt buộc: `backend-fastapi`, `project-git-manager`.

Mục tiêu:
- Endpoint read-only trả danh sách gợi ý; tạo liên kết vẫn qua POST relations hiện có.

Phạm vi:
- Schema Pydantic `RelationSuggestionRead`, `RelationSuggestionsResponse`.
- `GET /api/v1/documents/{document_id}/relation-suggestions` trên router documents (hoặc document_relations nếu nhất quán).
- Chỉ document searchable; user đăng nhập; `404` document không tồn tại.
- Audit tùy chọn: `document.relation_suggested` khi GET (metadata `candidate_count`) — chỉ nếu không làm chậm smoke.

Tiêu chí chấp nhận:
- API trả gợi ý đúng fixture thiết kế; không side-effect tạo relation.
- `py_compile` router + schema pass.

Kiểm tra bắt buộc:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile \
  apps/api/app/schemas/document_relation.py \
  apps/api/app/routers/documents.py
docker compose exec -T api python -m app.scripts.smoke_document_relations
git diff --check
```

### Mục Tiêu 4 - Frontend Gợi Ý Trong DocumentRelationsCard

Trạng thái: chưa làm.

Skill bắt buộc: `frontend-nuxt`, `project-git-manager`.

Mục tiêu:
- Subsection **Gợi ý liên kết** trên document detail; không gọi API trực tiếp trong component.

Phạm vi:
- Types `RelationSuggestion` trong `document-relation.ts` (hoặc `types/onboarding.ts` nếu gọn).
- `document.service.ts` / `document-relation.service.ts`: `getRelationSuggestions(documentId)`.
- Composable `useDocumentRelationSuggestions.ts`.
- Mở rộng `DocumentRelationsCard.vue`: load gợi ý khi mount; hiển thị nhãn quan hệ, document đích, quote chunk; phân style `high` vs `review`.

Tiêu chí chấp nhận:
- Document detail có danh sách gợi ý khi API trả dữ liệu.
- Form thêm liên kết thủ công vẫn hoạt động.

Kiểm tra bắt buộc:

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

### Mục Tiêu 5 - Apply / Dismiss UX Và Refresh Relations

Trạng thái: chưa làm.

Skill bắt buộc: `frontend-nuxt`, `project-git-manager`.

Mục tiêu:
- User tạo liên kết từ gợi ý hoặc bỏ qua tạm thời; danh sách outgoing/incoming cập nhật ngay.

Phạm vi:
- Nút **Tạo liên kết** → gọi POST relations hiện có (`useDocumentRelations` / emit `create`).
- Nút **Bỏ qua** → dismiss client-side (session/ref Set theo suggestion key); không gọi API.
- Sau apply thành công: refresh relations + ẩn gợi ý đã dùng; hiển thị lỗi POST nếu 409 trùng.

Tiêu chí chấp nhận:
- ≤2 thao tác: Tạo liên kết → thấy trong outgoing.
- Dismiss không hiện lại gợi ý đó trong cùng phiên trang.

Kiểm tra bắt buộc:

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

### Mục Tiêu 6 - Smoke End-to-End, Regression Và Hoàn Tất Phase

Trạng thái: chưa làm.

Skill bắt buộc: `backend-fastapi`, `frontend-nuxt`, `project-git-manager`.

Mục tiêu:
- Smoke tái chạy được; đóng Phase 16 trong tài liệu trạng thái.

Phạm vi:
- Script `python -m app.scripts.smoke_relation_suggestions`: seed QĐ + CV (CV text căn cứ số QĐ) → GET suggestions → POST relation → assert gợi ý biến mất / outgoing có 1.
- Regression: `smoke_document_relations`, `smoke_module_onboarding`, `smoke_search_module_filters`, `smoke_rag_answer`, `check_document_classifier` (hoặc subset đã dùng Phase 15).
- Cập nhật `docs/DOMAIN_MODULE_DECISION.md` (mục đã triển khai), `ROADMAP.md` Phase 16 hoàn thành, `PROJECT_STATUS.md`.
- Thay `TASK_NEXT.md` bằng placeholder Phase 17 hoặc “chưa lập” theo `ROADMAP.md`.

Tiêu chí chấp nhận:
- Tiêu chí hoàn thành Phase 16 trong `ROADMAP.md` đạt.
- Auto commit sau khi pass kiểm tra.

Kiểm tra bắt buộc:

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
