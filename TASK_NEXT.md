# Task Tiếp Theo: Triển Khai OCR Thật Cho PDF Và Ảnh

Trạng thái: đã lên kế hoạch.

Ngày tạo: 2026-05-28

## Lý Do Chọn Task

Theo `PROJECT_STATUS.md`, workflow MVP từ browser đã chạy được end-to-end:

```text
web upload -> document detail -> OCR status refresh -> searchable -> dashboard search -> open source document
```

Giới hạn lớn nhất hiện tại là OCR còn giả lập:
- File `.txt` và `.md` được đọc text trực tiếp.
- PDF/image chưa OCR thật.
- Các loại file khác sinh text mô phỏng.

Task tiếp theo nên thay OCR skeleton bằng OCR local/on-prem thật để MVP xử lý đúng loại tài liệu vận hành thực tế. Auth/route guard vẫn quan trọng, nhưng nên làm sau khi pipeline tài liệu có giá trị dữ liệu thật.

## Mục Tiêu

Triển khai OCR thật trong worker bằng PaddleOCR và OpenCV cho:
- PDF scan hoặc PDF ảnh.
- Ảnh scan: `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.bmp`.

Vẫn giữ fallback hiện tại cho:
- `.txt`
- `.md`

Workflow mục tiêu:

```text
upload PDF/image
-> worker lấy OCR job pending
-> chuyển PDF thành ảnh từng page nếu cần
-> preprocess ảnh bằng OpenCV
-> chạy PaddleOCR local
-> lưu text/confidence theo page
-> chunk
-> embed fake deterministic hiện tại
-> upsert Qdrant
-> document searchable
```

## Phạm Vi

Trong phạm vi:
- Thêm dependencies OCR local cho worker/API image.
- Tạo service OCR tách riêng khỏi `ocr_worker.py`.
- Chuyển PDF thành image theo page.
- Preprocess ảnh cơ bản bằng OpenCV.
- Chạy PaddleOCR local.
- Lưu `DocumentPage.text` và `DocumentPage.confidence`.
- Giữ chunking/search flow hiện có.
- Cập nhật README với cách test PDF/image OCR.
- Cập nhật `PROJECT_STATUS.md` sau khi hoàn thành.

Ngoài phạm vi:
- Local embedding model thật.
- RAG answer generation.
- Auth/seed admin/route guard.
- OCR layout nâng cao theo block/table.
- Manual correction UI.
- Retry từng page ở mức production.
- CI/CD, cloud service, Kubernetes.

## Điểm Bắt Đầu Hiện Tại

Worker hiện xử lý tại:

```text
apps/api/app/workers/ocr_worker.py
```

Luồng hiện có:
- Lấy `OCRJob` pending.
- Đổi document sang `ocr_running`.
- Gọi `_simulate_ocr_text(...)`.
- Tạo một `DocumentPage`.
- Chunk text.
- Fake embedding.
- Upsert Qdrant.
- Đổi document sang `searchable`.

Schema đã có sẵn:
- `documents`
- `document_pages`
- `document_chunks`
- `ocr_jobs`

`document_pages` đã có:
- `page_number`
- `text`
- `confidence`

## Thiết Kế Đề Xuất

### 1. OCR Service

Tạo service mới:

```text
apps/api/app/services/ocr_service.py
```

Trách nhiệm:
- Nhận `Path` file gốc và filename.
- Xác định loại file.
- Với `.txt/.md`: đọc text trực tiếp như hiện tại.
- Với PDF: render từng page thành image.
- Với image: preprocess rồi OCR.
- Trả về list page result:

```python
[
    {
        "page_number": 1,
        "text": "...",
        "confidence": 0.92,
    }
]
```

### 2. PDF To Image

Ưu tiên dùng thư viện Python vận hành được trong Docker, ít phụ thuộc system package.

Ứng viên hợp lý:
- `pypdfium2` để render PDF sang bitmap.
- Không dùng OCR cloud hoặc API ngoài.

### 3. Image Preprocess

Preprocess MVP bằng OpenCV:
- grayscale
- resize nếu ảnh quá nhỏ
- denoise nhẹ
- threshold hoặc adaptive threshold khi phù hợp
- giữ ảnh gốc, chỉ OCR trên bản preprocess in-memory hoặc temp file

Không làm deskew/table detection ở task này trừ khi cần để OCR chạy được.

### 4. PaddleOCR Execution

Khởi tạo PaddleOCR lazy singleton để tránh load model lại mỗi job.

