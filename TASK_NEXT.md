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

Phase trước: Phase 11 hoàn thành ngày 2026-06-07.

Phase hiện tại: Phase 12 - RAG Citation UX Và Search Enrichment.

Mục tiêu tiếp theo: Phase 12 / Mục Tiêu 2 - Implement `#chunk-{id}` Document Detail + Highlight.

Điều kiện chuyển sang mục tiêu kế tiếp:
- Mục tiêu hiện tại pass tiêu chí chấp nhận.
- Kiểm tra bắt buộc đã chạy hoặc lý do chưa chạy được đã ghi trong `PROJECT_STATUS.md`.
- `ROADMAP.md` đã được đọc lại sau khi hoàn thành mục tiêu.
- Đã auto commit thay đổi liên quan.

---

## Phase 12 - RAG Citation UX Và Search Enrichment

Trạng thái: đang làm (bắt đầu 2026-06-07).

Mục tiêu phase: cải thiện truy vết nguồn từ search/RAG tới đúng đoạn văn bản trên document detail; làm giàu UX kết quả tìm kiếm với metadata module.

Điều kiện hoàn thành phase:
- Từ dashboard RAG, click citation mở document detail và scroll tới đúng chunk trong ≥1 fixture smoke.
- Search result có nút/badge metadata module và (tùy chọn) "Mở đoạn" deep link chunk.
- Regression smoke RAG + semantic search + filter module pass.

Không làm trong phase này:
- Không LLM local (Ollama, vLLM, v.v.).
- Không PDF viewer page-level scroll (chỉ chunk list text).
- Không thay đổi chunking/OCR pipeline.

### Mục Tiêu 1 - Thiết Kế Anchor/Scroll Chunk Trên Document Detail

Trạng thái: hoàn thành (2026-06-07).

Skill bắt buộc: `frontend-nuxt`, `solution-architect`.

Mục tiêu:
- Khảo sát chunk list trên `/documents/[id]` và chốt contract anchor `#chunk-{chunk_id}`, highlight và fallback.

Phạm vi:
- Đọc `documents/[...id].vue`, DOM id chunk card, hash routing Nuxt.
- Ghi quyết định trong `PROJECT_STATUS.md` (selector, highlight class, timeout scroll).
- Không code trong mục tiêu này.

Tiêu chí chấp nhận:
- Có spec đủ rõ để implement mục tiêu 2–3.

Kiểm tra bắt buộc:

```bash
git diff --check
```

### Mục Tiêu 2 - Implement `#chunk-{id}` Document Detail + Highlight

Trạng thái: chưa làm (tiếp theo).

Skill bắt buộc: `frontend-nuxt`, `project-git-manager`.

Mục tiêu:
- Document detail scroll tới chunk khi URL có hash `#chunk-{chunk_id}`; highlight ngắn.

Phạm vi:
- `id="chunk-{id}"` trên chunk card; `onMounted` + watch hash; class ring/border highlight.
- Không animation phức tạp.

Tiêu chí chấp nhận:
- Mở `/documents/{id}#chunk-{chunk_id}` scroll tới đúng chunk trong manual/smoke checklist.

Kiểm tra bắt buộc:

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

### Mục Tiêu 3 - Cập Nhật RAG Citation URL Và Panel

Trạng thái: chưa làm.

Skill bắt buộc: `frontend-nuxt`, `semantic-search-rag`, `project-git-manager`.

Mục tiêu:
- RAG citation link dạng `/documents/{document_id}#chunk-{chunk_id}`; fallback an toàn khi chunk không còn.

Phạm vi:
- `RagAnswerPanel.vue`; giữ extractive logic backend.
- Mở rộng `smoke_rag_answer` hoặc checklist: citation URL chứa `chunk_id`.

Tiêu chí chấp nhận:
- Click citation từ dashboard RAG mở document detail với hash chunk.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_rag_answer
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

### Mục Tiêu 4 - Search Result Badges Và Nút "Mở Đoạn"

Trạng thái: chưa làm.

Skill bắt buộc: `frontend-nuxt`, `project-git-manager`.

Mục tiêu:
- Dashboard search result: badge metadata module và nút "Mở đoạn" deep link chunk.

Phạm vi:
- `dashboard.vue` kết quả semantic search; tái dùng hash contract mục tiêu 2.
- Contract/dispatch/decision badge khi có enrich metadata.

Tiêu chí chấp nhận:
- User click "Mở đoạn" từ search result mở đúng chunk trên document detail.

Kiểm tra bắt buộc:

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

### Mục Tiêu 5 - Tin Chỉnh Extractive Answer, Smoke Và Hoàn Tất Phase

Trạng thái: chưa làm.

Skill bắt buộc: `semantic-search-rag`, `project-git-manager`.

Mục tiêu:
- (Tùy chọn) cải thiện ghép câu extractive; hoàn tất Phase 12 và cập nhật tài liệu.

Phạm vi:
- `RagAnswerService._compose_answer` nếu cần tinh chỉnh nhẹ.
- Smoke/benchmark regression: `smoke_rag_answer`, `smoke_search_module_filters`, `smoke_api_workflows`.
- Cập nhật `ROADMAP.md`, `PROJECT_STATUS.md`, thay `TASK_NEXT.md` bằng checklist Phase 13.

Tiêu chí chấp nhận:
- Phase 12 đạt tiêu chí hoàn thành trong `ROADMAP.md`.
- Auto commit sau khi pass kiểm tra.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.smoke_search_module_filters
docker compose exec -T api python -m app.scripts.smoke_api_workflows
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```
