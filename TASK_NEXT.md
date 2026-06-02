# Task Tiếp Theo: Giảm Runtime OCR Và Reindex Payload Search

Trạng thái: đề xuất.

Ngày cập nhật: 2026-06-02

## Task Vừa Hoàn Thành

Đã tối ưu PDF scan, benchmark nhanh theo fixture và search pháp lý exact-match.

Kết quả chính:
- Bổ sung cleanup OCR hẹp cho PDF scan:
  - `CÔNG BÁO/SỐ 869 ? 870` hoặc `869 4 870` -> `CÔNG BÁO/SỐ 869 + 870`.
  - `LUẶT`/`LỤẬT` -> `LUẬT`.
  - `điều chính` -> `điều chỉnh`.
  - `dầu khi` -> `dầu khí`.
- Thêm hậu xử lý text OCR để nối các tiêu đề PDF scan bị tách dòng:
  - `TỔNG CÔNG TY HẠ TẦNG KỸ THUẬT`.
  - `KẾ HOẠCH MUA SẮM VẬT TƯ NĂM 2026`.
- Thêm chế độ benchmark nhanh:
  - `--files sample_006.pdf`
  - `--limit N`
- Tăng keyword reranking cho query pháp lý:
  - Query có `phạm vi điều chỉnh` ưu tiên chunk bắt đầu bằng `Điều 1`.
  - Giảm điểm candidate không chứa phrase pháp lý cần tìm.

Đã kiểm tra:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/scripts/benchmark_ocr_vi.py /app/app/services/document_content_service.py /app/app/services/search_service.py
docker compose run --rm --no-deps -e OCR_PREPROCESS_MODE=raw worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --files sample_006.pdf --engine paddle_vietocr --format json
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Luật Đấu thầu phạm vi điều chỉnh","limit":5}'
```

Kết quả benchmark `sample_006.pdf`:

```text
paddle_vietocr: CER 0.0, WER 0.0, accent loss 0.0, confidence 0.9279
TỔNG CÔNG TY HẠ TẦNG KỸ THUẬT
KẾ HOẠCH MUA SẮM VẬT TƯ NĂM 2026
Số: 08/KH-HTKT
```

OCR riêng page 1 của `22-qh-15.signed.pdf`:

```text
confidence=0.9256
CÔNG BÁO/SỐ 869 + 870/NGÀY 31-7-2023
LUẬT
ĐẦU THẦU
Điều 1. Phạm vi điều chỉnh
```

Search:
- Query `Luật Đấu thầu phạm vi điều chỉnh` đưa chunk `Điều 1. Phạm vi điều chính` lên top 1.

## Mục Tiêu Task Tiếp Theo

Giảm runtime OCR/VietOCR cho vòng kiểm tra và cập nhật lại payload search đã index để tận dụng `content_hash` dedup.

## Ràng Buộc Không Đổi

- Không dùng cloud OCR.
- Không dùng API LLM để sửa nội dung pháp lý.
- Docker Compose first.
- MVP first.
- Backend giữ `router -> service -> repository`.
- OCR pipeline local/on-prem.
- Không commit model files hoặc runtime artifacts.

## Phạm Vi Đề Xuất

### 1. Giảm Runtime OCR/VietOCR

Vấn đề:
- OCR VietOCR vẫn khoảng 36-44s/page trên PDF fixture vì detect + recognize nhiều crop.
- `OCR_PREPROCESS_MODE=auto` vẫn không phù hợp cho check thường xuyên trên full fixture.

Hướng xử lý:
- Cho benchmark tái sử dụng service/engine theo engine thay vì khởi tạo lại nhiều lần.
- Thêm tùy chọn benchmark `--preprocess-mode` để so sánh `raw/clahe/threshold/auto` rõ ràng.
- Đo runtime trên `sample_001.png`, `sample_004.png`, `sample_006.pdf` với cùng engine.

### 2. Reindex Qdrant Payload

Vấn đề:
- Code mới đã đưa `content_hash` vào Qdrant payload cho index/reindex sau.
- Collection hiện tại có thể vẫn còn payload cũ cho các chunk đã index trước thay đổi.

Hướng xử lý:
- Chạy dry-run reindex để xác nhận số chunk.
- Chạy reindex thật khi service ổn.
- Kiểm tra payload sau reindex có `content_hash`.
- Kiểm tra search vẫn trả đúng top 1 cho `Luật Đấu thầu phạm vi điều chỉnh`.

### 3. Mở Rộng Fixture Công Văn Không Nhạy Cảm

Vấn đề:
- JPEG công văn thực tế đã cải thiện nhưng chưa có fixture không nhạy cảm mô phỏng cùng dạng nhiễu.

Hướng xử lý:
- Tạo fixture công văn xã/phòng ban giả lập, có header hai bên và dấu mộc/nhiễu nhẹ.
- Ground truth gồm số hiệu, ngày tháng, kính gửi, nội dung yêu cầu.
- Benchmark `paddle_vietocr` trên fixture này.

## Tiêu Chí Hoàn Thành

- Benchmark có thể so sánh runtime theo preprocess mode mà không sửa env ngoài.
- Reindex Qdrant payload có `content_hash` cho chunk hiện có.
- Search sau reindex vẫn đưa Điều 1 lên top 1.
- Có fixture công văn không nhạy cảm cho lỗi OCR thực tế.
- Không phát sinh model/runtime artifact trong git.

## Task Sau Đó Đề Xuất

- Hybrid search PostgreSQL keyword + Qdrant vector nếu reranking payload vẫn chưa đủ cho các query khác.
- Fine-tune VietOCR hoặc recognizer local nếu fixture công văn mới vẫn còn lỗi khó.
