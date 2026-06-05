# Worker Ops Runbook

Runbook này dành cho vận hành local/on-prem bằng Docker Compose. Không dùng cloud service.

## Kiểm Tra Nhanh

```bash
docker compose ps
curl http://localhost:8000/health
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
- `failed`: job đã fail cuối cùng.
- `active`: tổng pending/running cần theo dõi.

## Smoke Worker

Trước khi chạy smoke worker, dừng worker thật để tránh tranh job smoke:

```bash
docker compose stop worker
docker compose exec -T api python -m app.scripts.smoke_worker_operations
docker compose start worker
```

Smoke trên kiểm tra:
- Atomic claim không cho hai session claim cùng một job.
- Retry policy không chạy lại job trước `next_run_at` và dừng ở `max_attempts`.
- Endpoint `/api/v1/ops/worker-queue` trả queue counters cho admin và chặn request chưa đăng nhập.

## Restart Worker

Restart nhẹ:

```bash
docker compose restart worker
```

Xem log:

```bash
docker compose logs -f worker
```

Nếu worker đang xử lý job dài, ưu tiên xem log và queue status trước khi restart. MVP hiện chưa có lease timeout cho job `ocr_running`; nếu container chết giữa job đang chạy, cần kiểm tra thủ công job/document tương ứng trước khi reprocess.

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

Tạo thư mục backup:

```bash
mkdir -p backups
```

PostgreSQL:

```bash
docker compose exec -T postgres pg_dump -U legal -d legal_doc_ai \
  > backups/postgres_$(date +%Y%m%d_%H%M%S).sql
```

Uploaded source files:

```bash
docker run --rm \
  -v app-qlvb-phongvattu_uploads_data:/data/uploads:ro \
  -v "$PWD/backups:/backups" \
  alpine tar czf /backups/uploads_$(date +%Y%m%d_%H%M%S).tgz -C /data uploads
```

Qdrant volume:

```bash
docker run --rm \
  -v app-qlvb-phongvattu_qdrant_data:/qdrant/storage:ro \
  -v "$PWD/backups:/backups" \
  alpine tar czf /backups/qdrant_$(date +%Y%m%d_%H%M%S).tgz -C /qdrant storage
```

## Restore

Restore nên chạy khi stack đang dừng hoặc chỉ bật service cần thiết.

PostgreSQL:

```bash
docker compose up -d postgres
docker compose exec -T postgres psql -U legal -d legal_doc_ai \
  < backups/postgres_YYYYMMDD_HHMMSS.sql
```

Uploaded source files:

```bash
docker compose stop api worker web
docker run --rm \
  -v app-qlvb-phongvattu_uploads_data:/data \
  -v "$PWD/backups:/backups" \
  alpine sh -c 'rm -rf /data/uploads && tar xzf /backups/uploads_YYYYMMDD_HHMMSS.tgz -C /data'
```

Qdrant volume:

```bash
docker compose stop qdrant
docker run --rm \
  -v app-qlvb-phongvattu_qdrant_data:/qdrant \
  -v "$PWD/backups:/backups" \
  alpine sh -c 'rm -rf /qdrant/storage && tar xzf /backups/qdrant_YYYYMMDD_HHMMSS.tgz -C /qdrant'
docker compose up -d qdrant
```

Sau restore:

```bash
docker compose up -d
docker compose exec -T api alembic upgrade head
docker compose exec -T api python -m app.scripts.smoke_worker_operations
```
