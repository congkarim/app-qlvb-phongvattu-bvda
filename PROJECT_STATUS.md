# Trạng Thái Dự Án

Cập nhật lần cuối: 2026-05-28

## Giai Đoạn Hiện Tại

MVP skeleton end-to-end đã được triển khai, đã kiểm tra thủ công và workflow web cơ bản đã được hoàn thiện.

Dự án hiện đang ở trạng thái có thể chạy đồng thời backend, worker, database, Qdrant, Redis và frontend Nuxt bằng Docker Compose. Người dùng có thể thao tác workflow MVP từ browser: upload văn bản, mở chi tiết, theo dõi trạng thái OCR, search và mở lại document nguồn.

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

Worker skeleton:
- Poll OCR job đang pending.
- Giả lập OCR.
- Lưu một OCR page.
- Tạo document chunks.
- Tạo fake deterministic embeddings.
- Upsert vector vào Qdrant.
- Chuyển document sang trạng thái `searchable`.

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
- Chưa triển khai xử lý PaddleOCR/OpenCV thật.
- Worker hiện đọc trực tiếp file `.txt` và `.md`.
- PDF/image chưa OCR thật.
- Office files như `.docx`, `.doc`, `.xlsx`, `.xls` chưa được trích xuất nội dung thật.
- Các loại file khác dùng text OCR giả lập.

Embedding:
- Embedding hiện là fake deterministic embedding.
- Chưa tích hợp local embedding model thật.

Search:
- Qdrant search đã chạy được cho skeleton flow.
- Điểm score chưa có ý nghĩa thực tế vì embedding còn giả.
- Metadata filters hiện còn tối thiểu.

Auth:
- Đã có JWT login skeleton.
- Chưa có seed admin user.
- Frontend chưa enforce auth route.

Frontend:
- UI hiện đã đủ cho MVP workflow cơ bản.
- Chưa có auth route guard.
- Chưa có layout/form polish ở mức production.

Generated files:
- Sau khi chạy dev server, Nuxt có thể sinh file trong `apps/web/.nuxt/`.
- Các file này đã nằm trong `.gitignore` và không phải source chính.

## Quyết Định Hiện Tại

Chưa triển khai OCR thật.

Task tiếp theo đã được chọn: bắt đầu OCR thật bằng PaddleOCR/OpenCV cho PDF/image và trích xuất text thật cho Office files trong worker.

Lý do chọn OCR trước auth/route guard:
- Workflow browser đã chạy được end-to-end.
- Giá trị vận hành hiện bị giới hạn bởi OCR giả lập.
- PDF/image scan và Office files là loại tài liệu thực tế cần xử lý trước khi đánh giá chất lượng search.

Workflow MVP hiện có:

```text
web upload -> document detail -> OCR status refresh -> searchable -> dashboard search -> open source document
```

Kế hoạch chi tiết nằm trong `TASK_NEXT.md`.
