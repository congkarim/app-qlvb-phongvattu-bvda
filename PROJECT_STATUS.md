# Trạng Thái Dự Án

Cập nhật lần cuối: 2026-06-04

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
- OCR scan tiếng Việt mặc định chạy `OCR_ENGINE=paddle_vietocr`: PaddleOCR detect text box, VietOCR recognize crop tiếng Việt.
- PaddleOCR baseline vẫn giữ được bằng `OCR_ENGINE=paddleocr`.
- Render PDF scan thành image từng page bằng `pypdfium2`.
- Preprocess ảnh bằng OpenCV trước OCR, hỗ trợ `OCR_PREPROCESS_MODE=auto/raw/clahe/threshold`.
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
- `/documents/[id]` có action reprocess, khóa nút khi document đang `ocr_pending`, `ocr_running`, `reprocess_pending`, `reprocess_running` hoặc `chunking`.
- `/documents/[id]` hiển thị audit OCR/reprocess job gồm `job_type`, `status`, `reason`, attempts, error message và thời gian tạo/cập nhật.
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

OCR tiếng Việt kiểm tra ngày 2026-06-01:

```bash
docker compose config
docker compose build api worker
docker compose up -d api worker
docker compose exec -T worker sh -lc 'python -m py_compile /app/app/core/config.py /app/app/services/document_content_service.py /app/app/services/ocr/*.py /app/app/scripts/benchmark_ocr_vi.py'
curl -fsS http://localhost:8000/health
```

Kết quả `OCR_ENGINE=paddle_vietocr` trên fixture `tests/fixtures/ocr_vi/sample_001.png`:

```text
confidence=0.9259
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc
Điều 1. Phạm vi điều chỉnh đấu thầu
Khoản 1. Văn bản scan phải giữ dấu tiếng Việt.
Số 74/VBHN-VPQH ngày 15 tháng 5 năm 2025.
```

Benchmark fixture:

```text
paddleocr: CER 0.0053, WER 0.0238, accent loss 0.0294, 34.944s
paddle_vietocr: CER 0.0, WER 0.0, accent loss 0.0, 49.487s
```

OCR fixture mở rộng kiểm tra ngày 2026-06-02:

```bash
docker compose config --quiet
docker compose run --rm --no-deps worker python -m py_compile /app/app/scripts/benchmark_ocr_vi.py
docker compose run --rm --no-deps -e OCR_PREPROCESS_MODE=raw worker python -m py_compile /app/app/scripts/benchmark_ocr_vi.py /app/tests/fixtures/ocr_vi/generate_fixtures.py
docker compose run --rm --no-deps -e OCR_PREPROCESS_MODE=raw worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --engine all --format json
```

Kết quả chính:
- Đã mở rộng `tests/fixtures/ocr_vi` lên 6 fixture không nhạy cảm, gồm 5 ảnh scan và 1 PDF scan 2 trang.
- `benchmark_ocr_vi.py` đã benchmark được cả PDF, gom text nhiều page và báo runtime/page.
- Với `OCR_PREPROCESS_MODE=raw`, `paddle_vietocr` giữ dấu tiếng Việt tốt hơn `paddleocr` trên các mẫu scan rõ, scan mờ và ảnh nghiêng.
- `sample_004.png` hai cột vẫn sai thứ tự đọc; đây là lỗi layout/detection cần xử lý riêng.
- `sample_006.pdf` giữ dấu tốt hơn với VietOCR nhưng còn tách dòng tiêu đề; runtime khoảng 39.6s/page.
- Benchmark full với `OCR_PREPROCESS_MODE=auto` bị dừng sau hơn 5 phút vì quá chậm cho kiểm tra thường xuyên.

OCR tài liệu thực tế kiểm tra ngày 2026-06-02:

```bash
docker compose ps
docker compose logs --tail=160 worker
docker compose exec -T postgres psql -U legal -d legal_doc_ai -c "select id, original_filename, content_type, document_type, status, created_at, updated_at from documents order by created_at desc limit 8;"
docker compose exec -T postgres psql -U legal -d legal_doc_ai -c "select j.document_id, d.original_filename, j.status as job_status, d.status as doc_status, j.attempts, j.error_message, j.updated_at from ocr_jobs j join documents d on d.id=j.document_id order by j.created_at desc limit 4;"
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Lê Thế Anh hồ sơ xin thôi việc Xuân Lâm","limit":5}'
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Luật Đấu thầu phạm vi điều chỉnh","limit":5}'
```

