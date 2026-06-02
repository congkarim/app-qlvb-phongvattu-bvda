# Task Tiếp Theo: Kiểm Tra OCR Với File Thực Tế Và Tối Ưu Layout Khó

Trạng thái: đề xuất.

Ngày cập nhật: 2026-06-02

## Task Vừa Hoàn Thành

Đã mở rộng fixture OCR tiếng Việt và chạy benchmark trên nhiều mẫu không nhạy cảm.

Kết quả chính:
- Thêm generator deterministic: `tests/fixtures/ocr_vi/generate_fixtures.py`.
- Mở rộng fixture từ 1 mẫu lên 6 mẫu:
  - scan rõ;
  - quyết định hành chính nhiều dấu;
  - scan nén/mờ;
  - trang hai cột và ghi chú;
  - ảnh nghiêng nhẹ có nhiễu;
  - PDF scan 2 trang.
- Mỗi fixture có ground truth `.txt` cùng tên.
- Cập nhật `benchmark_ocr_vi.py` để benchmark cả `.pdf`, gom text nhiều page và báo `seconds_per_page`.
- Cập nhật `tests/fixtures/ocr_vi/README.md` với mô tả fixture và kết quả benchmark.

Benchmark ngày 2026-06-02:

```bash
docker compose run --rm --no-deps -e OCR_PREPROCESS_MODE=raw worker \
  python -m app.scripts.benchmark_ocr_vi \
  --fixtures /app/tests/fixtures/ocr_vi \
  --engine all \
  --format json
```

Tóm tắt kết quả:

| file | paddleocr CER/WER/accent loss | paddle_vietocr CER/WER/accent loss | Nhận xét |
| --- | ---: | ---: | --- |
| `sample_001.png` | 0.0053 / 0.0238 / 0.0294 | 0.0 / 0.0 / 0.0 | VietOCR đạt tuyệt đối trên mẫu rõ. |
| `sample_002.png` | 0.1066 / 0.4722 / 0.4923 | 0.0063 / 0.0417 / 0.0 | VietOCR giữ dấu tốt, còn lỗi dấu câu nhỏ. |
| `sample_003.png` | 0.1443 / 0.5397 / 0.5424 | 0.0687 / 0.1111 / 0.0 | Scan mờ có cải thiện lớn nhưng còn hallucination vài từ. |
| `sample_004.png` | 0.6905 / 0.9783 / 0.4659 | 0.711 / 0.913 / 0.0 | Bố cục hai cột sai thứ tự đọc; đây là lỗi layout/detection, không phải mất dấu. |
| `sample_005.png` | 0.098 / 0.4154 / 0.4808 | 0.0034 / 0.0154 / 0.0 | VietOCR xử lý tốt ảnh nghiêng nhẹ. |
| `sample_006.pdf` | 0.1417 / 0.5487 / 0.5714 | 0.0526 / 0.0531 / 0.0 | PDF scan giữ dấu tốt hơn, còn tách dòng tiêu đề; runtime VietOCR khoảng 39.6s/page. |

Đã kiểm tra:

```bash
docker compose config --quiet
docker compose run --rm --no-deps worker python -m py_compile /app/app/scripts/benchmark_ocr_vi.py
docker compose run --rm --no-deps -e OCR_PREPROCESS_MODE=raw worker python -m py_compile /app/app/scripts/benchmark_ocr_vi.py /app/tests/fixtures/ocr_vi/generate_fixtures.py
docker compose run --rm --no-deps -e OCR_PREPROCESS_MODE=raw worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --engine all --format json
```

Ghi chú:
- Lệnh benchmark full với `OCR_PREPROCESS_MODE=auto` bị dừng sau hơn 5 phút vì quá chậm cho kiểm tra thường xuyên.
- Chưa kiểm tra được tài liệu thực tế người dùng upload lại vì repo chưa có file thực tế mới.

## Mục Tiêu Task Tiếp Theo

Upload lại tài liệu thực tế của người dùng và kiểm tra OCR end-to-end trên workflow thật:

```text
upload -> preprocess -> OCR -> chunk -> embedding -> qdrant -> search
```

## Ràng Buộc Không Đổi

- Không dùng cloud OCR.
- Không dùng API LLM để sửa nội dung pháp lý.
- Docker Compose first.
- MVP first.
- Backend giữ `router -> service -> repository`.
- OCR pipeline local/on-prem.
- Không commit model files hoặc runtime artifacts.

## Phạm Vi Đề Xuất

### 1. Kiểm Tra Tài Liệu Thực Tế

Sau khi người dùng cung cấp/upload lại file thực tế:
- Theo dõi worker log.
- Kiểm tra OCR page text.
- Kiểm tra chunk/search.
- Ghi lại file/page nào vẫn lỗi dấu, sai số hiệu, sai ngày tháng hoặc sai điều/khoản.

### 2. Tối Ưu Layout Khó

Ưu tiên xử lý các lỗi đã thấy trong benchmark:
- `sample_004.png`: trang hai cột bị sai thứ tự đọc.
- `sample_006.pdf`: tiêu đề PDF bị tách dòng không tự nhiên.
- `OCR_PREPROCESS_MODE=auto`: runtime quá cao trên full fixture.

Hướng xử lý:
- Cải thiện crop ordering theo cột trước khi sort theo dòng.
- Thêm heuristic nối dòng tiêu đề bị tách khi các box cùng hàng.
- Giảm số preprocess candidate khi scan rõ hoặc cho phép benchmark chạy theo mode cụ thể.
- Cache/reuse detector và predictor trong benchmark/service path nếu còn init lặp.

## Tiêu Chí Hoàn Thành

- Có kết quả OCR trên ít nhất một tài liệu thực tế người dùng upload lại.
- Có danh sách lỗi cụ thể theo file/page nếu OCR chưa đạt.
- Với layout hai cột, thứ tự đọc không còn trộn cột trái/phải trên fixture hiện có.
- Runtime benchmark có cấu hình kiểm tra nhanh ổn định cho toàn bộ fixture.
- Không phát sinh model/runtime artifact trong git.

## Task Sau Đó Đề Xuất

Khi OCR thực tế đủ ổn:
- Dedup/reranking semantic search để giảm kết quả trùng.
- Hybrid search keyword + vector cho truy vấn pháp lý.

Nếu OCR thực tế vẫn chưa đạt:
- Fine-tune VietOCR hoặc PaddleOCR recognizer trên dataset pháp lý tiếng Việt local.
