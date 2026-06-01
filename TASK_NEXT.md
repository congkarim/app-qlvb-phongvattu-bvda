# Task Tiếp Theo: Tích Hợp VietOCR Local Cho OCR Tiếng Việt

Trạng thái: sẵn sàng triển khai.

Ngày cập nhật: 2026-06-01

## Lý Do Ưu Tiên

OCR tiếng Việt scan hiện chưa đạt yêu cầu.

PaddleOCR 3.x với `lang=vi` vẫn dùng recognizer Latin:

```text
latin_PP-OCRv5_mobile_rec
```

Recognizer Latin đọc được chữ cái cơ bản nhưng thường rơi dấu tiếng Việt:

```text
Độc lập -> Đc lp
Phạm vi điều chỉnh -> Phm vi điu chnh
đấu thầu -> đu thu
```

Lớp restore hiện tại chỉ sửa được một số cụm pháp lý/tiêu ngữ phổ biến. Không nên dùng restore/LLM để đoán lại toàn văn bản pháp lý vì có rủi ro sửa sai nội dung.

Quyết định mới: tích hợp **VietOCR local** luôn như recognizer tiếng Việt chính cho ảnh/PDF scan, vẫn giữ PaddleOCR/OpenCV trong pipeline local.

## Mục Tiêu

Thêm OCR engine local mới:

```env
OCR_ENGINE=paddle_vietocr
```

Luồng đề xuất:

```text
PDF/image scan
-> preprocess OpenCV
-> PaddleOCR text detection
-> crop từng text line/box
-> VietOCR recognition
-> clean text
-> persist page text
-> chunk
-> embedding
-> Qdrant
```

PaddleOCR hiện tại vẫn giữ làm fallback/baseline:

```env
OCR_ENGINE=paddleocr
```

## Ràng Buộc Không Đổi

- Không dùng cloud OCR.
- Không dùng API LLM để sửa nội dung pháp lý.
- Chấp nhận mở rộng VietOCR local.
- Docker Compose first.
- MVP first, không over-engineering.
- Backend giữ kiến trúc `router -> service -> repository`.
- OCR pipeline vẫn local/on-prem.
- Không commit model files hoặc runtime artifacts.
- Không hardcode model path ngoài cấu hình env.
- Không thay đổi frontend nếu chưa cần.

## Phạm Vi Triển Khai

### 1. Thêm Dependency VietOCR

Thêm dependency Python cần thiết vào `apps/api/requirements.txt`.

Yêu cầu:
- Chạy được trong Docker CPU.
- Không phá sentence-transformers/PyTorch CPU hiện có.
- Nếu VietOCR cần version Torch khác, phải kiểm tra conflict trước khi đổi.

Gợi ý kiểm tra trong container trước khi sửa rộng:

```bash
docker compose run --rm worker python - <<'PY'
import torch
print(torch.__version__)
PY
```

### 2. Thêm Config VietOCR

Thêm settings:

```env
OCR_ENGINE=paddle_vietocr
VIETOCR_MODEL_DIR=/models/ocr/vietocr
VIETOCR_DEVICE=cpu
VIETOCR_CONFIG=transformer
VIETOCR_WEIGHT_PATH=/models/ocr/vietocr/transformerocr.pth
VIETOCR_MAX_BATCH_SIZE=1
```

Yêu cầu:
- Model nằm dưới `models/ocr/vietocr`.
- Không commit model.
- Nếu `OCR_ENGINE=paddle_vietocr` nhưng model chưa có, worker phải báo lỗi rõ ràng.
- Có thể cho phép fallback sang PaddleOCR bằng env riêng nếu cần:

```env
OCR_FALLBACK_ENGINE=paddleocr
```

### 3. Tách OCR Engine Module Nhỏ

Giữ `DocumentContentService` không phình quá lớn.

Đề xuất tạo module:

```text
apps/api/app/services/ocr/
  __init__.py
  schemas.py
  paddle_ocr_engine.py
  paddle_vietocr_engine.py
```

Interface tối thiểu:

```python
class OcrEngine(Protocol):
    def recognize(self, image_array: np.ndarray) -> list[OcrLine]:
        ...
```

`OcrLine` gồm:
- `text`
- `confidence`
- `box` optional

Không refactor toàn bộ document extraction nếu không cần. Chỉ tách phần engine để dễ test và fallback.

### 4. PaddleOCR Detection Cho VietOCR

Với `OCR_ENGINE=paddle_vietocr`:
- Dùng PaddleOCR để detect text boxes.
- Không dùng PaddleOCR recognizer làm kết quả chính.
- Crop ảnh theo box.
- Sắp xếp box theo thứ tự đọc: từ trên xuống dưới, trái sang phải.
- Đưa crop vào VietOCR để nhận dạng text.