Kết quả:
- `22-qh-15.signed.pdf`: document `searchable`, OCR job `completed`, 84 pages, 184 chunks, average confidence `0.9272`, total OCR text `175497` chars.
- `0f53863c-d731-4b39-b0ff-d883ab039a88.jpeg`: document `searchable`, OCR job `completed`, 1 page, 1 chunk, confidence `0.9037`.
- Qdrant đã nhận upsert cho PDF lúc `2026-06-02T08:26:44Z` và JPEG lúc `2026-06-02T08:28:05Z`.
- Search `Lê Thế Anh hồ sơ xin thôi việc Xuân Lâm` trả JPEG mới nhất ở top 1.
- Search `Luật Đấu thầu phạm vi điều chỉnh` có chunk đúng `Điều 1. Phạm vi điều chính` nhưng chỉ đứng thứ 5, đồng thời kết quả còn lẫn bản PDF upload cũ.

Lỗi OCR thực tế đã thấy:
- PDF `22-qh-15.signed.pdf`: giữ dấu tiếng Việt khá tốt nhưng có lỗi từ như `LUẶT`, `điều chính`, `dầu khi`, và dấu phân tách header `CÔNG BÁO/SỐ 869 ? 870`.
- JPEG công văn xã Xuân Lâm: có hallucination/nhiễu như `Thuật`, `Nhất`, `Thành`, `Nhà Tháng`, `Các thuận`; số hiệu/ngày có lỗi `72]`, `27IS/2026`.
- Search cần dedup/reranking vì cùng file `22-qh-15.signed.pdf` đã được upload nhiều lần và chunk đúng không luôn đứng top 1.

Tối ưu OCR/search kiểm tra ngày 2026-06-02:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/services/document_content_service.py /app/app/services/ocr/paddle_vietocr_engine.py /app/app/services/search_service.py /app/app/workers/ocr_worker.py /app/app/scripts/reindex_embeddings.py
docker compose run --rm --no-deps -e OCR_PREPROCESS_MODE=raw worker python - <<'PY'
from pathlib import Path
from app.services.document_content_service import DocumentContentService
service = DocumentContentService()
service.settings = service.settings.model_copy(update={"ocr_engine": "paddle_vietocr", "ocr_preprocess_mode": "raw"})
page = service.extract_pages(Path('/app/tests/fixtures/ocr_vi/sample_004.png'), 'sample_004.png')[0]
print(page.text)
PY
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Luật Đấu thầu phạm vi điều chỉnh","limit":5}'
```

Kết quả:
- `sample_004.png` đã đọc đúng thứ tự cột: tiêu đề, toàn bộ `Điều 5. Kiểm kê vật tư`, sau đó đến `Điều 6. Báo cáo sử dụng`.
- JPEG công văn xã Xuân Lâm khi OCR lại bằng code mới đạt confidence `0.9043`; số hiệu đọc đúng `Số: 72/UBND-KT`, ngày đọc đúng `27/5/2026`, giảm các nhiễu `Thuật`, `Nhất`, `Thành`, `Nhà Tháng`, `Các thuận`, `1990`, `1992`, `E`, `16`, `6n`, `2`.
- Search `Luật Đấu thầu phạm vi điều chỉnh` đưa chunk `Điều 1. Phạm vi điều chính` lên top 2 và top 5 không còn lẫn các bản upload cũ của cùng file PDF.

Tối ưu PDF scan và search kiểm tra bổ sung ngày 2026-06-02:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/scripts/benchmark_ocr_vi.py /app/app/services/document_content_service.py /app/app/services/search_service.py
docker compose run --rm --no-deps -e OCR_PREPROCESS_MODE=raw worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --files sample_006.pdf --engine paddle_vietocr --format json
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Luật Đấu thầu phạm vi điều chỉnh","limit":5}'
```

Kết quả:
- `benchmark_ocr_vi.py` có chế độ kiểm tra nhanh bằng `--files` và `--limit`, tránh phải chạy toàn bộ fixture khi chỉ cần kiểm tra một file/page.
- `sample_006.pdf` với `paddle_vietocr` và `OCR_PREPROCESS_MODE=raw` đạt `CER=0.0`, `WER=0.0`, `accent_loss=0.0`; tiêu đề đã nối đúng `TỔNG CÔNG TY HẠ TẦNG KỸ THUẬT` và `KẾ HOẠCH MUA SẮM VẬT TƯ NĂM 2026`.
- OCR riêng page 1 của `22-qh-15.signed.pdf` đạt confidence `0.9256`; header đọc đúng `CÔNG BÁO/SỐ 869 + 870/NGÀY 31-7-2023`, `LUẬT`, `ĐẦU THẦU`, `Điều 1. Phạm vi điều chỉnh`.
- Search `Luật Đấu thầu phạm vi điều chỉnh` đưa chunk `Điều 1. Phạm vi điều chính` lên top 1.

