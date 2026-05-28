# Legal Document AI

MVP local/on-prem cho quản lý văn bản, OCR skeleton và semantic search skeleton.

## Stack

- Backend: FastAPI, PostgreSQL, Redis, Qdrant, PaddleOCR, OpenCV
- Frontend: Nuxt 3, TypeScript, PrimeVue, TailwindCSS, Pinia
- Deploy local: Docker Compose

## Agent System

`AGENTS.md` chứa quy tắc chung cho Codex: stack cố định, kiến trúc backend/frontend, OCR pipeline và database conventions.

`.agents/skills/` chứa hướng dẫn theo domain:
- `backend-fastapi`
- `frontend-nuxt`
- `ocr-pipeline`
- `semantic-search-rag`
- `database-designer`
- `solution-architect`
- `project-git-manager`

Codex đọc `AGENTS.md`, sau đó chọn skill phù hợp với task. Chỉ tạo skill mới khi có domain kỹ thuật lặp lại nhiều lần và đủ khác biệt với các skill hiện có.

## Cấu Trúc

```text
apps/
  api/
  worker/
  web/
packages/
docker/
.agents/
AGENTS.md
docker-compose.yml
README.md
```

## Chạy Docker

```bash
docker compose up --build
```

API:

```bash
curl http://localhost:8000/health
```

Web:

```text
http://localhost:3000
```

## Test Workflow Bằng Browser

1. Mở web:

```text
http://localhost:3000
```

2. Vào `Upload`, chọn file `.txt`, bấm `Upload`.

3. Sau khi upload thành công, web mở trang chi tiết document:

```text
/documents/{document_id}
```

4. Ở trang detail, theo dõi:
- Metadata văn bản.
- OCR job status.
- OCR text.
- Chunks.

Trang detail tự refresh trạng thái cho tới khi document chuyển sang `searchable`.

5. Vào `Dashboard`, search:

```text
quản lý vật tư
```

6. Click kết quả search để mở lại document nguồn.

## Migrate DB

Chạy Postgres trước:

```bash
docker compose up -d postgres qdrant redis
```

Chạy migration:

```bash
docker compose run --rm api alembic upgrade head
```

## Start Backend/Frontend

Backend:

```bash
docker compose up api
```

Worker:

```bash
docker compose up worker
```

Frontend:

```bash
docker compose up web
```

## Test Upload API

Tạo file mẫu:

```bash
printf 'Điều 1. Quy định về quản lý vật tư. Khoản 1. Văn bản được OCR mô phỏng và lập chỉ mục semantic search.' > sample.txt
```

Upload:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload?document_type=document" \
  -F "file=@sample.txt"
```

Xem worker xử lý:

```bash
docker compose logs -f worker
```

List documents:

```bash
curl http://localhost:8000/api/v1/documents
```

## Test Semantic Search

Sau khi worker chuyển document sang `searchable`:

```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query":"quản lý vật tư","limit":5}'
```

## Ghi Chú MVP

- OCR hiện là skeleton: file `.txt`/`.md` đọc text trực tiếp, file khác tạo text mô phỏng.
- Embedding hiện là fake deterministic embedding để test luồng Qdrant.
- Workflow browser hiện hỗ trợ upload -> detail auto-refresh -> searchable -> dashboard search -> mở document nguồn.
- Chưa thêm cloud dependency, Kubernetes, CI/CD hoặc microservices.
