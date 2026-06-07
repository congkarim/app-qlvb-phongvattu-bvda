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

Phase trước: Phase 12 hoàn thành ngày 2026-06-07.

Phase hiện tại: Phase 13 - Module Đề Xuất / Kế Hoạch Mua Sắm MVP.

Mục tiêu tiếp theo: Phase 13 / Mục Tiêu 2 - Migration Và Model procurement_records.

Điều kiện chuyển sang mục tiêu kế tiếp:
- Mục tiêu hiện tại pass tiêu chí chấp nhận.
- Kiểm tra bắt buộc đã chạy hoặc lý do chưa chạy được đã ghi trong `PROJECT_STATUS.md`.
- `ROADMAP.md` đã được đọc lại sau khi hoàn thành mục tiêu.
- Đã auto commit thay đổi liên quan.

---

## Phase 13 - Module Đề Xuất / Kế Hoạch Mua Sắm MVP

Trạng thái: đang làm (bắt đầu 2026-06-07).

Mục tiêu phase: mở module nghiệp vụ thứ tư — sổ đề xuất mua sắm và kế hoạch vật tư — theo pattern metadata 1-1 với document core.

Điều kiện hoàn thành phase:
- Có quyết định scope trong `docs/DOMAIN_MODULE_DECISION.md`.
- Schema + API + UI `/procurements` + liên kết document detail hai chiều + smoke tái chạy được.
- Ít nhất một luồng: upload document → tạo metadata procurement → list/filter → search/RAG không regression các module khác.

Không làm trong phase này:
- Không quản lý tồn kho, phiếu xuất/nhập, tồn tối thiểu.
- Không workflow trình ký nhiều bước, SLA, assignee.
- Không bảng line items chi tiết (trừ khi có yêu cầu rõ sau MVP).
- Không LLM trích xuất metadata mới.

### Mục Tiêu 1 - Thiết Kế Module Procurement Trong DOMAIN_MODULE_DECISION.md

Trạng thái: hoàn thành (2026-06-07).

Skill bắt buộc: `solution-architect`, `database-designer`, `project-git-manager`.

Mục tiêu:
- Chốt tên kỹ thuật, metadata, status, map `business_type` và pattern 1-1 document.

Phạm vi:
- Cập nhật `docs/DOMAIN_MODULE_DECISION.md` mục procurement.
- Tham chiếu pattern contract/dispatch/decision Phase 4–10.
- Không code trong mục tiêu này.

Tiêu chí chấp nhận:
- Có spec đủ rõ để implement migration/API/UI mục tiêu 2–5.

Kiểm tra bắt buộc:

```bash
git diff --check
```

### Mục Tiêu 2 - Migration Và Model procurement_records

Trạng thái: chưa làm (tiếp theo).

Skill bắt buộc: `database-designer`, `backend-fastapi`, `project-git-manager`.

Mục tiêu:
- Alembic migration `procurement_records` với UUID PK, audit fields, soft delete, partial unique active `document_id`.

Phạm vi:
- Model SQLAlchemy, index filter MVP.
- Không API/router trong mục tiêu này.

Tiêu chí chấp nhận:
- `alembic upgrade head` pass trên DB dev; schema khớp thiết kế mục tiêu 1.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api alembic upgrade head
git diff --check
```

### Mục Tiêu 3 - API CRUD Và Smoke Backend

Trạng thái: chưa làm.

Skill bắt buộc: `backend-fastapi`, `project-git-manager`.

Mục tiêu:
- Repository, service, router `/api/v1/procurements` + `by-document/{document_id}`; audit và RBAC giống module trước.

Phạm vi:
- Script `python -m app.scripts.smoke_procurement_api`.
- Không frontend trong mục tiêu này.

Tiêu chí chấp nhận:
- Smoke procurement API pass create/list/filter/update/soft-delete.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_procurement_api
git diff --check
```

### Mục Tiêu 4 - Frontend /procurements

Trạng thái: chưa làm.

Skill bắt buộc: `frontend-nuxt`, `project-git-manager`.

Mục tiêu:
- Types, service, composable, page list/filter/form CRUD `/procurements`.

Phạm vi:
- Pattern giống `/contracts`, `/dispatches`, `/decisions`.
- Nav item app shell.

Tiêu chí chấp nhận:
- User CRUD procurement metadata; admin soft delete; form validation và loading/error state.

Kiểm tra bắt buộc:

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

### Mục Tiêu 5 - Liên Kết Document Detail Hai Chiều

Trạng thái: chưa làm.

Skill bắt buộc: `frontend-nuxt`, `backend-fastapi`, `project-git-manager`.

Mục tiêu:
- Card procurement trên `/documents/[id]`; link từ `/procurements` sang document; preset search dashboard (tạm `business_type` + filter nếu chưa có search filter procurement).

Phạm vi:
- Hai chiều document ↔ procurement record active.
- Không search filter procurement đầy đủ (để mục tiêu 6 tùy chọn).

Tiêu chí chấp nhận:
- Từ document detail mở/sửa procurement và ngược lại trong ≥1 fixture smoke/manual.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_procurement_api
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

### Mục Tiêu 6 - (Tùy Chọn) Search Filter Procurement Và Hoàn Tất Phase

Trạng thái: chưa làm.

Skill bắt buộc: `semantic-search-rag`, `project-git-manager`.

Mục tiêu:
- Filter procurement trên search/RAG; benchmark fixture; hoàn tất Phase 13 và cập nhật tài liệu.

Phạm vi:
- `SearchService` + dashboard filter theo pattern Phase 11.
- Smoke regression: `smoke_procurement_api`, `smoke_search_module_filters`, `smoke_rag_answer`, `smoke_api_workflows`.
- Cập nhật `ROADMAP.md`, `PROJECT_STATUS.md`, thay `TASK_NEXT.md` bằng phase kế tiếp hoặc ghi "chưa lập phase 14".

Tiêu chí chấp nhận:
- Phase 13 đạt tiêu chí hoàn thành trong `ROADMAP.md`.
- Auto commit sau khi pass kiểm tra.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_procurement_api
docker compose exec -T api python -m app.scripts.smoke_search_module_filters
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.smoke_api_workflows
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```