Giảm runtime OCR benchmark và reindex payload kiểm tra ngày 2026-06-03:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/scripts/benchmark_ocr_vi.py /app/app/services/ocr/__init__.py /app/tests/fixtures/ocr_vi/generate_fixtures.py
docker compose run --rm --no-deps worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --files sample_001.png --engine paddle_vietocr --preprocess-mode raw clahe --format json
docker compose exec -T api python -m app.scripts.reindex_embeddings --dry-run
docker compose exec -T api python -m app.scripts.reindex_embeddings
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Luật Đấu thầu phạm vi điều chỉnh","limit":5}'
```

Kết quả:
- `benchmark_ocr_vi.py` hỗ trợ `--preprocess-mode raw/clahe/threshold/auto/all`, output có cột `preprocess_mode`.
- Benchmark tái sử dụng `DocumentContentService` theo engine/preprocess mode; OCR engine cache không còn phụ thuộc preprocess mode nên không khởi tạo lại model khi chỉ đổi preprocess.
- Benchmark nhanh `sample_001.png` với `paddle_vietocr`:
  - `raw`: CER `0.0`, WER `0.0`, accent loss `0.0`, confidence `0.9264`, runtime `20.682s`.
  - `clahe`: CER `0.0`, WER `0.0`, accent loss `0.0`, confidence `0.9259`, runtime `11.944s`.
- Đã thêm fixture không nhạy cảm `sample_007.png` mô phỏng công văn xã/phòng ban với header hai bên, số hiệu, ngày tháng, kính gửi, nội dung yêu cầu, dấu mộc và nhiễu nhẹ.
- Benchmark `sample_007.png` với `paddle_vietocr/raw`: confidence `0.9228`, accent loss `0.0`; còn lỗi thứ tự header và thiếu một phần dòng liên hệ, phù hợp để theo dõi hồi quy OCR công văn.
- Reindex dry-run xác nhận `453` chunks; reindex thật đã index `453` chunks vào Qdrant collection `document_chunks_bkai_768_v1`.
- Kiểm tra Qdrant payload mẫu cho thấy các point đã có `content_hash`.
- Search `Luật Đấu thầu phạm vi điều chỉnh` sau reindex vẫn trả chunk `Điều 1. Phạm vi điều chính` ở top 1.

Cải thiện OCR công văn và hybrid search kiểm tra ngày 2026-06-03:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/services/document_content_service.py /app/app/services/ocr/paddle_vietocr_engine.py /app/app/services/search_service.py /app/app/repositories/document_repository.py /app/app/routers/search.py
docker compose run --rm --no-deps worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --files sample_007.png --engine paddle_vietocr --preprocess-mode raw clahe threshold --format json
docker compose run --rm --no-deps worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --files sample_007.png --engine paddle_vietocr --preprocess-mode auto --format json
docker compose up -d --build api
curl -fsS http://localhost:8000/health
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Luật Đấu thầu phạm vi điều chỉnh","limit":3}'
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Nghị định 192 2026 chế độ phụ cấp đặc thù lĩnh vực y tế","limit":3}'
```

Kết quả:
- `sample_007.png` đã cải thiện ordering header hai bên: phần `ỦY BAN NHÂN DÂN XÃ MINH PHÚ`, `PHÒNG KINH TẾ`, `Số: 72/UBND-KT` đứng trước tiêu ngữ bên phải, không còn xen kẽ từng dòng.
- OCR postprocess nối lại các dòng tiêu ngữ, tên xã, ngày tháng và các câu nội dung bị tách dòng; lọc nhiễu `000001`/`CHUNICH` và sửa `số điện thoai` -> `số điện thoại`, `MINH PHỦ` -> `MINH PHÚ`.
- Chế độ `auto` ưu tiên kết quả có marker hành chính/pháp lý như `Số:`, `Kính gửi`, `Người liên hệ`, `Điều`, `Khoản`, giúp giữ được dòng liên hệ khi preprocess `threshold` phát hiện tốt hơn.
- Benchmark `sample_007.png`:
  - Trước tối ưu `raw`: CER `0.4241`, WER `0.4907`, confidence `0.9228`.
  - Sau tối ưu `raw`: CER `0.2342`, WER `0.2963`, confidence `0.9266`.
  - Sau tối ưu `auto`: CER `0.2658`, WER `0.2963`, confidence `0.9252`, giữ `Người liên hệ: Nguyễn Văn An, số điện thoại 0900`.
