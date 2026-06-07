# Kế Hoạch Task Tiếp Theo

Cập nhật lần cuối: 2026-06-06

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

Phase trước: Phase 9 hoàn thành ngày 2026-06-06.

Phase hiện tại: Phase 10 - Module Quyết Định Và Thông Báo.

Mục tiêu tiếp theo: Phase 10 / Mục Tiêu 3 - Backend API Và Smoke.

Điều kiện chuyển sang mục tiêu kế tiếp:
- Mục tiêu hiện tại pass tiêu chí chấp nhận.
- Kiểm tra bắt buộc đã chạy hoặc lý do chưa chạy được đã ghi trong `PROJECT_STATUS.md`.
- `ROADMAP.md` đã được đọc lại sau khi hoàn thành mục tiêu.
- Đã auto commit thay đổi liên quan.

---

## Phase 10 - Module Quyết Định Và Thông Báo

Trạng thái: đang làm (bắt đầu 2026-06-06).

Mục tiêu phase: module nghiệp vụ thứ ba cho quyết định/thông báo theo pattern `contracts` và `dispatches`.

Điều kiện hoàn thành phase:
- Có quyết định scope trong `docs/DOMAIN_MODULE_DECISION.md`.
- Schema, API CRUD, UI `/decisions` và smoke script tái chạy được.
- Liên kết document detail hai chiều; không regression upload/OCR/search/RAG.

### Mục Tiêu 1 - Khảo Sát Và Thiết Kế Module Quyết Định

Trạng thái: hoàn thành (2026-06-07).

Skill bắt buộc: `solution-architect`, `database-designer`, `backend-fastapi`.

Mục tiêu:
- Chọn scope MVP module quyết định/thông báo và ghi quyết định trong `docs/DOMAIN_MODULE_DECISION.md` trước khi code.

Phạm vi:
- Đọc pattern `contract_records`, `dispatch_records`, liên kết document, audit, quyền admin/user.
- Đề xuất metadata tối thiểu, `business_type` mapping, API surface và boundary không làm trong MVP.
- Không code schema/API/UI trong mục tiêu này.

Tiêu chí chấp nhận:
- Mục mới trong `DOMAIN_MODULE_DECISION.md` đủ để triển khai schema ở mục tiêu 2.
- Ghi chú khảo sát trong `PROJECT_STATUS.md`.
- Không thêm cloud/LLM; giữ document/chunk core.

Kiểm tra bắt buộc:

```bash
git diff --check
```

### Mục Tiêu 2 - Schema Và Migration

Trạng thái: hoàn thành (2026-06-07).

Skill bắt buộc: `database-designer`, `backend-fastapi`.

Mục tiêu:
- Tạo bảng metadata quyết định với audit fields và soft delete.

Phạm vi:
- Alembic migration, SQLAlchemy model, quan hệ `Document`.
- Indexes cho list/filter MVP.

Tiêu chí chấp nhận:
- Migration chạy được trên stack local.
- Model khớp thiết kế mục tiêu 1.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api alembic upgrade head
git diff --check
```

### Mục Tiêu 3 - Backend API Và Smoke

Trạng thái: chưa làm.

Skill bắt buộc: `backend-fastapi`, `project-git-manager`.

Mục tiêu:
- API CRUD `/api/v1/decisions` theo `router -> service -> repository` và smoke tái chạy được.

Phạm vi:
- Router, service, repository, schema, audit log, soft delete admin-only.
- Script `smoke_decision_api` (hoặc tên tương đương).

Tiêu chí chấp nhận:
- Smoke pass; user/admin permission nhất quán với contracts/dispatches.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_decision_api
git diff --check
```

### Mục Tiêu 4 - Frontend UI Và Liên Kết Document

Trạng thái: chưa làm.

Skill bắt buộc: `frontend-nuxt`, `project-git-manager`.

Mục tiêu:
- Trang `/decisions` và liên kết hai chiều với document detail; hoàn tất phase 10.

Phạm vi:
- Page, composable, service, list/filter/form theo pattern `/contracts`.
- Cập nhật `ROADMAP.md`, `PROJECT_STATUS.md`, thay `TASK_NEXT.md` bằng phase kế tiếp (nếu có), auto commit.

Tiêu chí chấp nhận:
- UI CRUD hoạt động với API; không regression semantic search/RAG dashboard.

Kiểm tra bắt buộc:

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
docker compose exec -T api python -m app.scripts.smoke_decision_api
git diff --check
```
