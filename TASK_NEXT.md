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

Phase trước: Phase 17 hoàn thành ngày 2026-06-07.

Phase hiện tại: **Phase 18 — Dòng hàng mua sắm và danh mục vật tư MVP**.

Mục tiêu tiếp theo: **Mục tiêu 4** — materials catalog (admin) migration, API, seed mẫu.

Regression nhanh trước khi bắt đầu (baseline Phase 17):

```bash
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.smoke_procurement_api
docker compose exec -T api python -m app.scripts.smoke_health_checks
```

---

## Phase 18 — Dòng Hàng Mua Sắm Và Danh Mục Vật Tư MVP

Trạng thái phase: **đang làm** (mục tiêu 1 hoàn thành 2026-06-08).

Phạm vi: mở rộng `procurement_records` với bảng `procurement_line_items` và `materials_catalog` (autocomplete); filter search/list theo mặt hàng; **không** tồn kho, **không** workflow phê duyệt nhiều bước. Chi tiết: `ROADMAP.md` § Phase 18.

### Mục tiêu 1 — Thiết kế scope line items và materials catalog

Trạng thái: **hoàn thành** (2026-06-08).

Skills: `solution-architect`, `database-designer`.

Deliverables:
- Mục **Procurement Line Items (Phase 18)** trong `docs/DOMAIN_MODULE_DECISION.md`: schema, API contract, quyền, audit, ranh giới không làm (no stock, no approval workflow).
- Chốt unique constraint catalog, cách tính `amount`, filter search `procurement_item_name` / `procurement_item_code`.

Tiêu chí chấp nhận:
- Tài liệu thiết kế đủ để implement migration + API mà không cần đoán thêm field.
- Ghi rõ phụ thuộc Phase 13 và không đổi document/chunk core.

Kiểm tra: `git diff --check`.

---

### Mục tiêu 2 — Migration, model và repository line items

Trạng thái: **hoàn thành** (2026-06-08).

Skills: `database-designer`, `backend-fastapi`.

Deliverables:
- Alembic migration bảng `procurement_line_items`.
- Model SQLAlchemy + `ProcurementLineItemRepository` (list/create/update/soft delete theo `procurement_id`).

Tiêu chí chấp nhận:
- Migration chạy được trên stack Compose hiện có.
- Index filter theo `procurement_id` và tra cứu `item_name`.

Kiểm tra:

```bash
docker compose exec -T api alembic upgrade head
PYTHONPATH=apps/api python3 -m py_compile apps/api/app/models/procurement_line_item.py apps/api/app/repositories/procurement_line_item_repository.py
git diff --check
```

---

### Mục tiêu 3 — Service, API line items, audit và smoke backend cơ bản

Trạng thái: **hoàn thành** (2026-06-08).

Skills: `backend-fastapi`.

Deliverables:
- `ProcurementLineItemService`, router nested `GET/POST /procurements/{id}/line-items`, `PATCH/DELETE /procurement-line-items/{id}`.
- Audit events; smoke `apps/api/app/scripts/smoke_procurement_line_items.py` (CRUD cơ bản).

Tiêu chí chấp nhận:
- Smoke pass: tạo procurement → thêm ≥2 dòng → sửa → xóa → GET list đúng thứ tự.
- Quyền mirror procurement hiện có.

Kiểm tra:

```bash
docker compose exec -T api python -m app.scripts.smoke_procurement_line_items
docker compose exec -T api python -m app.scripts.smoke_procurement_api
git diff --check
```

---

### Mục tiêu 4 — Materials catalog (admin) — migration, API, seed mẫu

Trạng thái: **chưa làm** (mục tiêu tiếp theo).

Skills: `database-designer`, `backend-fastapi`.

Deliverables:
- Migration `materials_catalog`; repository/service/router admin CRUD.
- Seed vài mã vật tư mẫu (dev) hoặc script seed trong smoke.
- Endpoint list active cho user (autocomplete).

Tiêu chí chấp nhận:
- Admin CRUD catalog; user đọc list active.
- Soft delete catalog không xóa line item đã lưu (chỉ ẩn khỏi autocomplete).

Kiểm tra:

```bash
docker compose exec -T api alembic upgrade head
docker compose exec -T api python -m app.scripts.smoke_procurement_line_items
git diff --check
```

---

### Mục tiêu 5 — Frontend line items UI, tổng cộng và autocomplete

Trạng thái: **chưa làm**.

Skills: `frontend-nuxt`.

Deliverables:
- Types, service, composable line items + catalog.
- UI dòng hàng trên trang/modal procurement; hiển thị tổng `amount`; cảnh báo nhẹ khi lệch `estimated_value`.
- Trang hoặc section admin quản lý catalog.

Tiêu chí chấp nhận:
- User thêm/sửa/xóa dòng từ UI; autocomplete tên/đơn vị từ catalog.
- Không gọi API trực tiếp trong component.

Kiểm tra:

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

---

### Mục tiêu 6 — (Tùy chọn) Gợi ý dòng hàng từ OCR rule-based

Trạng thái: **chưa làm**.

Skills: `ocr-pipeline`, `vn-admin-doc-ocr-classifier`, `backend-fastapi`.

Deliverables:
- `ProcurementLineItemSuggestionService` + `GET .../line-item-suggestions`.
- UI nút **Gợi ý từ OCR** — preview, user xác nhận trước khi POST line items.

Tiêu chí chấp nhận:
- Fixture bảng vật tư trong chunk trả ≥1 gợi ý hợp lệ; không auto-insert.
- Có thể đánh dấu **bỏ qua mục tiêu 6** nếu heuristic chưa đủ tin cậy — ghi rõ trong `PROJECT_STATUS.md`.

Kiểm tra: smoke mở rộng hoặc unit test parser; regression `check_document_classifier` nếu chạm classifier.

---

### Mục tiêu 7 — Filter list/search theo mặt hàng

Trạng thái: **chưa làm**.

Skills: `semantic-search-rag`, `backend-fastapi`, `frontend-nuxt`.

Deliverables:
- Mở rộng list procurement API + UI filter `item_name`, `item_code`.
- Mở rộng `SearchService` / dashboard filter `procurement_item_name`, `procurement_item_code` (pre-resolve `document_id`).
- Smoke search filter mặt hàng.

Tiêu chí chấp nhận:
- List procurement và semantic search lọc đúng document có line item khớp.
- Không regression filter procurement metadata hiện có (Phase 11).

Kiểm tra:

```bash
docker compose exec -T api python -m app.scripts.smoke_search_module_filters
docker compose exec -T api python -m app.scripts.smoke_procurement_line_items
git diff --check
```

---

### Mục tiêu 8 — Regression, hoàn tất phase

Trạng thái: **chưa làm**.

Skills: `project-git-manager`.

Deliverables:
- Chạy regression suite Phase 17 + procurement.
- Cập nhật `PROJECT_STATUS.md` (đóng Phase 18), `ROADMAP.md` (trạng thái hoàn thành), placeholder Phase 19 trong `TASK_NEXT.md`.

Tiêu chí chấp nhận:
- Toàn bộ smoke bắt buộc pass (xem `ROADMAP.md` § Phase 18).
- Frontend build pass.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_procurement_line_items
docker compose exec -T api python -m app.scripts.smoke_procurement_api
docker compose exec -T api python -m app.scripts.smoke_search_module_filters
docker compose exec -T api python -m app.scripts.smoke_module_onboarding
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.smoke_relation_suggestions
docker compose exec -T api python -m app.scripts.smoke_health_checks
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

Generative RAG (optional): `docs/RAG_LLM_RUNBOOK.md` — không chặn đóng Phase 18.
