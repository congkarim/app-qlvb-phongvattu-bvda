# Task Đã Hoàn Thành: Bổ Sung Admin Seed Và Route Guard MVP

Trạng thái: đã triển khai.

Ngày tạo: 2026-05-31

Ngày hoàn thành: 2026-05-31

## Kết Quả

Đã triển khai:
- API seed admin local khi FastAPI khởi động nếu tài khoản chưa tồn tại.
- Cấu hình admin qua settings/env: `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_FULL_NAME`.
- Admin mặc định Docker Compose: `admin@example.com` / `admin123`.
- Chuyển password hashing sang `pbkdf2_sha256` của `passlib` để tránh lỗi tương thích binary `bcrypt`.
- Frontend lưu token bằng cookie `auth_token`.
- Frontend API client tự gắn `Authorization: Bearer <token>`.
- Nuxt global route middleware bảo vệ các route MVP.

## Kiểm Tra Đã Chạy

```bash
docker compose config
```

```bash
python3 - <<'PY'
import ast
from pathlib import Path
for path in Path('apps/api/app').rglob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
print('python syntax ok')
PY
```

```bash
docker compose run --rm web npm run build
```

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

Kết quả login: HTTP 200, response có `access_token` và `token_type= bearer`.

## Giới Hạn Còn Lại

- Backend documents/search endpoints chưa enforce JWT dependency, route guard hiện mới ở frontend MVP.
- Chưa có user management UI.
- Chưa có refresh token hoặc logout button ở layout.
- Embedding vẫn là fake deterministic embedding.

## Task Tiếp Theo Đề Xuất

Tích hợp local embedding model thật để score semantic search có ý nghĩa hơn.

Phạm vi gợi ý:
- Chọn embedding model local/on-prem phù hợp tiếng Việt.
- Thêm config model path/name và vector dimensions.
- Điều chỉnh Qdrant collection strategy khi dimensions thay đổi.
- Giữ fallback rõ ràng nếu model chưa được tải/cấu hình.
- Cập nhật README với cách chuẩn bị model và test semantic search.