- Search service đã chuyển sang hybrid retrieval: Qdrant vector candidates + PostgreSQL keyword candidates trên `document_chunks.text`, sau đó rerank/dedup chung.
- Router search truyền DB session vào service, giữ kiến trúc `router -> service -> repository`.
- Search response `score` hiện là hybrid rerank score để thứ tự kết quả và điểm hiển thị nhất quán.
- Query `Luật Đấu thầu phạm vi điều chỉnh` vẫn trả chunk `Điều 1. Phạm vi điều chính` top 1.
- Query `Nghị định 192 2026 chế độ phụ cấp đặc thù lĩnh vực y tế` vẫn trả đúng `Điều 1` của file nghị định 192 top 1.

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
- Đã tích hợp VietOCR local cho nhận dạng tiếng Việt có dấu; mặc định `OCR_ENGINE=paddle_vietocr`.
- Đã nâng OCR scan lên PaddleOCR 3.3.0/PP-OCRv5 để detect/crop text line; `OCR_ENGINE=paddleocr` vẫn dùng recognizer Latin `latin_PP-OCRv5_mobile_rec` làm baseline/fallback thủ công.
- Có cấu hình OCR qua env: `OCR_ENGINE`, `OCR_LANG`, `OCR_DEVICE`, `OCR_MODEL_DIR`, `OCR_PREPROCESS_MODE`, `OCR_MIN_CONFIDENCE`, `OCR_RESTORE_VIETNAMESE_TERMS`, `VIETOCR_MODEL_DIR`, `VIETOCR_DEVICE`, `VIETOCR_CONFIG`, `VIETOCR_WEIGHT_PATH`.
- PDF có text nhúng được trích xuất trực tiếp bằng `pypdfium2` trước khi fallback OCR để giữ dấu tiếng Việt.
- Worker đọc trực tiếp file `.txt` và `.md`.
- Worker trích xuất text thật từ `.docx`, `.xlsx`, `.xls`.
- `.doc` legacy chưa hỗ trợ LibreOffice converter, hiện fail rõ ràng.
- PaddleOCR model có thể được tải ở lần OCR đầu tiên nếu container chưa có model cache.
- Nếu chuẩn bị sẵn `models/ocr/PP-OCRv5_server_det` và `models/ocr/latin_PP-OCRv5_mobile_rec`, worker sẽ dùng model local qua `/models/ocr`.
- VietOCR weight local đã được chuẩn bị tại `models/ocr/vietocr/transformerocr.pth` trên máy local và không được commit.
- Nếu `OCR_ENGINE=paddle_vietocr` nhưng thiếu `VIETOCR_WEIGHT_PATH`, worker báo `FileNotFoundError` rõ ràng.
- Chất lượng OCR scan xấu vẫn phụ thuộc detection box và chất lượng crop; fixture hai cột đã được cải thiện bằng column-aware line ordering.
- PDF scan với VietOCR giữ dấu tốt hơn baseline; page 1 PDF thật và fixture PDF scan đã giảm lỗi header/tiêu đề, nhưng runtime vẫn cao.
- Tài liệu thực tế upload từ web đã chạy hết pipeline đến `searchable`; JPEG công văn đã giảm lỗi số hiệu/ngày tháng và nhiễu từ khi OCR lại bằng code mới, nhưng vẫn cần theo dõi thêm trên nhiều ảnh scan thật.
- Fixture công văn `sample_007.png` đã cải thiện rõ thứ tự header và giữ được số hiệu/ngày/kính gửi; với `auto` đã giữ được dòng `Người liên hệ`, nhưng số điện thoại vẫn có thể bị thiếu phần cuối nếu detection không bắt đủ vùng chữ.

Chunking:
- Đã sửa lỗi `section_title` quá dài làm PostgreSQL báo `value too long for type character varying(512)`.
- Các document VBHN lỗi cũ đã reprocess lại, trạng thái `searchable/completed`.