Yêu cầu:
- Chạy CPU mặc định.
- Hỗ trợ tiếng Việt nếu cấu hình PaddleOCR/package cho phép.
- Gom text theo thứ tự OCR trả về.
- Tính confidence trung bình page.
- Khi page không có text, lưu text rỗng và confidence `0.0`, không crash toàn job nếu có page khác đọc được.

### 5. Worker Integration

Sửa `OCRWorker.process_job`:
- Thay `_simulate_ocr_text` bằng `OCRService.extract_pages(...)`.
- Tạo nhiều `DocumentPage`, mỗi page một record.
- Chunk từ toàn bộ text các page theo thứ tự page.
- Giữ fake embedding hiện tại.
- Nếu không OCR được page nào có text, đánh job/document `failed` với error rõ ràng.

## Task Chi Tiết

### 1. Dependencies Và Docker

Yêu cầu:
- Thêm package OCR vào `apps/api/requirements.txt`.
- Đảm bảo worker image cài đủ dependency để import PaddleOCR/OpenCV/PDF renderer.
- Không thêm service mới vào Docker Compose nếu không cần.

Tiêu chí hoàn thành:
- `docker compose build worker` không lỗi.
- Worker import được `cv2`, `paddleocr` và PDF renderer.

### 2. OCR Service

Yêu cầu:
- Tạo `OCRService`.
- Tách logic đọc text file, OCR image, OCR PDF khỏi worker.
- API nội bộ trả page results typed rõ ràng.
- Có xử lý lỗi file không tồn tại, unsupported extension, OCR empty result.

Tiêu chí hoàn thành:
- Worker không còn chứa logic OCR chi tiết.
- `.txt/.md` vẫn chạy như trước.
- PDF/image chạy qua PaddleOCR.

### 3. Persist Page Results

Yêu cầu:
- Tạo `DocumentPage` theo từng page.
- Lưu `confidence` trung bình page.
- Chunk dùng text ghép từ các page theo thứ tự.
- Không phá search flow hiện tại.

Tiêu chí hoàn thành:
- Detail page hiển thị OCR text thật theo page.
- Chunks vẫn xuất hiện sau OCR.
- Document chuyển `searchable` khi xử lý thành công.

### 4. Error Handling

Yêu cầu:
- Job lỗi phải set `OCRJob.status = failed`.
- Document lỗi phải set `Document.status = failed`.
- `OCRJob.error_message` có lý do đủ debug.
- Log lỗi không làm worker chết vòng lặp.

Tiêu chí hoàn thành:
- Upload file unsupported hoặc PDF lỗi không làm worker crash.
- Detail page thấy trạng thái failed.

### 5. Documentation

Cập nhật:
- `README.md`: cách test upload PDF/image.
- `PROJECT_STATUS.md`: OCR thật đã triển khai hoặc giới hạn còn lại.
- `TASK_NEXT.md`: ghi chú hoàn thành và đề xuất task tiếp theo.

## Lệnh Kiểm Tra

Build:

```bash
docker compose build worker api
```

Start stack:

```bash
docker compose up --build
```

Health:

```bash
curl http://localhost:8000/health
```

Upload file text để kiểm tra fallback:

```bash
printf 'Điều 1. Quy định về quản lý vật tư.' > sample.txt
curl -X POST "http://localhost:8000/api/v1/documents/upload?document_type=document" \
  -F "file=@sample.txt"
```

Upload ảnh hoặc PDF:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload?document_type=document" \
  -F "file=@sample.pdf"
```

Theo dõi worker:

```bash
docker compose logs -f worker
```

Kiểm tra search sau khi document `searchable`:

```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query":"quản lý vật tư","limit":5}'
```

## Định Nghĩa Hoàn Thành

Task hoàn thành khi:
- Upload `.txt/.md` vẫn hoạt động.
- Upload ít nhất một ảnh scan chạy OCR thật và chuyển `searchable`.
- Upload ít nhất một PDF scan chạy OCR thật theo page và chuyển `searchable`.
- Detail page hiển thị OCR text/confidence theo page.
- Search vẫn trả source document.
- Worker không crash khi gặp file lỗi.
- README và PROJECT_STATUS được cập nhật.
- `git diff --check` sạch.
- Có commit riêng cho task.

## Task Sau Đó Nên Cân Nhắc

Sau OCR thật, ưu tiên một trong hai hướng:
- Tích hợp local embedding model thật để score search có ý nghĩa hơn.
- Bổ sung auth seed admin và route guard để kiểm soát truy cập.
