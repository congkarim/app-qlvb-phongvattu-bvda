# On-Prem Env Và Secret Runbook

Cập nhật lần cuối: 2026-06-06

## Mục Tiêu

Chuẩn hóa cấu hình `.env` cho Docker Compose nội bộ, tránh chạy production với secret hoặc mật khẩu admin mặc định.

## Local Development

Tạo file `.env` từ mẫu:

```bash
cp .env.example .env
```

Dev local có thể dùng fallback mặc định:

```env
APP_ENV=development
JWT_SECRET_KEY=local-dev-secret
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
POSTGRES_USER=legal
POSTGRES_PASSWORD=legal
DATABASE_URL=postgresql+psycopg://legal:legal@postgres:5432/legal_doc_ai
```

## Production Nội Bộ

Trước khi chạy production nội bộ, đặt tối thiểu:

```env
APP_ENV=production
JWT_SECRET_KEY=<random-secret-at-least-32-characters>
ADMIN_EMAIL=<admin-email-noi-bo>
ADMIN_PASSWORD=<strong-password-at-least-12-characters>
CORS_ALLOWED_ORIGINS=http://<internal-web-host>:3000
POSTGRES_PASSWORD=<strong-db-password>
DATABASE_URL=postgresql+psycopg://legal:<strong-db-password>@postgres:5432/legal_doc_ai
```

Không dùng:

```env
JWT_SECRET_KEY=local-dev-secret
JWT_SECRET_KEY=change-me-in-production
ADMIN_PASSWORD=admin123
CORS_ALLOWED_ORIGINS=*
DATABASE_URL=postgresql+psycopg://legal:legal@postgres:5432/legal_doc_ai
```

API sẽ từ chối khởi động khi `APP_ENV=production` mà vẫn dùng default JWT secret, default admin password, wildcard CORS hoặc default database credential.

## Kiểm Tra Cấu Hình

Kiểm tra Docker Compose render đúng biến:

```bash
docker compose config
```

Kiểm tra production guard chặn cấu hình mặc định:

```bash
docker compose run --rm --no-deps \
  -e APP_ENV=production \
  -e JWT_SECRET_KEY=local-dev-secret \
  -e ADMIN_PASSWORD=admin123 \
  -e CORS_ALLOWED_ORIGINS='*' \
  api python - <<'PY'
from app.core.config import Settings

try:
    Settings()
except ValueError as exc:
    print(str(exc).splitlines()[0])
else:
    raise SystemExit("expected production config validation failure")
PY
```

Kiểm tra production guard nhận cấu hình tối thiểu hợp lệ:

```bash
docker compose run --rm --no-deps \
  -e APP_ENV=production \
  -e JWT_SECRET_KEY='prod-secret-prod-secret-prod-secret-01' \
  -e ADMIN_PASSWORD='StrongAdminPass123' \
  -e CORS_ALLOWED_ORIGINS='http://intranet.local:3000' \
  -e DATABASE_URL='postgresql+psycopg://legal:strong-db-password@postgres:5432/legal_doc_ai' \
  api python - <<'PY'
from app.core.config import Settings

settings = Settings()
print(settings.is_production)
print(settings.cors_origins_list)
PY
```
