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

Phase trước: Phase 8 hoàn thành ngày 2026-06-06.

Phase hiện tại: Phase 9 - RAG UX Và Search Nâng Cao.

Mục tiêu tiếp theo: Phase 9 / Mục tiêu 1 - Khảo Sát RAG API Và Thiết Kế UX Dashboard.

Điều kiện chuyển sang mục tiêu kế tiếp:
- Mục tiêu hiện tại pass tiêu chí chấp nhận.
- Kiểm tra bắt buộc đã chạy hoặc lý do chưa chạy được đã ghi trong `PROJECT_STATUS.md`.
- `ROADMAP.md` đã được đọc lại sau khi hoàn thành mục tiêu.
- Đã auto commit thay đổi liên quan.

---

## Phase 9 - RAG UX Và Search Nâng Cao

Trạng thái: đang làm (bắt đầu 2026-06-06).

Mục tiêu phase: đưa RAG foundation từ API backend lên workflow người dùng trên dashboard và giữ citation rõ ràng.

Điều kiện hoàn thành phase:
- User hỏi–đáp trên web với citation chunk/document/page.
- Fallback `insufficient_evidence` hiển thị đúng trên UI.
- Smoke hoặc benchmark RAG answer có thể chạy lại sau khi có UI.

### Mục Tiêu 1 - Khảo Sát RAG API Và Thiết Kế UX Dashboard

Trạng thái: chưa làm.

Skill bắt buộc: `frontend-nuxt`, `semantic-search-rag`, `solution-architect`.

Mục tiêu:
- Nắm contract `POST /api/v1/search/answer` và thiết kế UX MVP trên dashboard trước khi code UI.

Phạm vi:
- Đọc `rag_answer_service`, schema response, `smoke_rag_answer`, dashboard/search composable hiện có.
- Xác định states UI: loading, grounded answer, `insufficient_evidence`, lỗi API.
- Đề xuất component/composable/service structure theo `page -> composable -> service -> API`.

Tiêu chí chấp nhận:
- Ghi chú kỹ thuật trong `PROJECT_STATUS.md`; cập nhật mục Kết quả khảo sát dưới đây khi xong.
- Không thêm LLM/cloud; giữ extractive RAG local hiện có.
- Chưa thay đổi UI lớn trước khi hoàn tất khảo sát.

Kết quả khảo sát:
- (chưa có)

### Mục Tiêu 2 - RAG Q&A UI Trên Dashboard

Trạng thái: chưa làm.

Skill bắt buộc: `frontend-nuxt`, `semantic-search-rag`.

Mục tiêu:
- User hỏi–đáp trên dashboard qua API RAG answer, hiển thị citation và link mở document/chunk.

Phạm vi:
- Service/composable gọi `POST /api/v1/search/answer`.
- UI panel Q&A trên `/dashboard`: input câu hỏi, answer, danh sách citation, trạng thái `insufficient_evidence`.
- Tái sử dụng filter metadata search hiện có nếu phù hợp MVP.

Tiêu chí chấp nhận:
- Admin/user đã login gọi được RAG answer từ dashboard.
- Citation hiển thị quote và nguồn (document/chunk/page).
- `insufficient_evidence` có message rõ, không hiển thị answer giả.

Kiểm tra bắt buộc:

```bash
docker compose run --rm --no-deps web npm run build
git diff --check
```

### Mục Tiêu 3 - Smoke Và Runbook RAG Answer Trên Web

Trạng thái: chưa làm.

Skill bắt buộc: `frontend-nuxt`, `backend-fastapi`, `project-git-manager`.

Mục tiêu:
- Có smoke/checklist tái chạy được cho RAG answer sau khi có UI; hoàn tất phase 9.

Phạm vi:
- Mở rộng hoặc bổ sung smoke (API + hướng dẫn kiểm tra UI thủ công ngắn trong README hoặc runbook nếu cần).
- Xác nhận `smoke_rag_answer` vẫn pass; ghi command trong `PROJECT_STATUS.md`.
- Phase 9 hoàn thành: cập nhật `ROADMAP.md`, `PROJECT_STATUS.md`, thay `TASK_NEXT.md` bằng checklist phase kế tiếp (nếu có), auto commit.

Tiêu chí chấp nhận:
- `docker compose exec -T api python -m app.scripts.smoke_rag_answer` pass.
- UI dashboard Q&A hoạt động với fixture/smoke data hoặc checklist manual rõ ràng.
- Không regression semantic search dashboard hiện có.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose run --rm --no-deps web npm run build
git diff --check
```
