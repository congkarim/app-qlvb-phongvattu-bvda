# Task Tiếp Theo: Cải Thiện OCR Công Văn Và Hybrid Search

Trạng thái: đề xuất.

Ngày cập nhật: 2026-06-03

## Task Vừa Hoàn Thành

Đã giảm runtime vòng benchmark OCR/VietOCR, reindex Qdrant payload để có `content_hash`, và thêm fixture công văn không nhạy cảm.

Kết quả chính:
- `benchmark_ocr_vi.py` có tùy chọn `--preprocess-mode raw/clahe/threshold/auto/all`.
- Output benchmark có `preprocess_mode`, giúp so sánh runtime/chất lượng mà không cần đổi env ngoài.
- Benchmark giữ lại `DocumentContentService` theo engine/preprocess mode trong cùng process.
- OCR engine cache không còn phụ thuộc preprocess mode, nên đổi preprocess không khởi tạo lại model detect/recognize.
- Thêm fixture `sample_007.png` và `sample_007.txt` cho công văn xã/phòng ban giả lập:
  - Header hai bên.
  - Số hiệu.
  - Ngày tháng.
  - Kính gửi.
  - Nội dung yêu cầu.
  - Dấu mộc và nhiễu nhẹ.
- Reindex Qdrant thật đã cập nhật payload `content_hash` cho chunks hiện có.
- Search sau reindex vẫn đưa chunk `Điều 1. Phạm vi điều chính` lên top 1 cho query `Luật Đấu thầu phạm vi điều chỉnh`.

Đã kiểm tra:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/scripts/benchmark_ocr_vi.py /app/app/services/ocr/__init__.py /app/tests/fixtures/ocr_vi/generate_fixtures.py
docker compose run --rm --no-deps worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --files sample_007.png --engine paddle_vietocr --preprocess-mode raw --format json
docker compose run --rm --no-deps worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --files sample_001.png --engine paddle_vietocr --preprocess-mode raw clahe --format json
docker compose config --quiet
docker compose up -d postgres qdrant api
curl -fsS http://localhost:8000/health
docker compose exec -T api python -m app.scripts.reindex_embeddings --dry-run
docker compose exec -T api python -m app.scripts.reindex_embeddings
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Luật Đấu thầu phạm vi điều chỉnh","limit":5}'
```

Kết quả benchmark đáng chú ý:
- `sample_001.png`, `paddle_vietocr/raw`: CER `0.0`, WER `0.0`, accent loss `0.0`, confidence `0.9264`, runtime `20.682s`.
- `sample_001.png`, `paddle_vietocr/clahe`: CER `0.0`, WER `0.0`, accent loss `0.0`, confidence `0.9259`, runtime `11.944s`.
- `sample_007.png`, `paddle_vietocr/raw`: confidence `0.9228`, accent loss `0.0`, còn lỗi thứ tự header và thiếu một phần dòng liên hệ.
- Reindex dry-run: `453` chunks.
- Reindex thật: `453` chunks.
- Qdrant collection kiểm tra: `document_chunks_bkai_768_v1`, payload mẫu có `content_hash`.

## Mục Tiêu Task Tiếp Theo

Cải thiện OCR trên công văn có header hai bên/dấu mộc và bổ sung hybrid search PostgreSQL keyword + Qdrant vector cho các query pháp lý hoặc hành chính còn nhạy với thứ hạng vector.

## Ràng Buộc Không Đổi

- Không dùng cloud OCR.
- Không dùng API LLM để sửa nội dung pháp lý.
- Docker Compose first.
- MVP first.
- Backend giữ `router -> service -> repository`.
- OCR pipeline local/on-prem.
- Không commit model files hoặc runtime artifacts.

## Phạm Vi Đề Xuất

### 1. OCR Công Văn Có Header Hai Bên

Vấn đề:
- `sample_007.png` giữ dấu tốt nhưng thứ tự header hai bên chưa ổn.
- Một phần dòng liên hệ bị mất hoặc bị gom sai khi gần vùng chữ ký/dấu mộc.

Hướng xử lý:
- Cải thiện line ordering cho layout header hai cột nhỏ ở đầu trang.
- Thêm rule giữ các dòng chứa `Kính gửi`, `Số:`, ngày tháng và `Người liên hệ`.
- Đo lại `sample_007.png` với `raw/clahe/threshold`.

### 2. Hybrid Search Keyword + Vector

Vấn đề:
- Exact legal/admin phrases vẫn cần reranking thủ công để ổn định top 1.
- PostgreSQL text search có thể bổ sung tín hiệu keyword cho các cụm như `phạm vi điều chỉnh`, `người liên hệ`, `số hiệu`.

Hướng xử lý:
- Thêm repository query keyword trên `document_chunks.text`.
- Kết hợp score keyword + Qdrant vector ở service search.
- Giữ response schema hiện tại, không thêm RAG.

## Tiêu Chí Hoàn Thành

- `sample_007.png` cải thiện thứ tự header và giữ được số hiệu/ngày/kính gửi/người liên hệ.
- Benchmark chạy được cho `sample_007.png` theo nhiều preprocess mode.
- Search legal exact phrase không phụ thuộc quá nhiều vào rule riêng từng query.
- Không phát sinh model/runtime artifact trong git.