Embedding:
- Đã thêm backend local `sentence-transformers` có thể bật bằng env.
- Mặc định Docker Compose có thể dùng fake embedding để dev khởi động nhanh, nhưng `.env` local hiện đã bật `sentence_transformers`.
- Model khuyến nghị: `bkai-foundation-models/vietnamese-bi-encoder`, `EMBEDDING_DIMENSIONS=768`.
- Đã thêm script reindex chunks hiện có sang Qdrant collection đang cấu hình.
- Model BKAI đã được chuẩn bị local tại `models/embeddings/bkai-vietnamese-bi-encoder`.

Search:
- Qdrant search đã chạy được cho skeleton flow.
- Score có ý nghĩa hơn khi bật local embedding thật và reindex sang collection version mới.
- Đã reindex 1.584 chunks sang Qdrant collection `document_chunks_bkai_768_v1`, vector size `768`.
- Benchmark 5 query tiếng Việt cho kết quả đúng ngữ cảnh hơn fake embedding, đặc biệt với `hiệu lực thi hành luật đấu thầu`, `trách nhiệm của chủ đầu tư`, `lựa chọn nhà thầu`.
- Semantic search đã có reranking/dedup nhẹ: lấy nhiều hit hơn từ Qdrant, boost exact legal markers và giảm kết quả yếu trùng theo document/title/text.
- Semantic search đã có hybrid retrieval MVP: lấy candidate từ Qdrant vector và PostgreSQL keyword, cộng tín hiệu exact phrase/term coverage trước khi dedup.
- Keyword search có migration `0002_chunk_text_trgm` tạo extension `pg_trgm` và GIN trigram index `ix_document_chunks_text_trgm` trên `document_chunks.text` cho các chunk chưa soft delete.
- Query `Luật Đấu thầu phạm vi điều chỉnh` đã đưa chunk Điều 1 lên top 1 và giảm bản upload cũ trong top 5.
- Metadata filters hiện còn tối thiểu.

Reprocess công văn cũ và tối ưu keyword index kiểm tra ngày 2026-06-03:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/scripts/reprocess_document.py /app/app/repositories/document_repository.py /app/app/services/qdrant_service.py /app/alembic/versions/0002_document_chunk_text_trgm_index.py
docker compose exec -T api alembic upgrade head
docker compose exec -T postgres psql -U legal -d legal_doc_ai -c "EXPLAIN ANALYZE ..."
docker compose exec -T api python -m app.scripts.reprocess_document --document-id 718b0db1-6c8c-4da4-b6aa-5689173d219a --dry-run
docker compose exec -T api python -m app.scripts.reprocess_document --document-id 718b0db1-6c8c-4da4-b6aa-5689173d219a
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Lê Thế Anh hồ sơ xin thôi việc Xuân Lâm","limit":3}'
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Số 72 UBND KT Kính gửi Ban chỉ huy 32 xóm","limit":3}'
```

Kết quả:
- Thêm script `python -m app.scripts.reprocess_document --document-id <id>` để OCR lại file đã upload, replace page/chunk theo document, upsert lại Qdrant và xóa point dư nếu số chunk giảm.
- Reprocess công văn JPEG `0f53863c-d731-4b39-b0ff-d883ab039a88.jpeg`:
  - Dry-run: `old_pages=1`, `new_pages=1`, `old_chunks=1`, `new_chunks=1`, average confidence `0.9043`.
  - Reprocess thật: document vẫn `searchable`, `1/1` chunk có `content_hash` và `qdrant_point_id`, không có chunk dư.
- Text sau reprocess đã cải thiện các lỗi cũ:
  - `Số: 72]/UBND-KT` -> `Số: 72/UBND-KT`.
  - `27IS/2026` -> `27/5/2026`.
  - Bỏ nhiễu đầu dòng như `Thuật`, `Nhất`, `Thành`, `Nhà Tháng`, `Các thuận`, `Anh thuận`.
  - `Thông bảo` -> `Thông báo`.
- Search `Lê Thế Anh hồ sơ xin thôi việc Xuân Lâm` trả công văn JPEG đã cleanup ở top 1.
- Search `Số 72 UBND KT Kính gửi Ban chỉ huy 32 xóm` trả công văn JPEG đã cleanup ở top 1.
- `EXPLAIN ANALYZE` trước index dùng seq scan trên `document_chunks.text`, khoảng `23ms` với 478 chunks.
- Sau migration, planner vẫn chọn seq scan do bảng nhỏ, nhưng khi `enable_seqscan=off` xác nhận index trigram usable bằng `Bitmap Index Scan`, khoảng `4.8ms` cho query keyword đại diện.

API reprocess document có audit kiểm tra ngày 2026-06-03:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/models/document.py /app/app/repositories/document_repository.py /app/app/services/document_service.py /app/app/routers/documents.py /app/app/schemas/document.py /app/app/workers/ocr_worker.py /app/alembic/versions/0003_ocr_job_type.py
docker compose up -d --build api worker
curl -fsS http://localhost:8000/health
docker compose exec -T api alembic current
curl -fsS -X POST http://localhost:8000/api/v1/documents/718b0db1-6c8c-4da4-b6aa-5689173d219a/reprocess -H 'Content-Type: application/json' -d '{"reason":"verify reprocess API workflow"}'
curl -fsS http://localhost:8000/api/v1/documents/718b0db1-6c8c-4da4-b6aa-5689173d219a
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Số 72 UBND KT Kính gửi Ban chỉ huy 32 xóm","limit":3}'
```

