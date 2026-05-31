# Trạng Thái Dự Án

Cập nhật lần cuối: 2026-05-31

## Giai Đoạn Hiện Tại

MVP end-to-end đã được triển khai, đã kiểm tra thủ công và workflow web cơ bản đã được hoàn thiện.

Dự án hiện đang ở trạng thái có thể chạy đồng thời backend, worker, database, Qdrant, Redis và frontend Nuxt bằng Docker Compose. Người dùng có thể đăng nhập bằng admin local, thao tác workflow MVP từ browser: upload văn bản, mở chi tiết, theo dõi trạng thái OCR/extract, search và mở lại document nguồn.

## Đã Xây Dựng

Hạ tầng agent:
- `AGENTS.md`
- `.agents/skills/backend-fastapi/SKILL.md`
- `.agents/skills/frontend-nuxt/SKILL.md`
- `.agents/skills/ocr-pipeline/SKILL.md`
- `.agents/skills/semantic-search-rag/SKILL.md`
- `.agents/skills/database-designer/SKILL.md`
- `.agents/skills/solution-architect/SKILL.md`
- `.agents/skills/project-git-manager/SKILL.md`

Quản lý repo:
- Đã thêm skill `project-git-manager` để quy định workflow git cho đầu task, trong task và khi hoàn thành task.
- Skill yêu cầu cập nhật `PROJECT_STATUS.md`, `TASK_NEXT.md` hoặc `README.md` khi task làm thay đổi trạng thái/kế hoạch/cách chạy dự án.
- Skill quy định commit có chọn lọc sau khi task hoàn thành và kiểm tra phù hợp đã chạy.

Docker services:
- `api`
- `worker`
- `web`
- `postgres`
- `redis`
- `qdrant`

Backend skeleton:
- FastAPI app.
- Health endpoint.
- Auth login skeleton.
- Upload API.
- API danh sách/chi tiết văn bản.
- Model và repository cho OCR job.
- Semantic search endpoint.
- Alembic migration ban đầu cho:
  - `users`
  - `departments`
  - `documents`
  - `document_pages`
  - `document_chunks`
  - `ocr_jobs`

Worker:
- Poll OCR job đang pending.
- Trích xuất text trực tiếp cho `.txt`, `.md`, `.docx`, `.xlsx`, `.xls`.
- PDF có text nhúng được trích xuất trực tiếp bằng `pypdfium2` để giữ Unicode tiếng Việt.
- OCR thật cho PDF/image scan bằng PaddleOCR/OpenCV khi page không có text nhúng.
- Render PDF scan thành image từng page bằng `pypdfium2`.
- Preprocess ảnh bằng OpenCV trước OCR.
- Lưu OCR/extracted text theo page logic.
- Tạo document chunks, giới hạn `section_title` ngắn hơn schema PostgreSQL để tránh lỗi insert.
- Tạo embedding qua backend cấu hình được: fake deterministic cho dev hoặc local `sentence-transformers`.
- Upsert vector vào Qdrant.
- Chuyển document sang trạng thái `searchable`.
- Đánh document/job `failed` với error rõ ràng cho định dạng lỗi hoặc unsupported như `.doc`.

Frontend skeleton:
- Nuxt 3 app.
- PrimeVue plugin.
- TailwindCSS.
- Pinia auth store.
- Các page:
  - `/login`
  - `/dashboard`
  - `/documents`
  - `/upload`
  - `/documents/[id]`
- Cấu trúc service/composable:
  - `page -> composable -> service -> API`

Auth MVP:
- API seed admin local khi khởi động nếu chưa tồn tại.
- Admin mặc định cho Docker Compose: `admin@example.com` / `admin123`.
- Frontend lưu access token bằng cookie.
- API client frontend tự gắn `Authorization: Bearer <token>`.
- Frontend có route guard cơ bản: chưa login thì chuyển về `/login`, đã login thì không quay lại `/login`.

Workflow web đã hoàn thiện:
- `/upload` hiển thị thông tin file đã chọn, loading/error state và tự mở document detail sau upload.
- `/documents/[id]` hiển thị metadata, OCR job status, OCR text, chunks và tự polling tới khi document `searchable`.
- `/documents` có refresh action, loading state, empty state và link sang detail.
- `/dashboard` có validation search input, loading/empty/error state và result link sang document nguồn.

## Đã Kiểm Tra Thủ Công

Các kiểm tra sau đã chạy thành công:

```bash
docker compose up --build
```

```bash
curl http://localhost:8000/health
```

Test upload:

```bash
printf 'Điều 1. Quy định về quản lý vật tư. Khoản 1. Văn bản được OCR mô phỏng và lập chỉ mục semantic search.' > sample.txt

curl -X POST "http://localhost:8000/api/v1/documents/upload?document_type=document" \
  -F "file=@sample.txt"
```

Test trích xuất/OCR đã chạy thành công cho:
- `.txt`: đọc text trực tiếp, document chuyển `searchable`.
- `.docx`: trích xuất paragraph/table text, document chuyển `searchable`.
- `.xlsx`: trích xuất sheet/row text, document chuyển `searchable`.
- `.png`: OCR thật bằng PaddleOCR, document chuyển `searchable`.
- `.pdf`: trích xuất text nhúng trước, fallback OCR cho page scan, document chuyển `searchable`.
- `.doc`: document/job chuyển `failed` với message yêu cầu convert sang `.docx` hoặc `.pdf`.

Test semantic search:

```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query":"quản lý vật tư","limit":5}'
```

Frontend routes đã kiểm tra:
- `http://localhost:3000/` redirect sang `/dashboard`.
- `http://localhost:3000/dashboard` trả 200.
- `http://localhost:3000/documents` trả 200.
- Browser workflow đã được chuẩn bị cho upload -> detail polling -> search.

Auth kiểm tra ngày 2026-05-31:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

Kết quả: HTTP 200, response có `access_token` và `token_type= bearer`.

## Lỗi Đã Sửa

Docker/runtime:
- Thêm `email-validator` vì Pydantic `EmailStr` cần package này.
- Bỏ Alembic migration khỏi startup của worker để tránh race condition.
- Thêm healthcheck cho API.
- Worker đợi API healthy rồi mới start.

Frontend:
- Sửa lỗi `useApiClient is not defined` bằng cách import explicit `useApiClient` trong các frontend service.

## Giới Hạn Hiện Tại

OCR:
- Đã triển khai OCR thật cho PDF/image scan bằng PaddleOCR/OpenCV.
- PDF có text nhúng được trích xuất trực tiếp bằng `pypdfium2` trước khi fallback OCR để giữ dấu tiếng Việt.
- Worker đọc trực tiếp file `.txt` và `.md`.
- Worker trích xuất text thật từ `.docx`, `.xlsx`, `.xls`.
- `.doc` legacy chưa hỗ trợ LibreOffice converter, hiện fail rõ ràng.
- PaddleOCR model có thể được tải ở lần OCR đầu tiên nếu container chưa có model cache.

Chunking:
- Đã sửa lỗi `section_title` quá dài làm PostgreSQL báo `value too long for type character varying(512)`.
- Các document VBHN lỗi cũ đã reprocess lại, trạng thái `searchable/completed`.

Embedding:
- Đã thêm backend local `sentence-transformers` có thể bật bằng env.
- Mặc định Docker Compose vẫn dùng fake embedding để dev khởi động nhanh.
- Model khuyến nghị: `bkai-foundation-models/vietnamese-bi-encoder`, `EMBEDDING_DIMENSIONS=768`.
- Đã thêm script reindex chunks hiện có sang Qdrant collection đang cấu hình.

Search:
- Qdrant search đã chạy được cho skeleton flow.
- Score có ý nghĩa hơn khi bật local embedding thật và reindex sang collection version mới.
- Metadata filters hiện còn tối thiểu.

Auth:
- Đã có JWT login skeleton.
- Đã có seed admin local.
- Frontend đã có route guard cơ bản.
- API tài liệu/search hiện chưa enforce backend authorization dependency, mới kiểm soát truy cập ở frontend MVP.

Frontend:
- UI hiện đã đủ cho MVP workflow cơ bản.
- Đã có auth route guard cơ bản.
- Chưa có layout/form polish ở mức production.

Generated files:
- Sau khi chạy dev server, Nuxt có thể sinh file trong `apps/web/.nuxt/`.
- Các file này đã nằm trong `.gitignore` và không phải source chính.

## Quyết Định Hiện Tại

OCR thật và trích xuất Office text mức MVP đã được triển khai.

Task tiếp theo nên ưu tiên chuẩn bị model local trong `models/embeddings`, bật env `sentence_transformers`, reindex dữ liệu thật và benchmark truy vấn tiếng Việt.

Workflow MVP hiện có:

```text
web upload -> document detail -> OCR status refresh -> searchable -> dashboard search -> open source document
```

Chi tiết task vừa hoàn thành nằm trong `TASK_NEXT.md`.
