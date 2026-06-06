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

Phase trước: Phase 7 hoàn thành ngày 2026-06-06.

Phase hiện tại: Phase 8 - Worker Resilience Và Production Upgrade.

Mục tiêu tiếp theo: Phase 8 / Mục tiêu 1 - Khảo Sát Job Kẹt Và Thiết Kế Lease Recovery.

Điều kiện chuyển sang mục tiêu kế tiếp:
- Mục tiêu hiện tại pass tiêu chí chấp nhận.
- Kiểm tra bắt buộc đã chạy hoặc lý do chưa chạy được đã ghi trong `PROJECT_STATUS.md`.
- `ROADMAP.md` đã được đọc lại sau khi hoàn thành mục tiêu.
- Đã auto commit thay đổi liên quan.

---

## Phase 8 - Worker Resilience Và Production Upgrade

Trạng thái: đang làm (bắt đầu 2026-06-06).

Mục tiêu phase: giảm rủi ro vận hành lâu dài khi worker crash hoặc khi nâng cấp phiên bản trên môi trường nội bộ.

Điều kiện hoàn thành phase:
- Job `ocr_running` bị kẹt có cơ chế phát hiện và recovery có kiểm soát.
- Admin có endpoint hoặc runbook rõ ràng để xem và xử lý job/document bị kẹt.
- Có runbook upgrade/migration Alembic có thể làm theo trên on-prem.
- Smoke worker recovery pass trên Docker Compose.

### Mục Tiêu 1 - Khảo Sát Job Kẹt Và Thiết Kế Lease Recovery

Trạng thái: chưa làm.

Skill bắt buộc: `backend-fastapi`, `solution-architect`.

Mục tiêu:
- Nắm rõ lifecycle job `ocr_running` hiện tại và thiết kế policy lease timeout/stale recovery trước khi đổi behavior.

Phạm vi:
- Đọc `OCRWorker`, `OCRJobRepository`, model `ocr_jobs` (`started_at`, `attempts`, `status`, `job_type`).
- Xác định document status nào bị kẹt khi worker crash (`ocr_running`, `reprocess_running`, `chunking`).
- Đề xuất config MVP, ví dụ `OCR_JOB_LEASE_TIMEOUT_SECONDS`, ngưỡng phát hiện stale và hành vi recovery (retry pending vs failed với `failed_reason`).

Tiêu chí chấp nhận:
- Ghi chú kỹ thuật trong `PROJECT_STATUS.md`; cập nhật mục Kết quả khảo sát dưới đây khi xong.
- Policy recovery không phá atomic claim và retry policy Phase 2.
- Chưa thay đổi runtime behavior lớn trước khi hoàn tất khảo sát.

Kết quả khảo sát:
- (chưa có)

### Mục Tiêu 2 - Stale-Job Recovery Backend

Trạng thái: chưa làm.

Skill bắt buộc: `backend-fastapi`.

Mục tiêu:
- Tự động phát hiện và recovery job `ocr_running` quá lâu theo lease timeout đã thiết kế.

Phạm vi:
- Thêm config lease timeout trong `apps/api/app/core/config.py`.
- Thêm repository/service method recover stale jobs; đồng bộ document/source file status khi cần.
- Worker loop gọi recovery trước/sau claim job (MVP: trong worker loop).
- Ghi audit hoặc log rõ ràng cho mỗi lần recovery.

Tiêu chí chấp nhận:
- Job `ocr_running` quá `started_at + lease_timeout` được recovery có kiểm soát.
- Job đang chạy thật không bị recover nhầm trong smoke.
- Retry policy hiện có vẫn pass.

Kiểm tra bắt buộc:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile <recovery-modules>
docker compose stop worker
docker compose exec -T api python -m app.scripts.smoke_worker_claim_atomic
docker compose exec -T api python -m app.scripts.smoke_worker_retry_policy
git diff --check
```

### Mục Tiêu 3 - Ops Endpoint Và Runbook Job Kẹt

Trạng thái: chưa làm.

Skill bắt buộc: `backend-fastapi`, `solution-architect`.

Mục tiêu:
- Admin xem và xử lý job/document bị kẹt qua endpoint ops và runbook.

Phạm vi:
- Mở rộng `/api/v1/ops/worker-queue` hoặc thêm endpoint admin-only liệt kê job/document stale.
- Thêm action admin-only recover/release job kẹt (nếu phù hợp MVP) hoặc ghi rõ runbook thủ công có kiểm soát.
- Cập nhật `docs/WORKER_OPS_RUNBOOK.md`.

Tiêu chí chấp nhận:
- Admin gọi được endpoint ops và thấy job/document đang kẹt.
- User thường bị `403` ở endpoint ops nhạy cảm.
- Runbook mô tả command có thể làm theo trên Docker Compose.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_worker_operations
git diff --check
```

### Mục Tiêu 4 - Runbook Nâng Cấp Alembic Production

Trạng thái: chưa làm.

Skill bắt buộc: `solution-architect`, `project-git-manager`.

Mục tiêu:
- Có runbook nâng cấp phiên bản và migration Alembic cho Docker Compose production nội bộ.

Phạm vi:
- Thêm `docs/PRODUCTION_UPGRADE_RUNBOOK.md`: backup, `alembic upgrade head`, restart service, smoke sau upgrade, rollback tối thiểu.
- Liên kết tới `docs/STORAGE_BACKUP_RESTORE_RUNBOOK.md`, `docs/ON_PREM_ENV_RUNBOOK.md`, `docs/WORKER_OPS_RUNBOOK.md`.

Tiêu chí chấp nhận:
- Runbook có command copy-paste được cho on-prem Docker Compose.
- Ghi rõ thứ tự: dừng worker → migrate → start lại api/worker/web.

### Mục Tiêu 5 - Smoke Worker Recovery Sau Crash Mô Phỏng

Trạng thái: chưa làm.

Skill bắt buộc: `backend-fastapi`.

Mục tiêu:
- Script smoke tái chạy được mô phỏng worker crash và xác nhận recovery.

Phạm vi:
- Thêm `python -m app.scripts.smoke_worker_stale_recovery` (hoặc mở rộng `smoke_worker_operations`).
- Kịch bản: job `ocr_running` stale → recovery → job/document về trạng thái hợp lệ.
- Ghi command trong runbook và `PROJECT_STATUS.md`.

Tiêu chí chấp nhận:
- Smoke pass trên Docker Compose khi worker đang dừng.
- Không regression `smoke_worker_claim_atomic` và `smoke_worker_retry_policy`.
- Phase 8 hoàn thành: cập nhật `ROADMAP.md`, `PROJECT_STATUS.md`, thay `TASK_NEXT.md` bằng checklist Phase 9, auto commit.