Kết quả:
- Thêm API `POST /api/v1/documents/{document_id}/reprocess`.
- Request body hỗ trợ `reason` để audit lý do reprocess.
- API không OCR inline; chỉ tạo `ocr_jobs` mới với `job_type='reprocess'`, `status='pending'`, document chuyển `reprocess_pending`, worker xử lý async.
- Thêm migration `0003_ocr_job_type` cho `ocr_jobs.job_type` và `ocr_jobs.reason`.
- Worker phân biệt `job_type='ocr'` và `job_type='reprocess'`:
  - OCR lần đầu vẫn create page/chunk mới.
  - Reprocess replace page/chunk hiện có, upsert lại Qdrant, xóa point dư nếu số chunk giảm.
- Worker commit trạng thái `ocr_running` hoặc `reprocess_running` ngay khi bắt đầu để API/UI thấy trạng thái đang xử lý.
- Nếu reprocess lỗi, document quay về trạng thái trước đó thay vì mất trạng thái `searchable`.
- Kiểm tra API trên document `718b0db1-6c8c-4da4-b6aa-5689173d219a`:
  - API trả `202 Accepted`, job `6a154fc5-e3f6-4f45-b929-d59db6566163`, `job_type='reprocess'`, `reason='verify reprocess API workflow'`.
  - Worker xử lý xong: job `completed`, attempts `1`, document `searchable`.
  - Detail API trả cả job OCR ban đầu `job_type='ocr'` và job reprocess `job_type='reprocess'`.
  - Document vẫn có `1/1` chunk active, có `content_hash` và `qdrant_point_id`.
  - Search `Số 72 UBND KT Kính gửi Ban chỉ huy 32 xóm` vẫn trả công văn JPEG top 1.

UI reprocess và job audit kiểm tra ngày 2026-06-04:

```bash
docker compose run --rm --no-deps web npm run build
```

Kết quả:
- Frontend document service đã có `reprocess(id, reason)` gọi `POST /api/v1/documents/{document_id}/reprocess`.
- Composable `useDocuments` đã có action `reprocessDocument` và loading state riêng cho reprocess.
- Trang `/documents/[id]` đã có form nhập lý do reprocess, nút reprocess, polling lại detail sau khi tạo job và không cho bấm khi document đang xử lý.
- Trang `/documents/[id]` đã hiển thị danh sách audit OCR/reprocess job thay vì chỉ job mới nhất.
- Nuxt production build trong Docker Compose hoàn tất thành công.

Sửa lỗi Nuxt dev app manifest ngày 2026-06-04:

```bash
docker compose run --rm --no-deps web npm run build
docker compose up -d --build web
curl -fsS -I http://localhost:3000/login
docker compose logs --tail=160 web | rg -n "#app-manifest|Pre-transform|ERROR|Failed to resolve" || true
```

Kết quả:
- Tắt `experimental.appManifest` trong Nuxt vì MVP hiện không dùng route rules/app manifest.
- Dev server không còn lỗi Vite pre-transform `Failed to resolve import "#app-manifest"`.
- `/login` trả HTTP 200 sau khi rebuild service `web`.

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

OCR thật và trích xuất Office text mức MVP đã được triển khai. OCR scan tiếng Việt hiện ưu tiên VietOCR local.

Task tiếp theo nên ưu tiên thêm API hoặc admin action để reprocess document từ UI/backend thay vì chỉ chạy script CLI, kèm audit rõ ràng cho các lần reprocess.

Workflow MVP hiện có:

```text
web upload -> document detail -> OCR status refresh -> searchable -> dashboard search -> open source document
```

Chi tiết task vừa hoàn thành nằm trong `TASK_NEXT.md`.
