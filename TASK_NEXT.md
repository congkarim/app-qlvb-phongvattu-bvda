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

Phase hiện tại: **chưa mở** — Phase 18 (dự kiến).

Mục tiêu tiếp theo: chưa lập checklist. Xem hướng dự kiến trong `ROADMAP.md` (HA Ollama, inventory/tồn kho, workflow phê duyệt — chưa chốt scope).

Điều kiện mở Phase 18:
- Cập nhật `ROADMAP.md` với checklist mục tiêu chi tiết và ưu tiên nghiệp vụ.
- Thay nội dung `TASK_NEXT.md` bằng checklist Phase 18.
- Ghi nhận trong `PROJECT_STATUS.md`.

---

## Phase 18 (Dự Kiến, Chưa Mở)

Trạng thái: chưa lập chi tiết.

Hướng dự kiến (tham chiếu `ROADMAP.md`, chưa chốt):
- HA / scale horizontal Ollama hoặc tách LLM host production.
- Inventory/tồn kho vật tư (ngoài scope MVP Phase 0–17).
- Workflow phê duyệt nhiều bước, line items procurement chi tiết.

**Chưa có mục tiêu thực thi.** Khi mở phase, thay section này bằng checklist mục tiêu cụ thể theo `ROADMAP.md`.

Regression nhanh sau Phase 17 (extractive default, không profile `llm`):

```bash
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.smoke_relation_suggestions
docker compose exec -T api python -m app.scripts.smoke_health_checks
```

Generative (optional, profile `llm` + model pulled): `docs/RAG_LLM_RUNBOOK.md`.