Lưu ý kỹ thuật:
- PaddleOCR 3.x output khác PaddleOCR 2.x; cần parser detection box riêng.
- Nếu detect box rỗng, fallback sang PaddleOCR full OCR nếu cấu hình cho phép.
- Cần giữ confidence page-level.

### 5. Preprocess

Giữ `OCR_PREPROCESS_MODE` hiện có:
- `raw`
- `clahe`
- `threshold`
- `auto`

Với VietOCR:
- Benchmark nhanh raw/clahe/threshold trên cùng ảnh.
- Chọn candidate theo số text line, confidence nếu có, số ký tự tiếng Việt có dấu và độ dài text.

Không apply restore toàn văn một cách mù quáng. `OCR_RESTORE_VIETNAMESE_TERMS` có thể giữ cho tiêu ngữ/cụm pháp lý phổ biến nhưng không được che lấp kết quả VietOCR.

### 6. Test Fixture Và Benchmark Nhỏ

Tạo fixtures không chứa dữ liệu nhạy cảm:

```text
tests/fixtures/ocr_vi/
```

Dataset tối thiểu:
- 3 ảnh rõ, font in văn bản pháp lý.
- 3 ảnh scan/nén/mờ.
- 1 PDF scan nếu tạo được nhanh.

Ground truth lưu dạng `.txt` cùng tên:

```text
sample_001.png
sample_001.txt
sample_002.png
sample_002.txt
```

Nội dung phải có:
- `CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM`
- `Độc lập - Tự do - Hạnh phúc`
- `Điều`, `Khoản`, `Mục`
- `Phạm vi điều chỉnh`
- `đấu thầu`
- số hiệu văn bản, ngày tháng
- các dấu tiếng Việt khó: `ă`, `â`, `ê`, `ô`, `ơ`, `ư`, hỏi/ngã/nặng

### 7. Benchmark Script

Thêm script:

```text
apps/api/app/scripts/benchmark_ocr_vi.py
```

Chức năng:
- Đọc fixtures từ `tests/fixtures/ocr_vi`.
- Chạy `paddleocr` và `paddle_vietocr`.
- Tính CER, WER, accent loss rate, runtime/page.
- Xuất bảng markdown hoặc JSON.
- Không ghi database.
- Không upload vào hệ thống.

Command:

```bash
docker compose exec -T worker python -m app.scripts.benchmark_ocr_vi \
  --fixtures /app/tests/fixtures/ocr_vi \
  --engine paddle_vietocr
```

### 8. Cập Nhật README Và PROJECT_STATUS

README cần có:
- Cách chuẩn bị VietOCR model local.
- Env để bật `OCR_ENGINE=paddle_vietocr`.
- Command test OCR.
- Ghi rõ model files không commit.

PROJECT_STATUS cần có:
- VietOCR đã tích hợp hay chưa.
- Kết quả benchmark ngắn.
- Giới hạn còn lại.

## Tiêu Chí Hoàn Thành

- `OCR_ENGINE=paddle_vietocr` chạy được trong Docker Compose worker.
- Upload ảnh/PDF scan tiếng Việt xử lý được end-to-end.
- PaddleOCR engine cũ vẫn chạy được khi `OCR_ENGINE=paddleocr`.
- Nếu thiếu VietOCR model, lỗi rõ ràng và không âm thầm tạo text sai.
- Có benchmark so sánh PaddleOCR vs Paddle+VietOCR trên fixtures.
- OCR mẫu phải giữ được tối thiểu:
  - `CỘNG HÒA`
  - `Độc lập`
  - `Phạm vi điều chỉnh`
  - `đấu thầu`
- Không dùng cloud service.
- Không commit model files.

## Rủi Ro

- VietOCR có thể làm image nặng hơn hoặc conflict dependency.
- VietOCR recognition phụ thuộc chất lượng crop line; nếu detection box kém thì recognizer tốt vẫn không đủ.
- CPU có thể chậm khi OCR nhiều page.
- Model VietOCR public có thể không tối ưu cho font/scan pháp lý; nếu chưa đạt, hướng tiếp theo là fine-tune local.

## Task Sau Khi Tích Hợp

Nếu VietOCR đạt yêu cầu:
- Chuẩn hóa tài liệu vận hành OCR local.
- Re-upload các tài liệu scan và kiểm tra search.
- Quay lại task dedup/reranking semantic search.

Nếu VietOCR chưa đạt:
- Lập task fine-tune recognizer tiếng Việt local.
- Mở rộng dataset OCR pháp lý.

## Commit Dự Kiến

```bash
git add TASK_NEXT.md
git commit -m "docs: plan local VietOCR integration"
```
