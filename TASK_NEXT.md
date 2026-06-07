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

Phase trước: Phase 14 hoàn thành ngày 2026-06-07.

Phase hiện tại: Phase 15 - Liên Kết Chéo Document (`document_relations`).

Mục tiêu tiếp theo: Phase 15 / Mục Tiêu 6 - Smoke End-to-End Và Đóng Phase 15.

Điều kiện chuyển sang mục tiêu kế tiếp:
- Mục tiêu hiện tại pass tiêu chí chấp nhận.
- Kiểm tra bắt buộc đã chạy hoặc lý do chưa chạy được đã ghi trong `PROJECT_STATUS.md`.
- `ROADMAP.md` đã được đọc lại sau khi hoàn thành mục tiêu.
- Đã auto commit thay đổi liên quan.

---

## Phase 15 - Liên Kết Chéo Document (`document_relations`)

Trạng thái: đang thực thi (mục tiêu 1–5 xong; tiếp mục tiêu 6 đóng phase).

Mục tiêu phase: quan hệ có hướng giữa hai document độc lập (tham chiếu, phụ lục của, triển khai, liên quan); tra cứu incoming/outgoing từ document detail; tạo/xóa thủ công, không auto từ OCR.

Điều kiện hoàn thành phase:
- Có quyết định scope trong `docs/DOMAIN_MODULE_DECISION.md`.
- API relations + UI document detail + smoke tái chạy được.
- Ít nhất một luồng: tạo liên kết A→B → xem hai chiều → xóa → regression pass.

Không làm trong phase này:
- Không LLM/rule auto-trích quan hệ từ chunk.
- Không đồ thị visualization, workflow phê duyệt chuỗi.
- Không đổi Qdrant/chunk pipeline, không module nghiệp vụ mới.
- Không merge/split document.

### Mục Tiêu 1 - Thiết Kế `document_relations` Trong DOMAIN_MODULE_DECISION

Trạng thái: hoàn thành (2026-06-07) — spec đã ghi khi lập phase.

Skill bắt buộc: `solution-architect`, `database-designer`, `project-git-manager`.

Mục tiêu:
- Chốt schema, `relation_type`, API shape, UX document detail/list, smoke plan.

Phạm vi:
- Cập nhật `docs/DOMAIN_MODULE_DECISION.md` mục Document Relations (Phase 15).
- Tham chiếu `document_files`, chunk `section_role=appendix`, document detail hiện có.

Tiêu chí chấp nhận:
- Spec đủ rõ để implement mục tiêu 2–6.
- Ghi rõ phân biệt appendix trong chunk vs relation chéo document.

Kiểm tra bắt buộc:

```bash
git diff --check
```

### Mục Tiêu 2 - Migration, Model Và Repository

Trạng thái: hoàn thành (2026-06-07).

Skill bắt buộc: `database-designer`, `backend-fastapi`, `project-git-manager`.

Mục tiêu:
- Bảng `document_relations` Alembic `0016`, model SQLAlchemy, repository query incoming/outgoing.

Phạm vi:
- Partial unique active, index, soft delete, guard self-link ở service/repository.

Tiêu chí chấp nhận:
- `alembic upgrade head` pass; repository list/create/soft-delete unit-level hoặc smoke nhỏ.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api alembic upgrade head
git diff --check
```

### Mục Tiêu 3 - DocumentRelationService, API Và Smoke Backend

Trạng thái: hoàn thành (2026-06-07).

Skill bắt buộc: `backend-fastapi`, `project-git-manager`.

Mục tiêu:
- `GET/POST /documents/{id}/relations`, `DELETE /document-relations/{id}`, audit, `smoke_document_relations.py`.

Phạm vi:
- Router → service → repository; RBAC user tạo/xem, xóa creator hoặc admin.

Tiêu chí chấp nhận:
- Smoke tạo/đọc/xóa/409 trùng; `smoke_api_workflows` regression pass.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_document_relations
docker compose exec -T api python -m app.scripts.smoke_api_workflows
git diff --check
```

### Mục Tiêu 4 - Frontend Card Liên Kết Trên Document Detail

Trạng thái: hoàn thành (2026-06-07).

Skill bắt buộc: `frontend-nuxt`, `project-git-manager`.

Mục tiêu:
- Card **Văn bản liên quan** trên `/documents/[id]`; form thêm liên kết; xóa có confirm.

Phạm vi:
- `useDocumentRelations`, service, component tái sử dụng; pattern `page -> composable -> service -> API`.

Tiêu chí chấp nhận:
- User thêm liên kết và mở document đích trong ≤3 thao tác từ detail.

Kiểm tra bắt buộc:

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

### Mục Tiêu 5 - Document List Badge/Filter Liên Kết (Tùy Chọn Nhẹ)

Trạng thái: hoàn thành (2026-06-07).

Skill bắt buộc: `frontend-nuxt`, `backend-fastapi`, `project-git-manager`.

Mục tiêu:
- `relation_count` hoặc filter `has_relations=true` trên list documents; badge trên table.

Phạm vi:
- Mở rộng list API/response nếu cần; không regression pagination.

Tiêu chí chấp nhận:
- Document có relation active hiển thị badge hoặc lọc được qua API.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_documents_pagination
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

### Mục Tiêu 6 - Smoke End-to-End Và Đóng Phase 15

Trạng thái: chưa làm (tiếp theo).

Skill bắt buộc: `solution-architect`, `project-git-manager`.

Mục tiêu:
- Regression toàn phase; cập nhật `ROADMAP.md`, `PROJECT_STATUS.md`; đóng Phase 15.

Phạm vi:
- Tái chạy smokes Phase 14 + relations; ghi nhận hoàn thành phase.

Tiêu chí chấp nhận:
- Tiêu chí hoàn thành Phase 15 trong `ROADMAP.md` đạt; auto commit.

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
