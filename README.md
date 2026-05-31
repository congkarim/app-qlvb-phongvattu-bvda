# Legal Document AI

MVP local/on-prem cho quản lý văn bản, OCR tài liệu scan, trích xuất nội dung Office và semantic search skeleton.

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

Login admin local:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
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

2. Đăng nhập bằng admin local được seed khi API khởi động:

```text
Email: admin@example.com
Password: admin123
```

3. Vào `Upload`, chọn file `.txt`, `.pdf`, ảnh, `.docx` hoặc `.xlsx`, bấm `Upload`.

4. Sau khi upload thành công, web mở trang chi tiết document:

```text
/documents/{document_id}
```

5. Ở trang detail, theo dõi:
- Metadata văn bản.
- OCR job status.
- OCR text.
- Chunks.

Trang detail tự refresh trạng thái cho tới khi document chuyển sang `searchable`.

6. Vào `Dashboard`, search:

```text
quản lý vật tư
```

7. Click kết quả search để mở lại document nguồn.

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

Các định dạng hiện hỗ trợ:
- `.txt`, `.md`: đọc text trực tiếp.
- `.docx`: trích xuất paragraph và table text.
- `.xlsx`, `.xls`: trích xuất text theo sheet và row.
- `.pdf`: ưu tiên trích xuất text nhúng bằng `pypdfium2`; page không có text mới render ảnh rồi OCR bằng PaddleOCR.
- `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.bmp`: OCR bằng PaddleOCR.
- `.doc`: chưa hỗ trợ trong MVP; worker đánh `failed` và yêu cầu convert sang `.docx` hoặc `.pdf`.

Upload Office/PDF/image:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload?document_type=document" \
  -F "file=@sample.docx"

curl -X POST "http://localhost:8000/api/v1/documents/upload?document_type=document" \
  -F "file=@sample.xlsx"

curl -X POST "http://localhost:8000/api/v1/documents/upload?document_type=document" \
  -F "file=@sample.pdf"
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

## Local Embedding Model

Mặc định Docker Compose vẫn dùng fake embedding để môi trường dev khởi động được ngay. Khi chạy semantic search thật, chuẩn bị model local trước rồi bật backend `sentence_transformers`.

Model khuyến nghị cho MVP tiếng Việt:

```text
bkai-foundation-models/vietnamese-bi-encoder
```

Đặt model đã tải sẵn vào:

```text
models/embeddings/bkai-vietnamese-bi-encoder
```

Ví dụ file `.env` để bật embedding thật:

```env
EMBEDDING_BACKEND=sentence_transformers
EMBEDDING_MODEL_NAME=bkai-foundation-models/vietnamese-bi-encoder
EMBEDDING_MODEL_PATH=/models/embeddings/bkai-vietnamese-bi-encoder
EMBEDDING_DEVICE=cpu
EMBEDDING_DIMENSIONS=768
EMBEDDING_BATCH_SIZE=16
EMBEDDING_LOCAL_FILES_ONLY=true
ALLOW_FAKE_EMBEDDINGS=false
QDRANT_COLLECTION=document_chunks_bkai_768_v1
```

Build lại image sau khi đổi dependencies:

```bash
docker compose build api worker
docker compose up -d postgres redis qdrant api worker
```

Reindex chunks hiện có sang collection đang cấu hình:

```bash
docker compose exec -T worker python -m app.scripts.reindex_embeddings --batch-size 16
```

Kiểm tra search:

```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query":"phạm vi điều chỉnh đấu thầu","limit":5}'
```

Lưu ý:
- Không dùng lại Qdrant collection cũ khi đổi model hoặc đổi `EMBEDDING_DIMENSIONS`.
- Mỗi model/dimension nên dùng collection version riêng, ví dụ `document_chunks_bkai_768_v1`.
- Nếu model local chưa có và `ALLOW_FAKE_EMBEDDINGS=false`, API/worker sẽ báo lỗi rõ ràng thay vì âm thầm dùng vector giả.

## Ghi Chú MVP

- PDF có text nhúng được đọc trực tiếp để giữ Unicode tiếng Việt; PDF/image scan vẫn OCR bằng PaddleOCR/OpenCV.
- Office text extraction đã chạy cho `.docx`, `.xlsx`, `.xls`.
- `.doc` legacy chưa hỗ trợ converter local trong MVP này.
- Embedding hỗ trợ fake deterministic cho dev và local `sentence-transformers` cho semantic search thật.
- API seed admin local mặc định `admin@example.com` / `admin123`.
- Frontend có route guard cơ bản và lưu token bằng cookie.
- Workflow browser hiện hỗ trợ upload -> detail auto-refresh -> searchable -> dashboard search -> mở document nguồn.
- PaddleOCR model được tải ở lần OCR đầu tiên nếu container chưa có cache model.
- Chưa thêm cloud dependency, Kubernetes, CI/CD hoặc microservices.
