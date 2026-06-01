# Task Tiếp Theo: Benchmark Và Chọn Recognizer Tiếng Việt Local

Trạng thái: đề xuất.

Ngày cập nhật: 2026-06-01

## Lý Do Ưu Tiên

OCR tiếng Việt scan hiện chưa đạt yêu cầu.

Task OCR vừa hoàn thành đã:
- Nâng PaddleOCR từ `2.9.1` lên `3.3.0`.
- Nâng PaddlePaddle từ `2.6.2` lên `3.2.0`.
- Chạy PP-OCRv5 với `lang=vi`.
- Thêm preprocess `auto`: raw resize, CLAHE, adaptive threshold.
- Thêm hậu xử lý cục bộ cho một số cụm pháp lý/tiêu ngữ.

Tuy nhiên, kiểm tra thực tế cho thấy PaddleOCR 3.x với `lang=vi` vẫn dùng recognizer Latin:

```text
latin_PP-OCRv5_mobile_rec
```

Recognizer Latin đọc được chữ cái cơ bản nhưng vẫn rơi dấu tiếng Việt, ví dụ:

```text
Độc lập -> Đc lp
Phạm vi điều chỉnh -> Phm vi điu chnh
đấu thầu -> đu thu
```

Lớp restore hiện tại chỉ là giải pháp MVP cho một số cụm phổ biến, không đủ an toàn để sửa toàn văn bản pháp lý.

## Mục Tiêu

Benchmark các lựa chọn recognizer tiếng Việt chạy local/on-prem, sau đó chọn hướng tích hợp chính thức cho OCR scan tiếng Việt.

Đầu ra mong muốn:
- Có bộ test OCR tiếng Việt nhỏ nhưng đại diện.
- Có script benchmark repeatable.
- Có bảng so sánh chất lượng và tốc độ.
- Có quyết định kỹ thuật: tiếp tục PaddleOCR, tích hợp VietOCR local, thử PaddleOCR-VL nếu máy đủ GPU, hoặc chuẩn bị fine-tune recognizer riêng.

## Ràng Buộc Không Đổi

- Không dùng cloud OCR.
- Không dùng API LLM để sửa nội dung pháp lý.
- Chấp nhận mở rộng VietOCR local nếu benchmark chứng minh tốt hơn.
- Docker Compose first.
- MVP first, không over-engineering.
- Backend giữ kiến trúc `router -> service -> repository`.
- OCR pipeline vẫn local/on-prem.
- Không commit model files hoặc runtime artifacts.
- Không hardcode model path ngoài cấu hình env.

## Candidate Recognizer

### 1. PaddleOCR PP-OCRv5 Hiện Tại

Vai trò:
- Baseline đang chạy trong hệ thống.
- Detection và recognition cùng từ PaddleOCR.

Config hiện tại:

```env
OCR_ENGINE=paddleocr
OCR_LANG=vi
OCR_MODEL_DIR=/models/ocr
OCR_PREPROCESS_MODE=auto
OCR_RESTORE_VIETNAMESE_TERMS=true
```

Cần benchmark:
- Raw output không restore.
- Output có restore.
- Tốc độ OCR/page CPU.
- Tỷ lệ mất dấu trên văn bản pháp lý.

### 2. VietOCR Local

Vai trò:
- Candidate recognizer tiếng Việt local được chấp nhận mở rộng.
- Có thể dùng PaddleOCR/OpenCV cho detection, sau đó crop từng text line/box và đưa sang VietOCR recognition.

Yêu cầu tích hợp nếu chọn:
- Thêm backend OCR mode, ví dụ:

```env
OCR_ENGINE=paddle_vietocr
VIETOCR_MODEL_DIR=/models/ocr/vietocr
VIETOCR_DEVICE=cpu
```

- Không thay router.
- Logic nằm trong service/module OCR, không đưa business logic vào router.
- Model VietOCR đặt dưới `models/ocr/vietocr`, không commit.
- Nếu model chưa có, worker báo lỗi rõ ràng hoặc fallback theo config.

Cần benchmark:
- Accuracy tiếng Việt có dấu.
- Lỗi số hiệu, ngày tháng, điều/khoản.
- Tốc độ CPU.
- RAM khi chạy cùng worker.

### 3. PaddleOCR-VL Local

Vai trò:
- Candidate OCR/VLM local nếu máy có GPU phù hợp.

Điều kiện:
- Chỉ thử nếu môi trường local có NVIDIA GPU/CUDA đủ chạy.
- Không làm thành dependency bắt buộc cho MVP CPU.

Cần benchmark:
- Chất lượng tiếng Việt scan.
- Chi phí tài nguyên.
- Khả năng đóng gói Docker Compose GPU.

### 4. Fine-Tune PaddleOCR Recognizer Tiếng Việt

Vai trò:
- Hướng dài hạn nếu cần độ chính xác cao và kiểm soát model.

Chưa triển khai ngay trong MVP.

Cần đánh giá:
- Dataset cần chuẩn bị.
- Công train.
- Cách đóng gói model local sau train.

## Bộ Test OCR

Tạo thư mục test không chứa dữ liệu nhạy cảm:

