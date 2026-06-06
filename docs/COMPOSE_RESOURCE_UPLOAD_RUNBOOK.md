# Compose Resource Limits And Upload Policy Runbook

Runbook này dành cho vận hành local/on-prem bằng Docker Compose. Không dùng cloud service.

## Mục Tiêu

- Giới hạn tài nguyên container để tránh một service OCR/worker chiếm hết máy chủ nội bộ.
- Chuẩn hóa policy upload file nguồn cho API và frontend.
- Liên kết storage volumes với runbook backup/restore hiện có.

## Resource Limits Docker Compose

Các service chính có `deploy.resources.limits` đọc từ `.env`:

| Service | CPU mặc định | Memory mặc định | Ghi chú |
| --- | --- | --- | --- |
| `postgres` | 1 | 1G | Metadata nghiệp vụ |
| `redis` | 0.5 | 512M | Cache/queue skeleton |
| `qdrant` | 1 | 2G | Vector search |
| `api` | 1 | 2G | FastAPI + upload |
| `worker` | 2 | 4G | OCR/extract nặng nhất |
| `web` | 0.5 | 512M | Nuxt frontend |

Biến môi trường tương ứng:

```env
POSTGRES_CPU_LIMIT=1
POSTGRES_MEMORY_LIMIT=1G
REDIS_CPU_LIMIT=0.5
REDIS_MEMORY_LIMIT=512M
QDRANT_CPU_LIMIT=1
QDRANT_MEMORY_LIMIT=2G
API_CPU_LIMIT=1
API_MEMORY_LIMIT=2G
WORKER_CPU_LIMIT=2
WORKER_MEMORY_LIMIT=4G
WEB_CPU_LIMIT=0.5
WEB_MEMORY_LIMIT=512M
```

Kiểm tra cấu hình render:

```bash
docker compose config
docker compose ps
```

Khi máy chủ yếu hơn hoặc có GPU/OCR nặng, tăng `WORKER_CPU_LIMIT` và `WORKER_MEMORY_LIMIT` trước. Không bỏ limit hoàn toàn trên production nội bộ trừ khi đã có giám sát tài nguyên khác.

## Storage Volumes

Named volumes nghiệp vụ:

- `postgres_data`
- `qdrant_data`
- `uploads_data`

Chi tiết backup/restore và kiểm tra volume thực tế:

```text
docs/STORAGE_BACKUP_RESTORE_RUNBOOK.md
```

Upload file nguồn nằm trong `uploads_data` mount tại `/data/uploads` cho `api` và `worker`.

## Upload Policy

Backend đọc các biến sau:

```env
UPLOAD_MAX_FILE_SIZE_BYTES=52428800
UPLOAD_MAX_FILES_PER_REQUEST=20
UPLOAD_MAX_ZIP_SIZE_BYTES=209715200
```

Mặc định on-prem MVP:

- Một file nguồn tối đa **50 MB**.
- Một request multi-file/zip tối đa **20 file**.
- File zip tối đa **200 MB**; từng member trong zip vẫn tuân theo giới hạn file đơn.

API từ chối upload vượt giới hạn bằng HTTP `413`.

Frontend hiển thị policy tối thiểu qua:

```env
NUXT_PUBLIC_UPLOAD_MAX_FILE_SIZE_MB=50
NUXT_PUBLIC_UPLOAD_MAX_FILES=20
NUXT_PUBLIC_UPLOAD_MAX_ZIP_SIZE_MB=200
```

## Kiểm Tra Nhanh

Health/readiness trước khi test upload:

```bash
curl -fsS http://localhost:8000/health/ready
```

Smoke upload limits:

```bash
PYTHONPATH=apps/api python3 -m app.scripts.smoke_upload_limits
```

Hoặc trong container API:

```bash
docker compose exec -T api python -m app.scripts.smoke_upload_limits
```

## Troubleshoot

1. Worker bị OOM khi OCR scan lớn:
   - Tăng `WORKER_MEMORY_LIMIT`.
   - Giảm `UPLOAD_MAX_FILE_SIZE_BYTES` nếu file quá lớn so với RAM máy.
2. Upload bị `413`:
   - Kiểm tra kích thước file/zip và số file trong request.
   - Đối chiếu `.env` với policy ở trên.
3. Ổ đĩa uploads đầy:
   - Kiểm tra dung lượng volume `uploads_data`.
   - Backup và dọn file không còn dùng theo quy trình nghiệp vụ trước khi tăng limit.

Runbook liên quan:

```text
docs/LOG_POLICY_RUNBOOK.md
docs/WORKER_OPS_RUNBOOK.md
docs/ON_PREM_ENV_RUNBOOK.md
docs/STORAGE_BACKUP_RESTORE_RUNBOOK.md
```
