# Production Upgrade Runbook

Runbook này dành cho nâng cấp phiên bản ứng dụng và migration Alembic trên môi trường nội bộ chạy Docker Compose. Không dùng cloud service.

Runbook liên quan:

- `docs/STORAGE_BACKUP_RESTORE_RUNBOOK.md` — backup/restore PostgreSQL, uploads, Qdrant trước khi nâng cấp hoặc khi rollback.
- `docs/ON_PREM_ENV_RUNBOOK.md` — kiểm tra `.env`, secret và production guard trước khi start lại stack.
- `docs/WORKER_OPS_RUNBOOK.md` — kiểm tra worker queue, job stale và smoke worker sau upgrade.

## Phạm Vi

Áp dụng khi:

- Deploy phiên bản mới của `api`, `worker`, `web`.
- Có migration Alembic mới trong `apps/api/alembic/versions/`.
- Cần restart stack production nội bộ có kiểm soát downtime ngắn.

Không thay thế backup định kỳ; luôn backup trước upgrade có migration schema.

## Checklist Trước Upgrade

1. Đọc release note/commit mới, xác định có migration Alembic hay thay đổi env bắt buộc.
2. Kiểm tra `.env` production theo `docs/ON_PREM_ENV_RUNBOOK.md`.
3. Ghi nhận revision hiện tại và trạng thiệt bị:

```bash
docker compose ps
docker compose exec -T api alembic current
curl -fsS http://localhost:8000/health/ready
```

4. Thông báo downtime ngắn nếu cần (web/worker sẽ dừng trong lúc migrate).

## Backup Bắt Buộc

Thực hiện backup đầy đủ theo `docs/STORAGE_BACKUP_RESTORE_RUNBOOK.md` (PostgreSQL + uploads + Qdrant).

Tối thiểu trước upgrade có migration schema:

```bash
mkdir -p backups
docker compose stop web worker api

docker compose exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-legal}" \
  -d "${POSTGRES_DB:-legal_doc_ai}" \
  --clean --if-exists \
  > "backups/pre_upgrade_postgres_$(date +%Y%m%d_%H%M%S).sql"

ls -lh backups/pre_upgrade_postgres_*.sql
```

Giữ lại tag/commit/image cũ để rollback application nếu cần.

## Quy Trình Nâng Cấp (Thứ Tự Bắt Buộc)

Thứ tự MVP: **dừng worker → migrate → start lại api/worker/web**.

### 1. Lấy mã mới và build image

Từ thư mục repo trên máy on-prem:

```bash
git fetch
git checkout <tag-or-branch-moi>
git pull

docker compose build api worker web
```

Nếu không bind-mount source mà chỉ dùng image đã build, bỏ qua `git checkout` trên host và dùng image tag nội bộ tương ứng.

### 2. Dừng worker và web (chặn xử lý OCR + upload mới)

```bash
docker compose stop worker web
```

Khuyến nghị dừng thêm `api` nếu muốn chặn hoàn toàn traffic API trong lúc migrate:

```bash
docker compose stop api
```

Worker **phải** dừng trước migrate để tránh job `ocr_running` giữ schema cũ giữa chừng. Xem thêm `docs/WORKER_OPS_RUNBOOK.md` nếu có job stale trước upgrade.

### 3. Chạy migration Alembic

Đảm bảo PostgreSQL (và Redis/Qdrant nếu api phụ thuộc health) đang chạy:

```bash
docker compose up -d postgres redis qdrant
```

Kiểm tra revision sẽ áp dụng:

```bash
docker compose run --rm api alembic current
docker compose run --rm api alembic heads
```

Chạy migrate:

```bash
docker compose run --rm api alembic upgrade head
```

Xác nhận sau migrate:

```bash
docker compose run --rm api alembic current
```

Nếu `upgrade head` fail: **dừng tại đây**, không start worker/web; xem mục Rollback tối thiểu.

### 4. Start lại api, worker, web

```bash
docker compose up -d api worker web
docker compose ps
```

Service `api` trong `docker-compose.yml` dev cũng chạy `alembic upgrade head` lúc start; sau bước migrate thủ công ở trên, lệnh đó sẽ no-op nếu đã ở `head`.

Kiểm tra health:

```bash
curl -fsS http://localhost:8000/health/live
curl -fsS http://localhost:8000/health/ready
```

## Smoke Sau Upgrade

Chạy trên Docker Compose sau khi stack đã start:

```bash
docker compose exec -T api alembic current

curl -fsS http://localhost:8000/health/ready

docker compose stop worker
docker compose exec -T api python -m app.scripts.smoke_worker_operations
docker compose exec -T api python -m app.scripts.smoke_worker_stale_recovery
docker compose start worker
```

Đăng nhập admin kiểm tra ops queue (thay email/password theo `.env` production):

```bash
TOKEN=$(curl -fsS -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

curl -fsS -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/ops/worker-queue
```

Kiểm tra thủ công tối thiểu trên web:

- Login admin.
- Mở `/status` — OCR, embedding, Qdrant, worker queue.
- Mở một document searchable — preview và search cơ bản.

Nếu smoke fail, xem log:

```bash
docker compose logs --tail=200 api worker
```

Chi tiết log policy: `docs/LOG_POLICY_RUNBOOK.md`.

## Rollback Tối Thiểu

Rollback gồm hai lớp: **application** và **database**. Chỉ rollback DB khi migration đã làm hỏng schema/dữ liệu.

### A. Rollback application (không đổi DB)

Khi migration đã thành công nhưng app mới lỗi runtime:

```bash
docker compose stop worker web api
git checkout <commit-or-tag-cu>
docker compose build api worker web
docker compose up -d api worker web
curl -fsS http://localhost:8000/health/ready
```

Lưu ý: nếu migration mới **không tương thích ngược** với code cũ, không dùng rollback application một mình — cần restore DB.

### B. Rollback database (restore backup)

Khi `alembic upgrade head` fail hoặc schema/data sai sau upgrade:

```bash
docker compose stop worker web api
```

Restore PostgreSQL từ file backup trước upgrade (chi tiết command trong `docs/STORAGE_BACKUP_RESTORE_RUNBOOK.md`):

```bash
docker compose up -d postgres
cat backups/pre_upgrade_postgres_YYYYMMDD_HHMMSS.sql | \
  docker compose exec -T postgres psql \
  -U "${POSTGRES_USER:-legal}" \
  -d "${POSTGRES_DB:-legal_doc_ai}"
```

Sau restore DB, checkout code/image cũ tương ứng backup rồi start lại:

```bash
git checkout <commit-or-tag-cu>
docker compose build api worker web
docker compose up -d api worker web
docker compose exec -T api alembic current
curl -fsS http://localhost:8000/health/ready
```

Không chạy `alembic downgrade` trên production nội bộ trừ khi team đã kiểm thử downgrade path; ưu tiên restore từ dump SQL đã backup.

### C. Job OCR giữa chừng sau upgrade

Nếu worker bị dừng giữa job:

1. Kiểm tra `stale_running` trên `/api/v1/ops/worker-queue`.
2. Liệt kê/recover theo `docs/WORKER_OPS_RUNBOOK.md`.
3. Start lại worker sau khi queue ổn định.

## Ghi Chú Vận Hành

- Luôn dừng **worker** trước migrate; không migrate khi worker đang xử lý job dài trừ khi đã kiểm tra queue/stale jobs.
- Uploads và Qdrant không thay thế backup PostgreSQL khi migration đổi schema metadata.
- Sau upgrade có thêm biến env mới, cập nhật `.env` và `docker compose config` trước `up -d`.
- Production nội bộ: đặt `APP_ENV=production` và secret mạnh theo `docs/ON_PREM_ENV_RUNBOOK.md`.

## Tóm Tắt Nhanh

```bash
# Backup + dừng xử lý
docker compose stop web worker api
# ... pg_dump theo STORAGE_BACKUP_RESTORE_RUNBOOK.md ...

# Code + build
git pull && docker compose build api worker web

# Migrate
docker compose up -d postgres redis qdrant
docker compose run --rm api alembic upgrade head

# Start lại
docker compose up -d api worker web
curl -fsS http://localhost:8000/health/ready

# Smoke
docker compose stop worker
docker compose exec -T api python -m app.scripts.smoke_worker_operations
docker compose exec -T api python -m app.scripts.smoke_worker_stale_recovery
docker compose start worker
```