```text
tests/fixtures/ocr_vi/
```

Dataset tối thiểu:
- 5 ảnh rõ, font in văn bản pháp lý.
- 5 ảnh scan mờ hoặc bị nén.
- 2 PDF scan nhiều page nếu có.

Ground truth lưu dạng `.txt` cùng tên:

```text
sample_001.png
sample_001.txt
sample_002.png
sample_002.txt
```

Nội dung phải có:
- Tiêu ngữ: `CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM`
- `Độc lập - Tự do - Hạnh phúc`
- `Điều`, `Khoản`, `Mục`
- `Phạm vi điều chỉnh`
- `đấu thầu`
- số hiệu văn bản, ngày tháng
- các dấu tiếng Việt khó: `ă`, `â`, `ê`, `ô`, `ơ`, `ư`, thanh hỏi/ngã/nặng

## Metric Benchmark

Tính tối thiểu:
- CER: Character Error Rate.
- WER: Word Error Rate.
- Accent loss rate: tỷ lệ ký tự tiếng Việt có dấu bị mất.
- Runtime/page.
- Peak memory nếu đo được đơn giản.

Ghi nhận thêm lỗi pháp lý quan trọng:
- Sai số điều/khoản.
- Sai số hiệu văn bản.
- Sai ngày tháng.
- Sai từ khóa nghiệp vụ như `đấu thầu`, `quản lý`, `tài sản công`.

## Phạm Vi Triển Khai Đề Xuất

### 1. Tạo Benchmark Script

Thêm script backend:

```text
apps/api/app/scripts/benchmark_ocr_vi.py
```

Chức năng:
- Đọc fixtures từ `tests/fixtures/ocr_vi`.
- Chạy từng OCR engine/candidate.
- Xuất bảng markdown hoặc JSON.
- Không ghi vào database.
- Không upload lên hệ thống.

Command gợi ý:

```bash
docker compose exec -T worker python -m app.scripts.benchmark_ocr_vi \
  --fixtures /app/tests/fixtures/ocr_vi \
  --engine paddleocr
```

Nếu thêm VietOCR:

```bash
docker compose exec -T worker python -m app.scripts.benchmark_ocr_vi \
  --fixtures /app/tests/fixtures/ocr_vi \
  --engine paddle_vietocr
```

### 2. Thêm OCR Engine Interface Nhỏ

Chỉ thêm abstraction nếu cần để benchmark nhiều engine:

```text
DocumentContentService
  -> OcrEngine protocol/interface
  -> PaddleOcrEngine
  -> PaddleVietOcrEngine
```

Không refactor rộng phần document extraction nếu benchmark chưa cần.

### 3. Tích Hợp VietOCR Ở Dạng Optional

Chỉ thêm dependency và code path nếu:
- Chạy được trong Docker CPU.
- Model local chuẩn bị được dưới `models/ocr/vietocr`.
- Benchmark cho kết quả tốt hơn PaddleOCR rõ ràng.

Nếu dependency quá nặng hoặc model không ổn định:
- Ghi nhận trong `PROJECT_STATUS.md`.
- Không ép vào runtime chính.

### 4. Chọn Hướng Chính Thức

Sau benchmark, cập nhật:
- `PROJECT_STATUS.md`: kết quả đo.
- `TASK_NEXT.md`: quyết định và task triển khai tiếp.
- `README.md`: cách chuẩn bị model nếu chọn VietOCR hoặc model mới.

## Tiêu Chí Hoàn Thành

- Có benchmark script chạy được trong Docker Compose.
- Có ít nhất baseline PaddleOCR PP-OCRv5.
- Có đánh giá VietOCR local nếu model/dependency chuẩn bị được.
- Có bảng kết quả CER/WER/accent loss/runtime.
- Có khuyến nghị rõ ràng recognizer nào dùng cho OCR scan tiếng Việt.
- Không dùng cloud service.
- Không commit model files.

## Rủi Ro

- VietOCR có thể cần thêm PyTorch dependency/model, làm image nặng hơn.
- VietOCR recognition cần crop line tốt; nếu detection box từ PaddleOCR kém thì recognizer tốt vẫn không đủ.
- PaddleOCR-VL có thể không phù hợp CPU local.
- Benchmark nhỏ có thể chưa đại diện cho toàn bộ scan thực tế; cần ghi rõ giới hạn dataset.

## Task Sau Benchmark

Tùy kết quả:
- Nếu VietOCR tốt hơn rõ ràng: triển khai `OCR_ENGINE=paddle_vietocr` trong pipeline chính.
- Nếu PaddleOCR vẫn tốt nhất: mở rộng restore/dictionary ở mức có kiểm soát và chuẩn bị fine-tune.
- Nếu cả hai chưa đạt: lập task fine-tune recognizer tiếng Việt local.

Sau khi OCR đạt yêu cầu, quay lại task search:
- Dedup/reranking semantic search để giảm kết quả trùng.
- Hybrid search keyword + vector cho truy vấn pháp lý.

## Commit Dự Kiến

```bash
git add TASK_NEXT.md
git commit -m "docs: plan local Vietnamese OCR recognizer benchmark"
```
