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

Auth/RBAC MVP:
- Admin local mặc định: `admin@example.com` / `admin123`.
- Login response trả `user.role`.
- Role `admin` được reprocess, quản lý source files và quản lý user tại `/users`.
- Role `user` được upload, search, xem tài liệu/source file và sửa metadata.
- Admin có thể tạo user local, đổi role `admin/user`, reset password, kích hoạt/vô hiệu hóa và xóa mềm user. API chặn admin tự hạ quyền hoặc tự vô hiệu hóa/xóa tài khoản đang dùng.

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

3. Vào `Upload`, chọn file `.txt`, `.pdf`, ảnh, `.docx` hoặc `.xlsx`, nhập metadata nghiệp vụ nếu có, bấm `Upload`.

Metadata nghiệp vụ hiện hỗ trợ:
- Số văn bản.
- Ngày ban hành.
- Đơn vị ban hành.
- Loại nghiệp vụ: công văn đến, công văn đi, hợp đồng, quyết định.

4. Sau khi upload thành công, web mở trang chi tiết document:

```text
/documents/{document_id}
```

5. Ở trang detail, theo dõi:
- Metadata văn bản và metadata nghiệp vụ.
- OCR job status.
- OCR text.
- Chunks, gồm filter xem nhanh tất cả chunk, chunk cần review, phụ lục và phụ lục cần review.

Trang detail tự refresh trạng thái cho tới khi document chuyển sang `searchable`.

Trong card `Metadata`, có thể bấm `Sửa metadata` để chỉnh tên văn bản, số văn bản, ngày ban hành, đơn vị ban hành và loại nghiệp vụ. Mỗi lần lưu được ghi vào audit log của document.

Trong card `Tệp nguồn`, bấm `Xem trước` để preview inline PDF, ảnh hoặc text cạnh metadata/OCR text. Bấm `Mở` để mở tab mới với định dạng browser hỗ trợ; DOCX/XLSX hoặc định dạng không preview được sẽ download.

Các thao tác reprocess, thêm source file, đổi thứ tự source file, xóa source file và đánh dấu chunk đã review chỉ dành cho admin.

Admin có thể vào `Users` để tạo tài khoản thường, đổi role, reset password, phân trang danh sách, xem audit log theo user và vô hiệu hóa hoặc xóa mềm user.

6. Vào `Dashboard`, search:

```text
quản lý vật tư
```

Admin có thể xem thêm card `Review queue` trong Dashboard để lọc chunks cần review theo phụ lục, document id hoặc confidence thấp, rồi mở document nguồn hoặc bấm `Đã review`.

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
- `.pdf`: ưu tiên trích xuất text nhúng bằng `pypdfium2`; page không có text mới render ảnh rồi OCR bằng PaddleOCR detector + VietOCR recognizer.
- `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.bmp`: OCR bằng PaddleOCR detector + VietOCR recognizer.
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

Semantic search hỗ trợ filter metadata:

```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query":"văn bản","limit":5,"business_type":"decision","doc_group":"A","section_role":"clause","requires_review":false}'
```

Các filter hiện có: `document_type`, `department_id`, `business_type`, `document_number`, `issued_date`, `doc_group`, `section_role`, `requires_review`. Dashboard cũng có các control filter tương ứng cho metadata đã rollout.
Với phụ lục, dùng `section_role=appendix` hoặc chọn option `Phụ lục` trong Dashboard.

## Smoke Appendix Data

Kiểm tra luồng phụ lục có dữ liệu thật từ document detail, review queue, semantic search và thao tác `Đã review`:

```bash
docker compose exec -T api python -m app.scripts.smoke_appendix_data
```

Script tạo document fixture tạm có chunk `section_role=appendix`, index vào Qdrant, xác nhận review queue và search trả đúng chunk phụ lục, đánh dấu chunk đã review, rồi cleanup document/Qdrant point mặc định.

Giữ dữ liệu smoke để kiểm tra UI thủ công:

```bash
docker compose exec -T api python -m app.scripts.smoke_appendix_data --keep-data
```

Lần chạy sau sẽ tự cleanup các document có prefix `[SMOKE] Appendix review fixture` trước khi seed mới.

## Local OCR Tiếng Việt

OCR scan mặc định chạy local bằng PaddleOCR detector, VietOCR recognizer, PaddlePaddle CPU, PyTorch CPU và OpenCV. PDF có text layer vẫn được đọc trực tiếp bằng `pypdfium2` để giữ Unicode tiếng Việt; chỉ page scan hoặc ảnh mới đi qua OCR.

Env OCR mặc định trong Docker Compose:

```env
OCR_ENGINE=paddle_vietocr
OCR_LANG=vi
OCR_USE_GPU=false
OCR_DEVICE=cpu
OCR_MODEL_DIR=/models/ocr
OCR_PREPROCESS_MODE=auto
OCR_MIN_CONFIDENCE=0.0
OCR_RESTORE_VIETNAMESE_TERMS=true
VIETOCR_MODEL_DIR=/models/ocr/vietocr
VIETOCR_DEVICE=cpu
VIETOCR_CONFIG=vgg_transformer
VIETOCR_WEIGHT_PATH=/models/ocr/vietocr/transformerocr.pth
VIETOCR_MAX_BATCH_SIZE=1
VIETOCR_BEAMSEARCH=false
```

