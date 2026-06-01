# Task Tiếp Theo: Cải Thiện OCR Scan Tiếng Việt Có Dấu

Trạng thái: lên kế hoạch.

Ngày tạo: 2026-06-01

## Mục Tiêu

Sửa luồng OCR ảnh/PDF scan để nhận diện tiếng Việt có dấu tốt hơn. Trọng tâm là nâng model OCR cho ảnh scan, giữ đọc text nhúng PDF như hiện tại và giảm preprocess làm mất dấu.

## Ràng Buộc Không Đổi

- Không dùng cloud OCR hoặc API LLM bên ngoài.
- Không đổi stack cố định: FastAPI, PostgreSQL, Redis, Qdrant, PaddleOCR, OpenCV, Nuxt 3, PrimeVue, TailwindCSS, Pinia.
- Docker Compose first.
- MVP first, không over-engineering.
- Backend giữ kiến trúc `router -> service -> repository`.
- OCR pipeline giữ hướng local/on-prem.
- Không commit OCR model files hoặc runtime artifacts.

## Nguyên Nhân Hiện Tại

Log worker cho thấy PaddleOCR 2.9.1 với `lang="vi"` đang tải recognizer Latin:

```text
latin_PP-OCRv3_rec_infer
```

Recognizer Latin thường đọc được chữ cái cơ bản nhưng làm rơi dấu tiếng Việt, ví dụ:

```text
Đấu thầu -> Dau thau
điều chỉnh -> dieu chinh
```

Ngoài ra preprocess hiện tại dùng denoise và adaptive threshold khá mạnh, có thể làm mất các dấu nhỏ trong tiếng Việt.

## Phạm Vi Triển Khai

### 1. Giữ Luồng PDF Text-Native

Không OCR lại PDF đã có text layer.

Luồng giữ nguyên:

```text
PDF text-native -> pypdfium2 get_textpage -> giữ Unicode tiếng Việt
```

Chỉ fallback OCR khi page PDF không có text hoặc text quá ít.

### 2. Nghiên Cứu Và Chốt PaddleOCR Version

Ưu tiên nâng từ PaddleOCR 2.9.1 lên PaddleOCR 3.x để dùng PP-OCRv5 multilingual.

Cần kiểm tra:
- API khởi tạo `PaddleOCR` trong version mới.
- Cách cấu hình `lang="vi"`.
- Cách set model cache/local model path.
- Compatibility với Python 3.11, Docker slim và `paddlepaddle`.

Nguồn tham khảo chính:
- PaddleOCR v3 OCR pipeline có `lang=vi`.
- PP-OCRv5 multilingual cải thiện accuracy multilingual so với PP-OCRv3.

### 3. Thêm Config OCR Local

Thêm cấu hình vào `Settings`:

```env
OCR_ENGINE=paddleocr
OCR_LANG=vi
OCR_USE_GPU=false
OCR_MODEL_DIR=/models/ocr
OCR_PREPROCESS_MODE=auto
OCR_MIN_CONFIDENCE=0.0
```

Mục tiêu:
- Không hardcode `lang="vi"` trong service.
- Model OCR nằm trong `models/ocr` khi chạy production/offline.
- Có thể chỉnh preprocess mà không sửa code.

### 4. Cập Nhật Docker Compose

Đảm bảo `api` và `worker` vẫn mount:

```text
./models:/models
```

Không đưa model vào Docker build context.

### 5. Cải Thiện Preprocess Cho Dấu Tiếng Việt

Hiện tại:

```text
gray -> resize -> denoise -> adaptive threshold
```

Đề xuất `OCR_PREPROCESS_MODE=auto`:
- Candidate 1: RGB/gray resize nhẹ, không threshold.
- Candidate 2: CLAHE contrast nhẹ.
- Candidate 3: adaptive threshold như hiện tại.

Chạy OCR trên các candidate và chọn kết quả theo:
- Confidence trung bình cao hơn.
- Có số lượng ký tự tiếng Việt có dấu tốt hơn.
- Text không rỗng.

Không xóa cấu trúc pháp lý quan trọng như `Điều`, `Khoản`, `Mục`, số hiệu, ngày tháng.

### 6. Tạo Bộ Test OCR Tiếng Việt

Chuẩn bị 1-2 ảnh/PDF scan nội bộ có nội dung mẫu:

```text
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc
Điều 1. Phạm vi điều chỉnh đấu thầu
```

Tiêu chí pass:
- Output còn `CỘNG HÒA`.
- Output còn `Độc lập`.
- Output còn `Phạm vi điều chỉnh`.
- Output còn `đấu thầu`.

### 7. Benchmark Trước Và Sau

Trước khi sửa:
- Upload ảnh/PDF scan tiếng Việt.
- Ghi lại OCR text hiện tại bị mất dấu.

Sau khi sửa:
- Upload lại cùng file.
- So sánh text, confidence, số dòng đọc được.

Ghi nhận vào `PROJECT_STATUS.md` và `TASK_NEXT.md`.

### 8. Cập Nhật Tài Liệu

Cập nhật:
- `README.md`: cách chuẩn bị OCR model local, env OCR, test OCR tiếng Việt.
- `PROJECT_STATUS.md`: trạng thái OCR tiếng Việt sau nâng cấp.
- `TASK_NEXT.md`: kết quả task và task kế tiếp.

### 9. Commit

Chạy kiểm tra:

```bash
docker compose config
docker compose build api worker
docker compose up -d api worker
docker compose exec -T worker python -m py_compile /app/app/services/document_content_service.py
```

Commit dự kiến:

```bash
git add ...
git commit -m "fix: improve Vietnamese OCR for scanned documents"
```

## Tiêu Chí Hoàn Thành

- PDF có text nhúng vẫn giữ dấu tiếng Việt qua text extraction.
- Ảnh/PDF scan tiếng Việt được OCR có dấu tốt hơn hiện tại.
- Worker không tải model ngoài ý muốn khi đã cấu hình local model.
- Có test/benchmark rõ trước và sau.
- Không dùng cloud service, không đổi stack, không commit model files.

## Rủi Ro Và Theo Dõi

- PaddleOCR 3.x có thể thay đổi API so với 2.9.1, cần kiểm tra trong container trước khi sửa rộng.
- PP-OCRv5 `lang=vi` có thể vẫn dùng nhóm model Latin nếu chưa có recognizer riêng cho tiếng Việt; nếu vậy cần đánh giá chất lượng thực tế.
- Adaptive threshold có thể tốt cho scan mờ nhưng làm mất dấu; cần chọn preprocess theo confidence/ký tự có dấu thay vì cố định một pipeline.
- Nếu PP-OCRv5 vẫn không đủ tốt cho scan xấu, task sau nên nghiên cứu fine-tune recognizer tiếng Việt local.

## Task Sau Đó Đề Xuất

Sau khi OCR tiếng Việt ổn hơn, quay lại cải thiện search:
- Dedup/reranking semantic search để giảm kết quả trùng.
- Hybrid search keyword + vector cho truy vấn pháp lý.
