# Storage, Backup And Restore Runbook

Runbook này dành cho vận hành local/on-prem bằng Docker Compose. Không dùng cloud service.

## Storage Volumes

Docker Compose đang dùng 3 named volumes nghiệp vụ:

| Volume | Mount trong container | Dữ liệu |
| --- | --- | --- |
| `postgres_data` | `/var/lib/postgresql/data` | PostgreSQL database, users, documents metadata, OCR jobs, audit logs |
| `qdrant_data` | `/qdrant/storage` | Qdrant collections và vector payload cho semantic search |
| `uploads_data` | `/data/uploads` | File nguồn đã upload và tài liệu cần preview/reprocess |

Tên volume thực tế trên máy thường có prefix theo project directory, ví dụ:

```bash
docker volume ls | grep app-qlvb-phongvattu
```

Kiểm tra mount của stack:

```bash
docker compose config
docker compose ps
docker volume inspect app-qlvb-phongvattu_postgres_data
docker volume inspect app-qlvb-phongvattu_qdrant_data
docker volume inspect app-qlvb-phongvattu_uploads_data
```

Nếu đặt tên project khác bằng `COMPOSE_PROJECT_NAME`, thay prefix volume tương ứng trong các command backup/restore bên dưới.

## Backup Policy

Backup đầy đủ phải gồm cả 3 phần:

- PostgreSQL dump.
- Uploaded source files.
- Qdrant storage.

PostgreSQL là nguồn sự thật cho metadata nghiệp vụ. `uploads_data` là nguồn sự thật cho file gốc. Qdrant có thể reindex lại từ PostgreSQL/chunks trong một số tình huống dev, nhưng production nội bộ vẫn nên backup Qdrant để restore nhanh và giữ search sẵn sàng.

Nên chạy backup khi hệ thống ít ghi. Với backup nhất quán nhất, dừng `web`, `worker` và `api` để chặn upload/reprocess mới trong lúc snapshot:

```bash
docker compose stop web worker api
docker compose up -d postgres qdrant redis
```

Tạo thư mục backup:

```bash
mkdir -p backups
```

## Backup PostgreSQL

```bash
docker compose exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-legal}" \
  -d "${POSTGRES_DB:-legal_doc_ai}" \
  --clean --if-exists \
  > backups/postgres_$(date +%Y%m%d_%H%M%S).sql
```

Kiểm tra file backup có dữ liệu:

```bash
ls -lh backups/postgres_*.sql
tail -n 5 backups/postgres_YYYYMMDD_HHMMSS.sql
```

## Backup Uploaded Source Files

```bash
docker run --rm \
  -v app-qlvb-phongvattu_uploads_data:/data/uploads:ro \
  -v "$PWD/backups:/backups" \
  alpine tar czf /backups/uploads_$(date +%Y%m%d_%H%M%S).tgz -C /data uploads
```

Kiểm tra archive:

```bash
tar tzf backups/uploads_YYYYMMDD_HHMMSS.tgz | head
```

## Backup Qdrant

```bash
docker compose stop qdrant
docker run --rm \
  -v app-qlvb-phongvattu_qdrant_data:/qdrant/storage:ro \
  -v "$PWD/backups:/backups" \
  alpine tar czf /backups/qdrant_$(date +%Y%m%d_%H%M%S).tgz -C /qdrant storage
docker compose up -d qdrant
```

Qdrant volume backup nên chạy khi `qdrant` đã dừng để tránh snapshot dang dở.

## Restore Order

Restore nên chạy trên volume trống hoặc sau khi đã xác nhận có thể ghi đè dữ liệu hiện tại. Không restore lên hệ thống đang phục vụ người dùng.

Thứ tự restore:

1. Dừng service ghi dữ liệu.
2. Restore PostgreSQL.
3. Restore uploaded source files.
4. Restore Qdrant.
5. Chạy migration head.
6. Khởi động toàn bộ stack và smoke kiểm tra.

```bash
docker compose stop web worker api qdrant
docker compose up -d postgres redis
```

## Restore PostgreSQL

Xóa và tạo lại database trước khi nạp dump:

```bash
docker compose exec -T postgres dropdb \
  -U "${POSTGRES_USER:-legal}" \
  --if-exists "${POSTGRES_DB:-legal_doc_ai}"

docker compose exec -T postgres createdb \
  -U "${POSTGRES_USER:-legal}" \
  "${POSTGRES_DB:-legal_doc_ai}"

docker compose exec -T postgres psql \
  -U "${POSTGRES_USER:-legal}" \
  -d "${POSTGRES_DB:-legal_doc_ai}" \
  < backups/postgres_YYYYMMDD_HHMMSS.sql
```

## Restore Uploaded Source Files

```bash
docker run --rm \
  -v app-qlvb-phongvattu_uploads_data:/data \
  -v "$PWD/backups:/backups" \
  alpine sh -c 'rm -rf /data/uploads && tar xzf /backups/uploads_YYYYMMDD_HHMMSS.tgz -C /data'
```

## Restore Qdrant

```bash
docker compose stop qdrant
docker run --rm \
  -v app-qlvb-phongvattu_qdrant_data:/qdrant \
  -v "$PWD/backups:/backups" \
  alpine sh -c 'rm -rf /qdrant/storage && tar xzf /backups/qdrant_YYYYMMDD_HHMMSS.tgz -C /qdrant'
docker compose up -d qdrant
```

## Post-Restore Checks

```bash
docker compose up -d api postgres redis qdrant
docker compose exec -T api alembic upgrade head
docker compose up -d worker web
docker compose ps
curl -fsS http://localhost:8000/health
```

Đăng nhập admin và kiểm tra worker queue:

```bash
TOKEN=$(curl -fsS -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

curl -fsS -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/ops/worker-queue
```

Smoke phù hợp sau restore:

```bash
docker compose stop worker
docker compose exec -T api python -m app.scripts.smoke_worker_operations
docker compose start worker
```

Nếu search không trả kết quả sau restore nhưng PostgreSQL và uploads còn đúng, kiểm tra Qdrant status tại trang `/status` hoặc endpoint `/api/v1/ops/system-status`. Khi Qdrant backup không dùng được, có thể reprocess/reindex tài liệu theo workflow admin để dựng lại vector từ dữ liệu nguồn.