`OCR_PREPROCESS_MODE=auto` chạy nhiều candidate ảnh:
- ảnh RGB resize nhẹ;
- CLAHE tăng tương phản nhẹ;
- adaptive threshold cho scan mờ.

Worker chọn kết quả theo confidence, số ký tự tiếng Việt có dấu và độ dài text. `OCR_RESTORE_VIETNAMESE_TERMS=true` vẫn có thể sửa một số cụm pháp lý/tiêu ngữ phổ biến, nhưng kết quả chính với scan tiếng Việt đến từ VietOCR.

Model OCR local/offline:

```text
models/ocr/PP-OCRv5_server_det
models/ocr/latin_PP-OCRv5_mobile_rec
models/ocr/vietocr/transformerocr.pth
```

Nếu hai thư mục PaddleOCR tồn tại, service sẽ truyền trực tiếp vào PaddleOCR và không dùng cache ẩn trong container. VietOCR weight phải có ở `VIETOCR_WEIGHT_PATH` khi `OCR_ENGINE=paddle_vietocr`; nếu thiếu, worker báo lỗi rõ ràng. Không commit model files vì `models/` đã nằm trong `.gitignore`.

Chuẩn bị VietOCR weight local:

```bash
mkdir -p models/ocr/vietocr
docker compose exec -T worker python - <<'PY'
from pathlib import Path
import urllib.request

target = Path("/models/ocr/vietocr/transformerocr.pth")
target.parent.mkdir(parents=True, exist_ok=True)
urllib.request.urlretrieve("https://vocr.vn/data/vietocr/vgg_transformer.pth", target)
print(target, target.stat().st_size)
PY
```

Kiểm tra OCR tiếng Việt nhanh trong worker:

```bash
docker compose exec -T worker python -m app.scripts.benchmark_ocr_vi \
  --fixtures /app/tests/fixtures/ocr_vi \
  --engine all
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

## Chunking OCR Text

Worker mặc định dùng module `ocr_chunking` để chunk OCR text theo thể thức văn bản hành chính tiếng Việt:

```env
CHUNKING_BACKEND=ocr_chunking
```

Module này detect `doc_type`, map sang nhóm A/B/C/D/E, giữ cấu trúc như `Điều`, `Khoản`, mục La Mã, phụ lục, bảng và chữ ký khi tạo chunk. Bảng `document_chunks` lưu `doc_group`, `chunk_level`, `section_role`, `section_path`, `chunk_confidence` và `requires_review` để UI hiển thị được cấu trúc chunk. Metadata chi tiết hơn như `fallback_info`, `contains_appendix` và entities tiếp tục nằm trong Qdrant payload.

Phụ lục được nhận diện rule-based từ heading như `PHỤ LỤC`, `PHỤ LỤC I`, `PHỤ LỤC 01` hoặc dòng đính kèm độc lập. Câu thân bài chỉ nhắc tới phụ lục không bị tách thành section phụ lục. Trường hợp OCR/layout yếu sẽ được đánh `requires_review=true`.

Backfill metadata chunk cho document cũ từ OCR pages đã lưu, không thay text chunk hay embedding hiện có:

```bash
docker compose exec -T api python -m app.scripts.backfill_chunk_metadata --dry-run --limit 20
docker compose exec -T api python -m app.scripts.backfill_chunk_metadata --batch-size 20
```

Nếu document cũ có số chunk hiện hữu lệch số chunk sinh lại từ OCR pages, các chunk dư được gán metadata fallback `doc_group=E`, `section_role=unknown` và `requires_review=true`.

Backfill một document cụ thể:

```bash
docker compose exec -T api python -m app.scripts.backfill_chunk_metadata --document-id <document_id>
```

Sau backfill, reindex Qdrant để payload search có metadata chunk mới:

```bash
docker compose exec -T api python -m app.scripts.reindex_embeddings
```

Rollback tạm thời về chunking cũ:

```env
CHUNKING_BACKEND=legacy
```

Lưu ý:
- Không dùng lại Qdrant collection cũ khi đổi model hoặc đổi `EMBEDDING_DIMENSIONS`.
- Mỗi model/dimension nên dùng collection version riêng, ví dụ `document_chunks_bkai_768_v1`.
- Nếu model local chưa có và `ALLOW_FAKE_EMBEDDINGS=false`, API/worker sẽ báo lỗi rõ ràng thay vì âm thầm dùng vector giả.
- Sau khi bật BKAI local và reindex, collection `document_chunks_bkai_768_v1` có vector size `768`.
- Kết quả benchmark ban đầu tốt với các query như `hiệu lực thi hành luật đấu thầu`, `trách nhiệm của chủ đầu tư`, `lựa chọn nhà thầu`; dữ liệu upload trùng PDF/DOCX vẫn có thể làm kết quả bị duplicate.

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
