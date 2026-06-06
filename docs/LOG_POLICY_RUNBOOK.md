# Log Policy Runbook

Runbook này mô tả policy log tối thiểu cho vận hành local/on-prem bằng Docker Compose.

## Mục Tiêu

- Phân biệt log liveness/readiness với log nghiệp vụ.
- Giúp admin troubleshoot upload, OCR worker và search mà không lộ secret.
- Giữ cấu hình log đơn giản, không thêm hệ thống log tập trung mới.

## Cấu Hình

Biến môi trường chính:

```bash
LOG_LEVEL=INFO
```

Giá trị hỗ trợ: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

Mặc định local/dev: `INFO`.

Format log API/worker:

```text
2026-06-06 10:15:30,123 INFO [app.workers.ocr_worker] Processing OCR job ...
```

## Xem Log

```bash
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f postgres
docker compose logs -f redis
docker compose logs -f qdrant
```

Lọc nhanh lỗi worker:

```bash
docker compose logs worker | rg -i "error|failed|exception"
```

## Health Và Readiness

Endpoint public, không cần auth:

```bash
curl -fsS http://localhost:8000/health/live
curl -fsS http://localhost:8000/health/ready
```

Ý nghĩa:
- `/health/live`: process API còn chạy.
- `/health/ready`: API sẵn sàng xử lý workflow, kiểm tra PostgreSQL, Redis, Qdrant và thư mục uploads.

Docker Compose dùng `/health/ready` cho healthcheck của service `api`.

Worker ghi heartbeat tại `/tmp/worker.heartbeat` mỗi vòng poll. Healthcheck worker kiểm tra file heartbeat còn mới trong 2 phút.

## Nên Log

- Khởi động service, migration, seed admin.
- Claim/process OCR job: `job_id`, `document_id`, `attempt`, trạng thái kết thúc.
- Lỗi recoverable/final failed với `failed_reason`.
- Lỗi kết nối PostgreSQL, Redis, Qdrant.
- Lỗi cấu hình model/OCR/embedding khi worker không thể xử lý job.

## Không Log

- JWT token, cookie, password, secret key.
- Toàn bộ nội dung văn bản OCR hoặc chunk text dài.
- Payload upload raw hoặc file binary.
- Thông tin cá nhân không cần thiết cho troubleshoot.

## Troubleshoot Nhanh

1. API không lên:
   - `curl http://localhost:8000/health/live`
   - `curl http://localhost:8000/health/ready`
   - `docker compose logs api`
2. Worker không claim job:
   - `docker compose ps worker`
   - `docker compose logs worker`
   - Kiểm tra queue: `GET /api/v1/ops/worker-queue` sau login admin.
3. Search không trả kết quả:
   - Kiểm tra `/health/ready` component `qdrant`.
   - Xem trang admin `/status` hoặc `GET /api/v1/ops/system-status`.

Smoke health/readiness:

```bash
python3 -m app.scripts.smoke_health_checks --api-base http://localhost:8000
```

Hoặc trong container API:

```bash
docker compose exec -T api python -m app.scripts.smoke_health_checks --api-base http://localhost:8000
```
