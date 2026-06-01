# OCR Vietnamese Fixtures

Thư mục này chứa fixtures OCR tiếng Việt không nhạy cảm.

Có thể tạo nhanh sample local bằng:

```bash
docker compose exec -T worker python -m app.scripts.benchmark_ocr_vi \
  --fixtures /app/tests/fixtures/ocr_vi \
  --generate-sample \
  --engine paddleocr
```

Không commit model OCR hoặc file upload runtime vào thư mục này.
