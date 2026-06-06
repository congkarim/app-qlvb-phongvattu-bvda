# Worker Ops Runbook

Runbook này dành cho vận hành local/on-prem bằng Docker Compose. Không dùng cloud service.

## Kiểm Tra Nhanh

```bash
docker compose ps
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

Log policy và hướng dẫn xem log:

```text
docs/LOG_POLICY_RUNBOOK.md
```

Đăng nhập admin rồi kiểm tra queue worker:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/ops/worker-queue
```

Các field chính:
- `pending_ready`: job có thể được worker claim ngay.
- `pending_delayed`: job retry đang chờ tới `next_run_at`.
- `running`: job đang `ocr_running`.
- `stale_running`: job `ocr_running` quá `OCR_JOB_LEASE_TIMEOUT_SECONDS` (mặc định 3600s).
- `failed`: job đã fail cuối cùng.
- `active`: tổng pending/running cần theo dõi.
- `lease_timeout_seconds`, `stale_recovery_enabled`: cấu hình recovery hiện tại.

## Job Kẹt (Stale)

Worker tự recovery stale job trước mỗi lần claim. Admin cũng có thể xem và recover thủ công qua API ops.

Liệt kê job stale và document đang kẹt:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/ops/worker-queue/stale-jobs?limit=50&offset=0"
```

Response gồm `items[]` với `job_id`, `document_id`, `document_status`, `started_at`, `stale_for_seconds`, `attempts/max_attempts`.

Recover tất cả job stale (khuyến nghị dừng worker trước nếu muốn kiểm soát thủ công hoàn toàn):

```bash
docker compose stop worker

curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/ops/worker-queue/recover-stale
```

Recover một job cụ thể:

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/ops/worker-queue/stale-jobs/<job_id>/recover"
```

Hành vi recovery:
- Còn lượt retry: job → `pending`, `failed_reason=worker_lease_expired`, document → `ocr_pending`/`reprocess_pending`.
- Hết lượt: job → `failed`, document → `failed` hoặc `searchable` (reprocess có chunk cũ).
- User thường nhận `403` ở mọi endpoint `/api/v1/ops/*`.

Sau recover thủ công, start lại worker:

```bash
docker compose start worker
```

Cấu hình lease (env service `api`/`worker`):

```bash
OCR_JOB_LEASE_TIMEOUT_SECONDS=3600
OCR_JOB_STALE_RECOVERY_ENABLED=true
```

Tăng `OCR_JOB_LEASE_TIMEOUT_SECONDS` nếu job OCR scan lớn thường chạy > 1 giờ để tránh recover nhầm job đang chạy thật.

## Smoke Worker

Trước khi chạy smoke worker, dừng worker thật để tránh tranh job smoke:

```bash
docker compose stop worker
docker compose exec -T api python -m app.scripts.smoke_worker_operations
docker compose exec -T api python -m app.scripts.smoke_worker_stale_recovery
docker compose start worker
```

Smoke trên kiểm tra:
- Atomic claim không cho hai session claim cùng một job.
- Retry policy không chạy lại job trước `next_run_at` và dừng ở `max_attempts`.
- Endpoint `/api/v1/ops/worker-queue` trả queue counters cho admin và chặn request chưa đăng nhập.
- Endpoint stale jobs liệt kê/recover job kẹt; user thường bị `403`.
- `smoke_worker_stale_recovery` mô phỏng worker crash: job stale được recovery qua worker loop, job đang chạy thật không bị recover nhầm.

## Restart Worker

Restart nhẹ:

```bash
docker compose restart worker
```

Xem log:

```bash
docker compose logs -f worker
```

Nếu worker đang xử lý job dài, ưu tiên xem log và queue status trước khi restart. Job `ocr_running` có lease timeout (`OCR_JOB_LEASE_TIMEOUT_SECONDS`, mặc định 3600s); worker tự recovery job stale trước mỗi claim. Nếu container chết giữa job, kiểm tra `stale_running` trên `/ops/worker-queue` hoặc gọi `/ops/worker-queue/stale-jobs` rồi recover theo runbook trên.

## Khi Job Failed

1. Mở document detail trên web và xem card `Job audit`.
2. Kiểm tra:
   - `failed_reason`
   - `error_message`
   - `attempts/max_attempts`
   - `job_type`
3. Với lỗi input không retry như `unsupported_document_format`, `empty_document_content`, `empty_chunks`, `uploaded_file_missing`, sửa file nguồn hoặc upload lại định dạng đúng.
4. Với lỗi runtime `processing_error`, xem log worker để xác định nguyên nhân trước khi bấm reprocess.
5. Admin có thể bấm `Reprocess` trong detail sau khi document không còn active job.

## Backup

Backup đầy đủ cho PostgreSQL, uploaded source files và Qdrant đã tách thành runbook riêng:

```text
docs/STORAGE_BACKUP_RESTORE_RUNBOOK.md
```

## Restore

Restore đầy đủ nên theo thứ tự trong `docs/STORAGE_BACKUP_RESTORE_RUNBOOK.md`, sau đó chạy lại migration và smoke worker ops.
