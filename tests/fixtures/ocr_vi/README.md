# OCR Vietnamese Fixtures

Thư mục này chứa fixtures OCR tiếng Việt không nhạy cảm.

## Bộ fixture

- `sample_001.png`: scan rõ, tiêu ngữ và số hiệu văn bản.
- `sample_002.png`: quyết định hành chính, nhiều dấu tiếng Việt.
- `sample_003.png`: scan nén/mờ, mẫu thông tư.
- `sample_004.png`: bố cục hai cột và ghi chú.
- `sample_005.png`: ảnh nghiêng nhẹ, có nhiễu.
- `sample_006.pdf`: PDF scan 2 trang.

Mỗi fixture có ground truth `.txt` cùng tên.

Tạo lại toàn bộ fixture bằng:

```bash
python3 tests/fixtures/ocr_vi/generate_fixtures.py
```

Hoặc chạy trong container worker:

```bash
docker compose run --rm --no-deps worker python /app/tests/fixtures/ocr_vi/generate_fixtures.py
```

Benchmark OCR:

```bash
docker compose run --rm --no-deps -e OCR_PREPROCESS_MODE=raw worker \
  python -m app.scripts.benchmark_ocr_vi \
  --fixtures /app/tests/fixtures/ocr_vi \
  --engine all
```

## Kết quả gần nhất

Ngày chạy: 2026-06-02.

Cấu hình: `OCR_PREPROCESS_MODE=raw`, `OCR_ENGINE` benchmark lần lượt `paddleocr` và `paddle_vietocr`.

| file | paddleocr CER/WER/accent loss | paddle_vietocr CER/WER/accent loss | Nhận xét |
| --- | ---: | ---: | --- |
| `sample_001.png` | 0.0053 / 0.0238 / 0.0294 | 0.0 / 0.0 / 0.0 | VietOCR sửa được lỗi mất `Số`. |
| `sample_002.png` | 0.1066 / 0.4722 / 0.4923 | 0.0063 / 0.0417 / 0.0 | VietOCR giữ dấu tốt, còn lỗi dấu câu nhỏ. |
| `sample_003.png` | 0.1443 / 0.5397 / 0.5424 | 0.0687 / 0.1111 / 0.0 | Scan mờ vẫn có hallucination vài từ cuối dòng. |
| `sample_004.png` | 0.6905 / 0.9783 / 0.4659 | 0.711 / 0.913 / 0.0 | Hai cột bị sai thứ tự đọc, cần cải thiện ordering/detection. |
| `sample_005.png` | 0.098 / 0.4154 / 0.4808 | 0.0034 / 0.0154 / 0.0 | VietOCR xử lý tốt ảnh nghiêng nhẹ. |
| `sample_006.pdf` | 0.1417 / 0.5487 / 0.5714 | 0.0526 / 0.0531 / 0.0 | PDF scan giữ dấu tốt hơn, còn tách dòng tiêu đề; khoảng 39.6s/page với VietOCR. |

Không commit model OCR hoặc file upload runtime vào thư mục này.
